"""Opt-in browser acceptance against isolated APIs and the actual Gemini endpoint.

No provider substitution, production database, mail delivery, or notification worker.
See docs/local-ai-testing.md. Ordinary discovery never reads a credential file.
"""

import json
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect

import test_backlog_real_api as backlog_real


# Installed only into this fixture's subprocesses. Observe the real HTTP transport;
# do not replace its response. Persist metadata only, never request bodies/headers.
AUDIT_TRANSPORT = r'''
import json
import os
from pathlib import Path
import httpx

original = httpx.HTTPTransport.handle_request
def audited(self, request):
    if request.url.host in ("127.0.0.1", "localhost", "::1"):
        return original(self, request)
    assert request.url.host == "generativelanguage.googleapis.com"
    assert request.url.scheme == "https"
    body = json.loads(request.read())
    prompt = json.loads(body["contents"][0]["parts"][0]["text"])
    context = prompt["context"]
    text = json.dumps(body)
    row = {"kind": prompt["kind"], "host": request.url.host,
        "no_bearer_or_cookie": not any(k in request.headers for k in ("authorization", "cookie")),
        "key_in_body": os.environ["GEMINI_API_KEY"] in text,
        "private_profile_in_body": "PRIVATE_PROFILE_CANARY" in text,
        "candidate_ids": [p["id"] for p in context.get("candidates", [])],
        "evidence": context.get("evidence", []),
        "project_id": context.get("project", {}).get("id"),
        "inactive_user_ids": context.get("access_usage", {}).get("inactive_user_ids", []),
        "audit_ids": [str(e["id"]) for e in context.get("audit_events", [])],
        "user_ids": [str(u["id"]) for u in context.get("users", [])]}
    response = original(self, request)
    row["http_status"] = response.status_code
    with Path(os.environ["GEMINI_ACCEPTANCE_AUDIT"]).open("a", encoding="utf-8") as out:
        out.write(json.dumps(row) + "\n")
    return response
httpx.HTTPTransport.handle_request = audited
'''


@unittest.skipUnless(os.environ.get('RUN_REAL_GEMINI_ACCEPTANCE') == '1',
                     'Explicit RUN_REAL_GEMINI_ACCEPTANCE=1 required (external Gemini calls)')
