import re
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect

from browser_support import BrowserCase
from test_backlog_api import STORY
from test_projects_api import PROJECT


class ManagementUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.mock_auth()
        self.project = {**PROJECT, 'objective': 'Objetivo original'}
        self.story = {**STORY}
        self.writes = []
        self.queries = []
        self.password_status = 204
        self.page.route('**/auth/password-policy', lambda r: r.fulfill(json={'min_length': 16, 'max_length': 128}))
        self.page.route('**/auth/password', self.password_response)
        self.page.route(re.compile(r'/projects(?:[/?]|$)'), self.project_response)
        self.page.route('**/projects/*/stories**', self.story_response)
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def password_response(self, route):
        self.writes.append(('password', route.request.post_data_json))
        if self.password_status == 204:
            route.fulfill(status=204)
        else:
            route.fulfill(status=self.password_status, json={'detail': 'private-debug-data'})

    def project_response(self, route):
        request = route.request
        url = urlsplit(request.url)
        query = parse_qs(url.query)
        if request.method == 'PATCH':
            self.writes.append(('project', request.post_data_json))
            self.project.update(request.post_data_json)
            route.fulfill(json=self.project)
        elif url.path.endswith('/projects'):
            self.queries.append(('project', query))
            items = [self.project] if query.get('q', [''])[0].casefold() in self.project['name'].casefold() else []
            route.fulfill(json={'items': items, 'total': len(items), 'limit': 20, 'offset': 0})
        else:
            route.fulfill(json=self.project)

    def story_response(self, route):
        request = route.request
        url = urlsplit(request.url)
        if request.method == 'PATCH':
            self.writes.append(('story', request.post_data_json))
            self.story.update(request.post_data_json)
            route.fulfill(json=self.story)
        elif url.path.endswith('/stories'):
            query = parse_qs(url.query)
            self.queries.append(('story', query))
            matches = (query.get('q', [''])[0].casefold() in (self.story['title'] + self.story['description']).casefold()
                       and query.get('status', [self.story['status']])[0] == self.story['status']
                       and query.get('priority', [self.story['priority']])[0] == self.story['priority'])
            items = [self.story] if matches else []
            route.fulfill(json={'items': items, 'total': len(items), 'limit': 20, 'offset': 0})
        else:
            route.fulfill(json=self.story)

    def open_project(self):
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name=self.project['name'], exact=True).click()
        expect(self.page.locator('#project-detail')).to_be_visible()

    def test_password_change_uses_policy_and_clears_session_on_success(self):
        self.page.get_by_role('button', name='Alterar senha', exact=True).click()
        expect(self.page.locator('#password-policy-hint')).to_contain_text('16 a 128')
        self.page.get_by_label('Senha atual', exact=True).fill('  password12345  ')
        self.page.get_by_label('Nova senha', exact=True).fill('short-password')
        self.page.get_by_label('Confirme a nova senha', exact=True).fill('short-password')
        self.page.get_by_role('button', name='Salvar nova senha', exact=True).click()
        expect(self.page.locator('#new-password')).to_have_attribute('aria-invalid', 'true')
        self.assertEqual(self.writes, [])
        self.page.get_by_label('Nova senha', exact=True).fill('  A-new-password!2026  ')
        self.page.get_by_label('Confirme a nova senha', exact=True).fill('  A-new-password!2026  ')
        self.page.get_by_role('button', name='Salvar nova senha', exact=True).click()
        expect(self.page.locator('#login-message')).to_contain_text('Senha alterada')
        self.assertEqual(self.writes, [('password', {
            'current_password': '  password12345  ', 'new_password': '  A-new-password!2026  '
        })])
        for field in ('current-password', 'new-password', 'confirm-new-password'):
            expect(self.page.locator('#' + field)).to_have_value('')
        expect(self.page.locator('#profile-view')).to_be_hidden()

    def test_password_rejection_keeps_identity_and_safe_message(self):
        self.password_status = 400
        self.page.get_by_role('button', name='Alterar senha', exact=True).click()
        self.page.get_by_label('Senha atual', exact=True).fill('incorrect-password')
        self.page.get_by_label('Nova senha', exact=True).fill('A-new-password!2026')
        self.page.get_by_label('Confirme a nova senha', exact=True).fill('A-new-password!2026')
        self.page.get_by_role('button', name='Salvar nova senha', exact=True).click()
        expect(self.page.locator('#password-change-message')).to_contain_text('senha atual')
        expect(self.page.locator('#password-change-message')).not_to_contain_text('private-debug-data')
        expect(self.page.locator('#profile-view')).to_be_visible()

    def test_project_edit_objective_cancel_and_search(self):
        self.open_project()
        self.page.get_by_role('button', name='Editar projeto', exact=True).click()
        self.page.get_by_label('Nome do projeto para edição', exact=True).fill('Descartar rascunho')
        self.page.get_by_role('button', name='Cancelar edição do projeto', exact=True).click()
        expect(self.page.locator('#project-detail-title')).to_have_text(PROJECT['name'])
        self.assertEqual(self.writes, [])
        self.page.get_by_role('button', name='Editar projeto', exact=True).click()
        self.page.get_by_label('Nome do projeto para edição', exact=True).fill('  Projeto revisado  ')
        self.page.get_by_label('Descrição do projeto para edição', exact=True).fill('<b>texto literal</b>')
        self.page.get_by_label('Objetivo do projeto para edição', exact=True).fill('Entregar valor verificável')
        self.page.get_by_role('button', name='Salvar projeto', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('Projeto atualizado')
        expect(self.page.locator('#project-detail-objective')).to_have_text('Entregar valor verificável')
        self.assertEqual(self.writes[-1], ('project', {
            'name': 'Projeto revisado', 'description': '<b>texto literal</b>',
            'objective': 'Entregar valor verificável'
        }))
        self.assertEqual(self.page.locator('#project-detail-description b').count(), 0)
        self.page.get_by_label('Buscar projetos pelo nome', exact=True).fill('inexistente')
        self.page.get_by_role('button', name='Buscar projetos', exact=True).click()
        expect(self.page.locator('#projects-list')).to_contain_text('Nenhum projeto encontrado')
        self.assertEqual(self.queries[-1][1]['q'], ['inexistente'])

    def test_story_edit_and_filters(self):
        self.open_project()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        self.page.get_by_role('button', name=self.story['title'], exact=True).click()
        self.page.get_by_label('Editar título da história', exact=True).fill('História refinada')
        self.page.get_by_label('Editar descrição da história', exact=True).fill('Necessidade refinada')
        self.page.get_by_label('Editar critérios de aceite', exact=True).fill('Dado X, quando Y, então Z')
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('Alterações salvas')
        self.assertEqual(self.writes[-1][1]['title'], 'História refinada')
        expect(self.page.locator('#story-detail-criteria')).to_have_text('Dado X, quando Y, então Z')
        self.page.get_by_label('Buscar histórias', exact=True).fill('refinada')
        self.page.get_by_label('Filtrar por status', exact=True).select_option('todo')
        self.page.get_by_label('Filtrar por prioridade', exact=True).select_option('medium')
        self.page.get_by_role('button', name='Aplicar filtros', exact=True).click()
        expect(self.page.locator('#backlog-list')).to_contain_text('Nenhuma história encontrada')
        self.assertEqual(self.queries[-1][1]['status'], ['todo'])
        self.assertEqual(self.queries[-1][1]['priority'], ['medium'])
        self.assertEqual(self.queries[-1][1]['q'], ['refinada'])

    def test_project_save_failure_preserves_draft_and_logout_clears_it(self):
        self.open_project()
        self.page.get_by_role('button', name='Editar projeto', exact=True).click()
        self.page.get_by_label('Nome do projeto para edição', exact=True).fill('Rascunho importante')
        self.page.route('**/projects/' + PROJECT['id'], lambda r: r.fulfill(status=503))
        self.page.get_by_role('button', name='Salvar projeto', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('indisponível')
        expect(self.page.get_by_label('Nome do projeto para edição', exact=True)).to_have_value('Rascunho importante')
        self.page.locator('#projects-logout').click()
        expect(self.page.locator('#project-edit-name')).to_have_value('')

    def test_client_contracts_include_edits_and_filter_parameters(self):
        self.page.goto(self.base_url + '/__test__/')
        result = self.evaluate('''async ({p,s})=>{
          const {createApiClient}=await import('/scripts/api.js');
          const {createProjectsApiClient}=await import('/scripts/projects-api.js');
          const {createBacklogApiClient}=await import('/scripts/backlog-api.js');
          const calls=[];
          const record=(value,status=200)=>async(url,o)=>{calls.push({url,method:o.method,headers:o.headers,body:o.body});return new Response(status===204?null:JSON.stringify(value),{status});};
          const auth=createApiClient({baseUrl:location.origin,fetchImpl:record(null,204)});
          await auth.changePassword('token',' old-password ',' new-password ');
          const projects=createProjectsApiClient({baseUrl:location.origin,fetchImpl:record(p)});
          await projects.update('token',p.id,{name:'New',objective:'Value'});
          const empty={items:[],total:0,limit:20,offset:0};
          const list=createProjectsApiClient({baseUrl:location.origin,fetchImpl:record(empty)});
          await list.list('token',{q:'100%_value'});
          const backlog=createBacklogApiClient({baseUrl:location.origin,fetchImpl:record(empty)});
          await backlog.list('token',s.project_id,{q:'100%_value',status:'done',priority:'high'});
          return calls;
        }''', {'p': self.project, 's': self.story})
        self.assertEqual(result[0]['method'], 'POST')
        self.assertEqual(result[0]['headers']['Authorization'], 'Bearer token')
        self.assertEqual(result[1]['method'], 'PATCH')
        self.assertEqual(parse_qs(urlsplit(result[2]['url']).query)['q'], ['100%_value'])
        self.assertEqual(parse_qs(urlsplit(result[3]['url']).query)['status'], ['done'])

    def test_logout_discards_late_password_success(self):
        pending = []
        self.page.route('**/auth/password', lambda r: pending.append(r))
        self.page.get_by_role('button', name='Alterar senha', exact=True).click()
        self.page.get_by_label('Senha atual', exact=True).fill('  password12345  ')
        self.page.get_by_label('Nova senha', exact=True).fill('Uma-nova-senha!2026')
        self.page.get_by_label('Confirme a nova senha', exact=True).fill('Uma-nova-senha!2026')
        self.page.get_by_role('button', name='Salvar nova senha', exact=True).click()
        expect(self.page.locator('#password-change-save')).to_be_disabled()
        self.page.locator('#password-change-form').evaluate('(form)=>form.requestSubmit()')
        self.assertEqual(len(pending), 1)
        self.page.locator('#logout-button').click()
        pending[0].fulfill(status=204)
        expect(self.page.locator('#login-message')).to_have_text('Você saiu da sua conta.')
        expect(self.page.locator('#profile-view')).to_be_hidden()
        expect(self.page.locator('#current-password')).to_have_value('')

    def test_saved_project_followed_by_reload_failure_confirms_write(self):
        self.open_project()
        self.page.get_by_role('button', name='Editar projeto', exact=True).click()
        self.page.get_by_label('Nome do projeto para edição', exact=True).fill('Projeto confirmado')
        self.page.route('**/projects?*', lambda r: r.fulfill(status=503))
        self.page.get_by_role('button', name='Salvar projeto', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('Projeto atualizado. Atualize a lista')
        expect(self.page.locator('#project-detail-title')).to_have_text('Projeto confirmado')
        self.assertEqual(len(self.writes), 1)

    def test_saved_project_followed_by_reload_401_keeps_success_notice(self):
        self.open_project()
        self.page.get_by_role('button', name='Editar projeto', exact=True).click()
        self.page.get_by_label('Nome do projeto para edição', exact=True).fill('Salvo antes do 401')
        self.page.route('**/projects?*', lambda r: r.fulfill(status=401))
        self.page.get_by_role('button', name='Salvar projeto', exact=True).click()
        expect(self.page.locator('#login-message')).to_contain_text('Projeto atualizado')
        expect(self.page.locator('#login-message')).to_contain_text('Sua sessão terminou')
        self.assertEqual(self.project['name'], 'Salvo antes do 401')

    def test_refresh_failure_preserves_project_edit_draft(self):
        self.open_project()
        self.page.get_by_role('button', name='Editar projeto', exact=True).click()
        self.page.get_by_label('Nome do projeto para edição', exact=True).fill('Rascunho sem salvar')
        self.page.route('**/projects?*', lambda r: r.fulfill(status=503))
        self.page.get_by_role('button', name='Atualizar projetos', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('indisponível')
        expect(self.page.locator('#project-edit-form')).to_be_visible()
        expect(self.page.locator('#project-edit-name')).to_have_value('Rascunho sem salvar')

    def test_refresh_failure_preserves_story_edit_draft(self):
        self.open_project()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        self.page.get_by_role('button', name=self.story['title'], exact=True).click()
        self.page.get_by_label('Editar título da história', exact=True).fill('Refinamento sem salvar')
        self.page.route('**/projects/*/stories?*', lambda r: r.fulfill(status=503))
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('indisponível')
        expect(self.page.locator('#story-detail')).to_be_visible()
        expect(self.page.locator('#story-update-title')).to_have_value('Refinamento sem salvar')
