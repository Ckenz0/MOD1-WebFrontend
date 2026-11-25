"""Browser acceptance with three disposable APIs and a loopback Code Review owner.

No real provider credentials, production data, GitHub comments or notifications.
"""

import base64
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import expect

import test_backlog_real_api as real


class ProviderHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        self.server.calls.append({'path': self.path, 'body': body,
            'basic_ok': self.headers.get('Authorization') == 'Basic ' + base64.b64encode(b'local-user:local-password').decode(),
            'no_cookie': self.headers.get('Cookie') is None})
        if self.server.mode == 'uncertain':
            self.send_response(503); self.end_headers(); return
        response = {'id':'33333333-3333-4333-8333-333333333333', 'criado_em':'2026-11-16T12:00:00Z',
            'arquitetura':body['arquitetura'], 'arquivos':len(body.get('arquivos', [])) or 1,
            'achados':[{'arquivo':'demo.py', 'linha':1, 'categoria':'estilo', 'gravidade':'baixa',
                'titulo':'<b>Achado controlado</b>', 'sugestao':'Revisar clareza do nome'}],
            'testes':[], 'testes_executados':False, 'pr':None,
            'ia':{'status':'disabled', 'texto':''}, 'markdown':'# Relatório controlado <img src=x>'}
        encoded = json.dumps(response).encode()
        self.send_response(201); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(encoded))); self.end_headers(); self.wfile.write(encoded)


@unittest.skipUnless(all(os.environ.get(k) for k in ('AUTH_BACKEND_PATH', 'PROJECTS_BACKEND_PATH', 'BACKLOG_BACKEND_PATH')),
                     'Set all three backend paths for isolated Module4 browser acceptance')