class GeminiRealApiTests(backlog_real.BacklogRealApiTests):
    test_registration_project_stories_progress_restart_and_access_isolation = None

    def setUp(self):
        key = os.environ.get('GEMINI_API_KEY')
        if not key:
            # dotenv is available in the backend venv, but not required by the UI.
            # Read only this explicitly selected file, and only after opt-in.
            env_file = os.environ.get('GEMINI_ACCEPTANCE_ENV_FILE')
            self.assertTrue(env_file, 'Supply Gemini key in environment or an explicit private env file')
            for line in Path(env_file).read_text(encoding='utf-8-sig').splitlines():
                if line.strip().startswith('GEMINI_API_KEY='):
                    key = line.split('=', 1)[1].strip().strip('\"\'')
        self.assertTrue(key, 'Gemini credential missing')
        self.real_ai_settings = dict(AI_PROVIDER='gemini', AI_SIMULATED='false',
            AI_BASE_URL='http://127.0.0.1:9/unused', GEMINI_API_KEY=key,
            GEMINI_MODEL=os.environ.get('GEMINI_ACCEPTANCE_MODEL', 'gemini-3.5-flash-lite'),
            GEMINI_API_BASE_URL='https://generativelanguage.googleapis.com/v1beta',
            GEMINI_TIMEOUT_SECONDS='30', GEMINI_MAX_OUTPUT_TOKENS='4096',
            MODULE6_ENABLED='false', MAIL_PROVIDER='disabled', LOCAL_MAILBOX_ENABLED='false')
        super().setUp()
        self.page.set_default_timeout(10000)
        # Promote only the account in our temporary Identity database.
        self.admin(self.auth_python, self.auth_root, self.auth_env, '''
from mod1_auth.config import Settings
from mod1_auth.database import create_engine_for_url, create_session_factory
from mod1_auth.repositories import UserRepository
s=Settings(_env_file=None)
engine=create_engine_for_url(s.database_url.get_secret_value())
with create_session_factory(engine)() as session:
    users=UserRepository(session)
    user=users.get_by_email('conta@example.com')
    with users.identity.atomic():
        account=users.identity.account(user.id)
        account['is_admin']=True
        users.identity.save_account(user.id, account)
engine.dispose()
''')
        self.owner = self.headers('conta@example.com', '  password12345  ')
        self.register('candidate@example.com')
        self.candidate = self.headers('candidate@example.com')
        self.candidate_id = self.get(self.auth_url+'/auth/me', self.candidate)['id']
        self.register('candidate-two@example.com')
        self.candidate_two = self.headers('candidate-two@example.com')
        self.candidate_two_id = self.get(self.auth_url+'/auth/me', self.candidate_two)['id']
        self.register('private@example.com')
        self.private = self.headers('private@example.com')
        self.private_id = self.get(self.auth_url+'/auth/me', self.private)['id']
        for headers, shared, summary in [(self.candidate, True, 'Python backend sintético'),
                                         (self.candidate_two, True, 'PostgreSQL e testes sintéticos'),
                                         (self.private, False, 'PRIVATE_PROFILE_CANARY')]:
            self.call('patch', self.auth_url+'/auth/profile', headers, {
                'summary': summary, 'seniority': 'mid', 'weekly_availability_hours': 20,
                'skills': [{'name': 'PostgreSQL' if headers is self.candidate_two else 'Python', 'level': 4}],
                'share_for_recommendations': shared}, 200)
        self.project = self.call('post', self.projects_url+'/projects', self.owner, {
            'name': 'Portal sintético de aceitação Gemini',
            'description': 'Portal para abrir solicitações e consultar seu andamento.',
            'scope': 'Criar solicitação e listar apenas solicitações próprias.',
            'technology_stack': ['Python'], 'technical_requirements': ['PostgreSQL'],
            'soft_skills': ['Comunicação']}, 201)
        self.pid = self.project['id']
        self.pbase = self.projects_url+'/projects/'+self.pid
        self.bbase = self.backlog_url+'/projects/'+self.pid
        self.call('post', self.pbase+'/members', self.owner,
                  {'user_id': self.candidate_id, 'roles': ['developer']}, 201)
        self.call('post', self.bbase+'/items', self.owner, {
            'kind': 'task', 'title': 'Implementar consulta Python com persistência PostgreSQL',
            'description': 'Implementar endpoint e testes de integração para consulta das solicitações.',
            'assignee_id': self.candidate_id}, 201)
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def configured_env(self, env):
        configured = dict(env, **self.real_ai_settings)
        audit_dir = Path(self.temp.name)/'audit_hook'
        audit_dir.mkdir(exist_ok=True)
        (audit_dir/'sitecustomize.py').write_text(AUDIT_TRANSPORT, encoding='utf-8')
        configured['PYTHONPATH'] = str(audit_dir)+os.pathsep+env.get('PYTHONPATH', '')
        configured['GEMINI_ACCEPTANCE_AUDIT'] = str(Path(self.temp.name)/'gemini-audit.jsonl')
        return configured

    def admin(self, python, cwd, env, script):
        return super().admin(python, cwd, self.configured_env(env), script)

    def start(self, python, cwd, env, factory, port):
        return super().start(python, cwd, self.configured_env(env), factory, port)

    def headers(self, email, password='ProjetoMvp!2026'):
        response = self.context.request.post(self.auth_url+'/auth/token', form={
            'username': email, 'password': password})
        self.assertEqual(response.status, 200, 'Synthetic login failed')
        return {'Authorization': 'Bearer '+response.json()['access_token']}

    def call(self, method, url, headers, data=None, status=200):
        response = getattr(self.context.request, method)(url, headers=headers, data=data)
        self.assertEqual(response.status, status, f'{method.upper()} local API: unexpected status')
        return response.json() if status != 204 else None

    def get(self, url, headers=None):
        return self.call('get', url, headers or self.owner)

    def audit(self):
        path = Path(self.temp.name)/'gemini-audit.jsonl'
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []

    def open_project(self, initial_backlog=False):
        if not self.page.locator('#projects-view').is_visible():
            self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name=self.project['name'], exact=True).click()
        self.page.get_by_role('button', name='Gerenciar projeto e planejamento', exact=True).click()
        if initial_backlog:
            self.page.get_by_role('button', name='Quadro e itens', exact=True).click()
            self.page.get_by_role('button', name='Sugerir backlog inicial', exact=True).click()
        else:
            self.page.get_by_role('button', name='Recomendações', exact=True).click()

    def generate_in_browser(self, base, kind):
        self.page.get_by_label('Tipo de recomendação', exact=True).select_option(kind)
        with self.page.expect_response(lambda r: r.url == base and r.request.method == 'POST', timeout=45000) as result:
            self.page.get_by_role('button', name='Solicitar recomendação', exact=True).click()
        self.assertEqual(result.value.status, 201, kind+' did not persist a real proposal')
        rec = result.value.json()
        self.assertEqual((rec['kind'], rec['status'], rec['version']), (kind, 'pending', 1))
        self.assertEqual(rec['provider'], 'gemini')
        self.assertEqual(rec['model'], self.real_ai_settings['GEMINI_MODEL'])
        self.assertIs(rec['simulated'], False)
        self.assertTrue(rec['summary'] and rec['justification'])
        self.assertIsInstance(rec['suggestions'], list)
        expect(self.page.locator('#workspace-content')).to_contain_text('Google Gemini')
        expect(self.page.locator('#workspace-status')).to_contain_text('Nenhuma alteração foi aplicada')
        self.assertEqual(self.get(base+'/'+rec['id']), rec)
        return rec

    def seed_inactivity(self):
        # Only this fixture's SQLite database. No fabricated production history.
        script = '''
from datetime import UTC, datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from projects_service.config import Settings
from projects_service.database import create_database_engine
from projects_service.collaboration_repository import CollaborationRepository
from projects_service.models import AccessObservationRecord
engine=create_database_engine(Settings(_env_file=None))
with Session(engine) as session:
    repo=CollaborationRepository(session)
    pid, uid=UUID(PROJECT_PLACEHOLDER), UUID(USER_PLACEHOLDER)
    project=repo.project(pid)
    row=AccessObservationRecord(project_id=pid,user_id=uid,
        observed_since=datetime.now(UTC)-timedelta(days=60),last_activity_at=None,
        access_signature=repo.access_signature(project,uid))
    session.merge(row)
    session.commit()
engine.dispose()
'''.replace('PROJECT_PLACEHOLDER', repr(self.pid)).replace('USER_PLACEHOLDER', repr(self.candidate_id))
        self.admin(self.projects_python, self.projects_root, self.projects_env, script)

    def snapshot(self):
        return {'members': self.get(self.pbase+'/members'),
            'teams': self.get(self.pbase+'/teams'),
            'items': self.get(self.bbase+'/items'),
            'project': self.get(self.pbase)}

    def reject_in_browser(self, base, rec):
        # Cards are sections headed by model prose; use the ID-specific request
        # expectation and the last pending card, independent of generated wording.
        label = 'Rejeitar recomendação' if rec['suggestions'] else 'Dispensar análise'
        with self.page.expect_response(base+'/'+rec['id']+'/reject') as result:
            self.page.get_by_role('button', name=label, exact=True).last.click()
        self.assertEqual(result.value.status, 200)
        rejected = result.value.json()
        self.assertEqual((rejected['status'], rejected['version']), ('rejected', 2))
        self.assertEqual(self.get(base+'/'+rec['id']), rejected)
        return rejected

    def approve_in_browser(self, base, rec):
        with self.page.expect_response(base+'/'+rec['id']+'/approve') as result:
            self.page.get_by_role('button', name='Aprovar recomendação', exact=True).last.click()
        self.assertEqual(result.value.status, 200)
        approved = result.value.json()
        self.assertEqual((approved['status'], approved['version']), ('approved', 2))
        self.assertEqual(self.get(base+'/'+rec['id']), approved)
        return approved

    def assert_project_approval_effects(self, rec):
        events = self.get(self.pbase+'/history?action=recommendation.approved')['items']
        self.assertEqual(len([e for e in events if e['changes'].get('recommendation_id') == rec['id']]), 1)
        if rec['kind'] == 'roles':
            members = {m['user_id']: m for m in self.get(self.pbase+'/members')['items']}
            for suggestion in rec['suggestions']:
                member = members[suggestion['user_id']]
                self.assertTrue(set(suggestion['roles']).issubset(member['roles']))
                self.assertTrue(set(suggestion['roles']).issubset({g['role'] for g in member['role_grants']}))
        else:
            links = self.get(self.pbase+'/teams')['items']
            owned = self.get(self.projects_url+'/teams')['items']
            for suggestion in rec['suggestions']:
                team_id = suggestion.get('team_id')
                if not team_id:
                    matches = [t for t in owned if t['name'] == suggestion['name']]
                    self.assertEqual(len(matches), 1)
                    team_id = matches[0]['id']
                link = next(link for link in links if link['team_id'] == team_id)
                self.assertTrue(set(suggestion['roles']).issubset(link['roles']))
            headers_by_id = {self.candidate_id: self.candidate, self.candidate_two_id: self.candidate_two}
            recipients = {uid for s in rec['suggestions'] for uid in s.get('user_ids', [])}
            for uid in recipients:
                inbox = self.get(self.projects_url+'/notifications', headers_by_id[uid])['items']
                self.assertEqual(len([n for n in inbox if n['project_id'] == self.pid and n['kind'] == 'team_recommendation_approved']), 1)
            private_inbox = self.get(self.projects_url+'/notifications', self.private)['items']
            self.assertFalse(any(n['project_id'] == self.pid for n in private_inbox))
        # Verify persisted internal outbox and EventRecord. External M6 delivery
        # remains explicitly disabled: no notification worker is launched.
        script = '''
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from projects_service.config import Settings
from projects_service.database import create_database_engine
from projects_service.models import OutboxRecord, NotificationDeliveryRecord
settings=Settings(_env_file=None)
assert settings.module6_enabled is False
engine=create_database_engine(settings)
with Session(engine) as session:
    rows=list(session.scalars(select(OutboxRecord).where(OutboxRecord.recommendation_id==UUID(REC_PLACEHOLDER))))
    assert len(rows)==1
    assert rows[0].payload['kind']==KIND_PLACEHOLDER
    assert rows[0].status==STATUS_PLACEHOLDER
    assert session.scalar(select(func.count()).select_from(NotificationDeliveryRecord))==0
engine.dispose()
'''.replace('REC_PLACEHOLDER', repr(rec['id'])).replace('KIND_PLACEHOLDER', repr(rec['kind'])).replace(
            'STATUS_PLACEHOLDER', repr('delivered_in_app' if rec['kind'] == 'teams' else 'pending'))
        self.admin(self.projects_python, self.projects_root, self.projects_env, script)

    def test_seven_real_kinds_persist_require_decision_and_enforce_context(self):
        before = self.snapshot()
        pbase = self.pbase+'/recommendations'
        # Unknown history must not become assumed inactivity or a provider call.
        self.call('post', pbase, self.owner,
                  {'kind': 'access_revocation', 'constraints': {'unused_days': 30}}, 409)
        self.assertEqual(self.audit(), [])
        self.seed_inactivity()
        self.open_project()
        records = []
        stale_context_verified = False
        for kind in ('roles', 'teams', 'skills_map', 'training', 'access_revocation'):
            with self.subTest(kind=kind):
                if kind == 'access_revocation':
                    self.seed_inactivity()
                rec = self.generate_in_browser(pbase, kind)
                self.assertEqual(self.snapshot(), before, 'Generation must not change business data')
                audited = self.audit()[-1]
                self.assertEqual(audited['kind'], kind)
                self.assertEqual(audited['project_id'], self.pid)
                self.assertNotIn(self.private_id, audited['candidate_ids'])
                self.assertIn(self.candidate_id, audited['candidate_ids'])
                self.assertTrue(set(rec['evidence']).issubset(audited['evidence']))
                if kind == 'access_revocation':
                    self.assertEqual(audited['inactive_user_ids'], [self.candidate_id])
                    self.assertTrue(all(s['user_id'] == self.candidate_id for s in rec['suggestions']))
                # Unauthorized account and another project cannot read a proposal.
                self.call('get', pbase+'/'+rec['id'], self.private, status=404)
                self.call('get', self.projects_url+'/projects/'+str(uuid4())+'/recommendations/'+rec['id'], self.owner, status=404)
                if kind in ('roles', 'teams') and rec['suggestions']:
                    approved = self.approve_in_browser(pbase, rec)
                    self.assert_project_approval_effects(approved)
                    self.assertEqual(self.call('post', pbase+'/'+rec['id']+'/approve', self.owner,
                                              {'expected_version': 1}), approved)
                    self.assert_project_approval_effects(approved)
                    records.append((pbase, approved))
                    before = self.snapshot()
                elif kind == 'access_revocation' and rec['suggestions']:
                    # A changed observation invalidates the captured context even
                    # while the same user remains eligible. No access is removed.
                    self.seed_inactivity()
                    with self.page.expect_response(pbase+'/'+rec['id']+'/approve') as stale:
                        self.page.get_by_role('button', name='Aprovar recomendação', exact=True).last.click()
                    self.assertEqual(stale.value.status, 409)
                    expired = self.get(pbase+'/'+rec['id'])
                    self.assertEqual((expired['status'], expired['version']), ('expired', 2))
                    records.append((pbase, expired))
                    stale_context_verified = True
                else:
                    records.append((pbase, self.reject_in_browser(pbase, rec)))
        self.assertEqual(self.snapshot(), before, 'Rejection must not apply proposals')
        self.page.get_by_role('button', name='Voltar para projetos', exact=True).click()
        self.open_project(initial_backlog=True)
        bbase = self.bbase+'/recommendations'
        rec = self.generate_in_browser(bbase, 'initial_backlog')
        self.assertEqual(self.snapshot(), before)
        self.call('get', bbase+'/'+rec['id'], self.private, status=404)
        records.append((bbase, rec))
        # Explicit approval exercises an actual business mutation only when there
        # are applicable suggestions. Empty output must remain non-applicable.
        if rec['suggestions']:
            with self.page.expect_response(bbase+'/'+rec['id']+'/approve') as approved:
                self.page.get_by_role('button', name='Aprovar recomendação', exact=True).click()
            self.assertEqual(approved.value.status, 200)
            rec = approved.value.json()
            self.assertEqual(rec['status'], 'approved')
            self.assertEqual(len(rec['applied_item_ids']), len(rec['suggestions']))
            self.assertEqual(self.get(self.bbase+'/items')['total'], before['items']['total']+len(rec['suggestions']))
            repeat = self.call('post', bbase+'/'+rec['id']+'/approve', self.owner, {'expected_version': 1})
            self.assertEqual(repeat, rec)
            self.assertEqual(self.get(self.bbase+'/items')['total'], before['items']['total']+len(rec['suggestions']))
            records[-1] = (bbase, rec)
        else:
            self.call('post', bbase+'/'+rec['id']+'/approve', self.owner, {'expected_version': 1}, 409)
            records[-1] = (bbase, self.reject_in_browser(bbase, rec))
        self.page.get_by_role('button', name='Voltar para projetos', exact=True).click()
        self.page.locator('#projects-back').click()
        self.page.get_by_role('button', name='Administração', exact=True).click()
        self.page.get_by_role('button', name='Análise de acessos', exact=True).click()
        abase = self.auth_url+'/admin/recommendations'
        self.call('post', abase, self.private, {'kind': 'access_anomalies'}, 403)
        accounts_before = self.get(self.auth_url+'/admin/users')
        rec = self.generate_in_browser(abase, 'access_anomalies')
        self.assertEqual(self.get(self.auth_url+'/admin/users'), accounts_before)
        identity_audit = self.audit()[-1]
        self.assertTrue(set(rec['evidence']).issubset(identity_audit['audit_ids']))
        for suggestion in rec['suggestions']:
            self.assertIn(suggestion['user_id'], identity_audit['user_ids'])
            self.assertTrue(set(suggestion['evidence_ids']).issubset(identity_audit['audit_ids']))
        records.append((abase, self.reject_in_browser(abase, rec)))
        for python, root, env, factory, port, attribute in [
            (self.auth_python, self.auth_root, self.auth_env, 'mod1_auth.main:create_app', self.auth_port, 'auth_process'),
            (self.projects_python, self.projects_root, self.projects_env, 'projects_service.app:create_app', self.projects_port, 'projects_process'),
            (self.backlog_python, self.backlog_root, self.backlog_env, 'backlog_service.app:create_app', self.backlog_port, 'backlog_process')]:
            self.stop(getattr(self, attribute))
            setattr(self, attribute, self.start(python, root, env, factory, port))
        for base, stored in records:
            self.assertEqual(self.get(base+'/'+stored['id']), stored, 'Proposal/decision lost across service restart')
            self.assertIn(stored['id'], [r['id'] for r in self.get(base)['items']])
        audit = self.audit()
        self.assertEqual(len(audit), 7, 'Exactly seven real provider requests expected')
        self.assertEqual({r['kind'] for r in audit}, {'access_anomalies', 'roles', 'teams', 'skills_map', 'training', 'access_revocation', 'initial_backlog'})
        for row in audit:
            self.assertEqual(row['http_status'], 200)
            self.assertTrue(row['no_bearer_or_cookie'])
            self.assertFalse(row['key_in_body'])
            self.assertFalse(row['private_profile_in_body'])
        for base in (pbase, bbase, abase):
            self.assertEqual(self.context.request.get(base).status, 401)
        report = {'verified_at_utc': datetime.now(timezone.utc).isoformat(),
            'model': self.real_ai_settings['GEMINI_MODEL'],
            'target': 'temporary SQLite APIs + headless Edge + official Gemini HTTPS',
            'real_provider_requests': len(audit), 'persistence_after_restart': True,
            'unauthorized_reads_blocked': True, 'stale_context_verified': stale_context_verified,
            'private_profile_excluded': True, 'credentials_excluded_from_body': True,
            'records': [{'kind': rec['kind'], 'suggestion_count': len(rec['suggestions']),
                         'decision': rec['status']} for _, rec in records]}
        report_dir = Path(__file__).resolve().parents[1]/'.local'/'gemini-acceptance'
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
