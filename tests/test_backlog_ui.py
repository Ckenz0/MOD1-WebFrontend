import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from playwright.sync_api import expect

from browser_support import BrowserCase
from test_backlog_api import STORY
from test_projects_api import PROJECT


class BacklogUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.stories = []
        self.writes = []
        self.list_status = 200
        self.fail_after_write = False
        self.after_write_status = 503
        self.offsets = []
        self.mock_auth()
        self.page.route('**/projects?*', lambda r: r.fulfill(json={'items': [PROJECT], 'total': 1, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects/' + PROJECT['id'], lambda r: r.fulfill(json=PROJECT))
        self.page.route('**/projects/*/stories**', self.respond)
        self.page.goto(self.base_url)
        self.login()
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name=PROJECT['name'], exact=True).click()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        expect(self.page.locator('#backlog-view')).to_be_visible()
        expect(self.page.get_by_role('button', name='Criar história', exact=True)).to_be_enabled()

    def respond(self, route):
        request = route.request
        path = urlparse(request.url).path
        method = request.method
        if method in ('POST', 'PATCH'):
            data = request.post_data_json
            self.writes.append((method, data))
            if method == 'POST':
                story = {**STORY, **data, 'id': str(uuid4()), 'project_id': PROJECT['id']}
                self.stories.append(story)
            else:
                story = next(s for s in self.stories if s['id'] == path.rsplit('/', 1)[-1])
                story.update(data)
            route.fulfill(status=201 if method == 'POST' else 200, json=story)
            if self.fail_after_write:
                self.list_status = self.after_write_status
        elif path.endswith('/stories'):
            offset = int(parse_qs(urlparse(request.url).query).get('offset', ['0'])[0])
            self.offsets.append(offset)
            priorities = {'high': 0, 'medium': 1, 'low': 2}
            items = sorted(self.stories, key=lambda s: priorities[s['priority']])
            route.fulfill(status=self.list_status, json={'items': items[offset:offset+20], 'total': len(items), 'limit': 20, 'offset': offset})
        else:
            story = next((s for s in self.stories if s['id'] == path.rsplit('/', 1)[-1]), None)
            route.fulfill(status=200 if story else 404, json=story or {})

    def create(self, title='Entrega de teste'):
        self.page.get_by_label('Título da história', exact=True).fill(title)
        self.page.get_by_role('button', name='Criar história', exact=True).click()

    def capture_evidence(self, filename):
        if directory := os.environ.get('CAPTURE_BACKLOG_EVIDENCE'):
            target = Path(directory)
            target.mkdir(parents=True, exist_ok=True)
            self.page.evaluate('window.scrollTo(0, 0)')
            self.page.screenshot(path=str(target / filename), full_page=True)

    def test_empty_validation_and_unicode_boundaries(self):
        expect(self.page.locator('#backlog-list')).to_contain_text('Ainda não há histórias')
        self.create(' ')
        expect(self.page.get_by_label('Título da história', exact=True)).to_be_focused()
        self.assertEqual(self.writes, [])
        self.create('😀' * 121)
        expect(self.page.locator('#story-title-error')).to_be_visible()
        self.page.get_by_label('Título da história', exact=True).fill('😀' * 120)
        self.page.get_by_label('Critérios de aceite', exact=True).fill('x' * 2001)
        self.page.get_by_role('button', name='Criar história', exact=True).click()
        expect(self.page.locator('#story-criteria-error')).to_be_visible()
        self.page.get_by_label('Critérios de aceite', exact=True).fill('x' * 2000)
        self.page.get_by_label('Descrição da história', exact=True).fill('x' * 2001)
        self.page.get_by_role('button', name='Criar história', exact=True).click()
        expect(self.page.locator('#story-description-error')).to_be_visible()
        self.page.get_by_label('Descrição da história', exact=True).fill('x' * 2000)
        self.page.get_by_role('button', name='Criar história', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('História criada')
        self.assertEqual(len(self.writes), 1)

    def test_literal_multiline_and_progress(self):
        self.page.get_by_label('Descrição da história', exact=True).fill('<b>texto literal</b>\nsegunda linha')
        self.page.get_by_label('Critérios de aceite', exact=True).fill('Dado X\nQuando Y\nEntão Z')
        self.create('Uma história útil')
        expect(self.page.locator('#story-detail-description')).to_have_text('<b>texto literal</b>\nsegunda linha')
        self.assertEqual(self.page.locator('#story-detail-description b').count(), 0)
        expect(self.page.locator('#story-detail-criteria')).to_have_text('Dado X\nQuando Y\nEntão Z')
        self.page.get_by_label('Prioridade da história', exact=True).select_option('high')
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('Alterações salvas')
        expect(self.page.locator('#backlog-list')).to_contain_text('Concluído')
        expect(self.page.locator('#backlog-list')).to_contain_text('Alta')
        self.page.get_by_label('Status da história', exact=True).select_option('todo')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-list')).to_contain_text('A fazer')

    def test_confirmed_create_and_update_survive_refresh_failure(self):
        self.fail_after_write = True
        self.create()
        expect(self.page.locator('#backlog-status')).to_contain_text('História criada')
        expect(self.page.locator('#backlog-status')).to_contain_text('Atualize a lista')
        self.assertEqual(len(self.writes), 1)
        self.page.get_by_label('Status da história', exact=True).select_option('in_progress')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('Alterações salvas')
        self.assertEqual([w[0] for w in self.writes], ['POST', 'PATCH'])

    def test_pagination_prioritization_and_mobile_themes(self):
        self.stories = [{**STORY, 'id': str(uuid4()), 'project_id': PROJECT['id'], 'title': f'História {i}', 'priority': 'low'} for i in range(21)]
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        expect(self.page.locator('#backlog-count')).to_contain_text('1–20 de 21')
        self.page.locator('#backlog-next').click()
        expect(self.page.locator('#backlog-count')).to_contain_text('21–21 de 21')
        self.page.get_by_role('button', name='História 20', exact=True).click()
        self.page.get_by_label('Prioridade da história', exact=True).select_option('high')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-count')).to_contain_text('1–20 de 21')
        self.assertEqual(self.offsets[-1], 0)
        self.page.set_viewport_size({'width': 390, 'height': 844})
        for theme in ('light', 'dark'):
            self.page.evaluate('(t)=>document.documentElement.dataset.theme=t', theme)
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.get_by_label('Título da história', exact=True).focus()
        self.page.keyboard.press('Tab')
        expect(self.page.get_by_label('Descrição da história', exact=True)).to_be_focused()

    def test_service_failure_recovery_and_unauthorized_logout(self):
        self.list_status = 503
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('indisponível')
        self.list_status = 200
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        expect(self.page.get_by_role('button', name='Criar história', exact=True)).to_be_enabled()
        self.list_status = 404
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('não está disponível')
        self.capture_evidence('backlog-project-unavailable.png')
        self.list_status = 401
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        expect(self.page.locator('#login-view')).to_be_visible()
        expect(self.page.locator('#backlog-view')).to_be_hidden()

    def test_late_response_after_project_switch_and_logout_is_ignored(self):
        self.page.evaluate('''async ({p,s}) => {
          const {createBacklogController}=await import('/scripts/backlog.js');
          let resolveOld; let token='token';
          const api={list:(_,id)=>id===p.id?new Promise(r=>resolveOld=r):Promise.resolve({items:[],total:0,limit:20,offset:0})};
          const c=createBacklogController({api,getProject:async(_,id)=>({...p,id}),getUserId:()=>p.owner_id,
            getToken:()=>token,onUnauthorized:()=>{},onBack:()=>{}});
          const old=c.open(p); await c.open({id:'44444444-4444-4444-8444-444444444444',name:'Outro projeto'});
          resolveOld({items:[s],total:1,limit:20,offset:0}); await old;
          let resolveLogout;
          api.list=()=>new Promise(r=>resolveLogout=r);
          const pending=c.open({id:'55555555-5555-4555-8555-555555555555',name:'Projeto pendente'});
          token=null; c.clear(); resolveLogout({items:[s],total:1,limit:20,offset:0}); await pending;
        }''', {'p': PROJECT, 's': STORY})
        expect(self.page.locator('#backlog-view')).to_be_hidden()
        expect(self.page.locator('#backlog-list')).to_be_empty()

    def test_double_submit_creates_only_once(self):
        self.page.get_by_label('Título da história', exact=True).fill('Apenas uma vez')
        self.page.evaluate('''() => {const f=document.querySelector('#backlog-form'); f.requestSubmit();f.requestSubmit()}''')
        expect(self.page.locator('#backlog-status')).to_contain_text('História criada')
        self.assertEqual(len(self.writes), 1)

    def test_confirmed_create_then_401_keeps_confirmation_at_login(self):
        self.fail_after_write = True
        self.after_write_status = 401
        self.create()
        expect(self.page.locator('#login-view')).to_be_visible()
        expect(self.page.locator('#login-message')).to_contain_text('História criada')
        expect(self.page.locator('#login-message')).to_contain_text('sessão terminou')
        expect(self.page.locator('#backlog-list')).to_be_empty()
        self.assertEqual([w[0] for w in self.writes], ['POST'])
        self.capture_evidence('backlog-created-session-expired.png')

    def test_unicode_padding_does_not_create_empty_or_unreadable_titles(self):
        self.create(' \u0085\u001c ')
        expect(self.page.locator('#story-title-error')).to_be_visible()
        self.assertEqual(self.writes, [])
        self.create('\ufeff\u0085 História Unicode \u001f\ufeff')
        expect(self.page.locator('#backlog-list')).to_contain_text('História Unicode')
        self.assertEqual(self.writes[0][1]['title'], 'História Unicode')

    def test_confirmed_update_then_401_keeps_confirmation_at_login(self):
        self.create()
        expect(self.page.locator('#backlog-status')).to_contain_text('História criada')
        self.fail_after_write = True
        self.after_write_status = 401
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#login-view')).to_be_visible()
        expect(self.page.locator('#login-message')).to_contain_text('Alterações salvas')
        expect(self.page.locator('#backlog-list')).to_be_empty()
        self.assertEqual([w[0] for w in self.writes], ['POST', 'PATCH'])
        self.capture_evidence('backlog-updated-session-expired.png')