class Module4RealApiTests(real.BacklogRealApiTests):
    test_registration_project_stories_progress_restart_and_access_isolation = None

    def additional_auth_settings(self):
        return {'MAIL_PROVIDER':'disabled', 'LOCAL_MAILBOX_ENABLED':'false',
                'MODULE6_ENABLED':'false', 'AI_PROVIDER':'structured-http', 'AI_BASE_URL':'http://127.0.0.1:9'}

    def additional_projects_settings(self):
        return {'MODULE6_ENABLED':'false', 'AI_PROVIDER':'structured-http', 'AI_BASE_URL':'http://127.0.0.1:9'}

    def additional_backlog_settings(self):
        self.provider = ThreadingHTTPServer(('127.0.0.1', 0), ProviderHandler)
        self.provider.calls = []; self.provider.mode = 'succeeded'
        self.provider_thread = threading.Thread(target=self.provider.serve_forever, daemon=True)
        self.provider_thread.start()
        self.addCleanup(self.stop_provider)
        return {'MODULE4_ENABLED':'true', 'MODULE4_BASE_URL':f'http://127.0.0.1:{self.provider.server_port}',
                'MODULE4_USERNAME':'local-user', 'MODULE4_PASSWORD':'local-password', 'MODULE6_ENABLED':'false',
                'AI_PROVIDER':'structured-http', 'AI_BASE_URL':'http://127.0.0.1:9'}

    def stop_provider(self):
        self.provider.shutdown(); self.provider.server_close(); self.provider_thread.join()

    def setUp(self):
        super().setUp()
        self.page.set_default_timeout(10000)
        self.register('module4@example.com')
        token = self.context.request.post(self.auth_url + '/auth/token', form={
            'username':'module4@example.com', 'password':'ProjetoMvp!2026'}).json()['access_token']
        self.headers = {'Authorization':'Bearer ' + token}
        project = self.context.request.post(self.projects_url + '/projects', headers=self.headers,
            data={'name':'Revisão local de código'}).json()
        self.project_id = project['id']
        self.item_base = self.backlog_url + '/projects/' + self.project_id + '/items'
        result = self.context.request.post(self.item_base, headers=self.headers,
            data={'kind':'task','title':'Revisar função Python'})
        self.assertEqual(result.status, 201)
        self.item = result.json()
        self.review_base = self.item_base + '/' + self.item['id'] + '/code-reviews'
        self.page.goto(self.base_url); self.sign_in('module4@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Revisão local de código', exact=True).click()
        self.page.get_by_role('button', name='Planejamento', exact=True).click()
        self.page.get_by_role('button', name='Quadro e itens', exact=True).click()
        self.page.get_by_role('table', name='Itens do projeto').get_by_role('button', name='Revisar função Python', exact=True).click()
        self.page.get_by_role('button', name='Revisões de código', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_be_enabled()

    def submit_synthetic_file(self):
        self.page.get_by_label('Arquivos Python', exact=True).set_input_files({
            'name':'demo.py', 'mimeType':'text/x-python', 'buffer':b'def answer():\n    return 42\n'})
        with self.page.expect_response(lambda response: response.url == self.review_base and response.request.method == 'POST') as response:
            self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        self.assertEqual(response.value.status, 201)
        return response.value.json(), response.value.request.post_data_json

    def test_review_transitions_todo_preserves_report_on_restart_and_does_not_auto_complete(self):
        row, payload = self.submit_synthetic_file()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        expect(self.page.get_by_text('<b>Achado controlado</b>', exact=True)).to_be_visible()
        expect(self.page.locator('#workspace-content img')).to_have_count(0)
        self.assertEqual(row['status'], 'succeeded')
        self.assertEqual(self.provider.calls[0]['path'], '/api/analisar')
        self.assertTrue(self.provider.calls[0]['basic_ok'])
        self.assertTrue(self.provider.calls[0]['no_cookie'])
        self.assertFalse(self.provider.calls[0]['body']['usar_ia'])
        self.assertNotIn('request_id', self.provider.calls[0]['body'])
        current = self.context.request.get(self.item_base + '/' + self.item['id'], headers=self.headers).json()
        self.assertEqual(current['status'], 'in_progress')
        replay = self.context.request.post(self.review_base, headers=self.headers, data=payload)
        self.assertEqual(replay.status, 201); self.assertEqual(replay.json()['id'], row['id'])
        self.assertEqual(len(self.provider.calls), 1)
        self.stop(self.backlog_process)
        self.backlog_process = self.start(self.backlog_python, self.backlog_root, self.backlog_env,
            'backlog_service.app:create_app', self.backlog_port)
        self.page.get_by_role('button', name='Atualizar revisões', exact=True).click()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        self.assertEqual(self.context.request.get(self.review_base, headers=self.headers).json()['total'], 1)
        self.page.get_by_role('button', name='Voltar ao item', exact=True).click()
        expect(self.page.get_by_label('Nova situação do item', exact=True)).to_have_value('in_progress')
        self.assertEqual(len(self.provider.calls), 1)
        capture = os.environ.get('CAPTURE_MODULE4_EVIDENCE')
        if capture:
            from pathlib import Path
            directory = Path(capture).resolve(); directory.mkdir(parents=True, exist_ok=True)
            self.page.get_by_role('button', name='Revisões de código', exact=True).click()
            expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
            for width, theme in [(1366, 'light'), (390, 'dark')]:
                self.page.set_viewport_size({'width':width,'height':900})
                self.page.evaluate('(theme)=>document.documentElement.dataset.theme=theme', theme)
                self.page.screenshot(path=str(directory / f'module4-{width}-{theme}.png'), full_page=True)
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_provider_unknown_outcome_preserves_item_and_requires_explicit_new_analysis(self):
        self.provider.mode = 'uncertain'
        row, _ = self.submit_synthetic_file()
        expect(self.page.get_by_role('heading', name='Resultado incerto', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        self.assertEqual(row['status'], 'uncertain')
        current = self.context.request.get(self.item_base + '/' + self.item['id'], headers=self.headers).json()
        self.assertEqual(current['status'], 'todo')
        self.page.get_by_role('button', name='Atualizar revisões', exact=True).click()
        expect(self.page.get_by_role('button', name='Nova análise mesmo com risco de duplicidade', exact=True)).to_be_visible()
        self.assertEqual(len(self.provider.calls), 1)
