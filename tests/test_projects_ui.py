import re
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect

from browser_support import BrowserCase
from test_projects_api import PROJECT

PROJECT_ROUTES = re.compile(r"/projects(?:[/?]|$)")


class ProjectsUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.mock_auth()
        self.items = []
        self.posts = []
        self.page.route(PROJECT_ROUTES, self.handle_projects)
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def handle_projects(self, route):
        request = route.request
        url = urlsplit(request.url)
        if request.method == 'OPTIONS':
            route.fulfill(status=200)
        elif request.method == 'POST':
            draft = request.post_data_json
            self.posts.append(draft)
            p = {**PROJECT, **draft}
            self.items.insert(0, p)
            route.fulfill(status=201, json=p)
        elif url.path.endswith('/projects'):
            query = parse_qs(url.query)
            limit = int(query.get('limit', ['20'])[0])
            offset = int(query.get('offset', ['0'])[0])
            route.fulfill(json={'items': self.items[offset:offset+limit], 'total': len(self.items),
                                'limit': limit, 'offset': offset})
        else:
            route.fulfill(json=next(p for p in self.items if url.path.endswith(p['id'])))

    def open_projects(self):
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        expect(self.page.locator('#projects-view')).to_be_visible()

    def test_empty_create_and_detail(self):
        self.open_projects()
        expect(self.page.locator('#projects-list')).to_contain_text('Você ainda não tem projetos')
        self.page.get_by_label('Nome do projeto', exact=True).fill('  Primeiro projeto  ')
        self.page.get_by_label('Descrição', exact=True).fill('linha 1\nlinha 2')
        self.page.get_by_role('button', name='Criar projeto', exact=True).click()
        expect(self.page.locator('#projects-list')).to_contain_text('Primeiro projeto')
        expect(self.page.locator('#project-detail')).to_contain_text('linha 1\nlinha 2')
        self.assertEqual(self.posts, [{'name': 'Primeiro projeto', 'description': 'linha 1\nlinha 2'}])
        self.page.get_by_role('button', name='Voltar para minha conta', exact=True).click()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def test_project_field_validation_and_keyboard(self):
        self.open_projects()
        self.page.get_by_role('button', name='Criar projeto', exact=True).click()
        expect(self.page.locator('#project-name')).to_have_attribute('aria-invalid', 'true')
        expect(self.page.locator('#project-name')).to_be_focused()
        self.page.locator('#project-name').fill('😀'*121)
        self.page.locator('#project-description').fill('x'*2001)
        self.page.locator('#project-submit').click()
        self.assertEqual(self.posts, [])
        expect(self.page.locator('#project-description')).to_have_attribute('aria-invalid', 'true')
        self.page.locator('#project-name').fill('😀'*120)
        self.page.locator('#project-description').fill('x'*2000)
        self.page.locator('#project-submit').focus()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('#project-detail')).to_be_visible()
        self.assertEqual(len(self.posts), 1)

    def test_single_submit_and_recoverable_failure(self):
        self.open_projects()
        pending = []
        self.page.route('**/projects', lambda route: pending.append(route))
        self.page.locator('#project-name').fill('A')
        self.page.locator('#project-submit').click()
        expect(self.page.locator('#project-submit')).to_be_disabled()
        self.page.locator('#project-form').evaluate('(form)=>form.requestSubmit()')
        self.assertEqual(len(pending), 1)
        pending[0].fulfill(status=503, body='private-sql')
        expect(self.page.locator('#projects-status')).to_contain_text('indisponível')
        expect(self.page.locator('#project-submit')).to_be_enabled()
        self.assertNotIn('private-sql', self.page.locator('#projects-status').inner_text())
        self.assertEqual(len(pending), 1)

    def test_project_text_is_inert(self):
        p = {**PROJECT, 'name': '<img src=x onerror=alert(1)>', 'description': 'linha 1\nlinha 2'}
        self.items = [p]
        self.open_projects()
        self.page.get_by_role('button', name=p['name'], exact=True).click()
        expect(self.page.locator('#project-detail')).to_contain_text(p['name'])
        self.assertEqual(self.page.locator('#project-detail img').count(), 0)
        self.assertEqual(self.page.locator('#project-detail-description').inner_text(), p['description'])

    def test_unauthorized_ends_session(self):
        self.page.route(PROJECT_ROUTES, lambda route: route.fulfill(status=401, body='private-token'))
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        expect(self.page.locator('#login-view')).to_be_visible()
        expect(self.page.locator('#projects-view')).to_be_hidden()
        self.assertEqual(self.page.locator('#projects-list').inner_text(), '')

    def test_network_failure_can_retry(self):
        self.page.route(PROJECT_ROUTES, lambda route: route.abort('failed'))
        self.open_projects()
        expect(self.page.locator('#projects-status')).to_contain_text('conectar')
        self.page.unroute(PROJECT_ROUTES)
        self.page.route(PROJECT_ROUTES, self.handle_projects)
        self.page.get_by_role('button', name='Atualizar projetos', exact=True).click()
        expect(self.page.locator('#projects-list')).to_contain_text('Você ainda não tem projetos')

    def test_pagination(self):
        self.items = [{**PROJECT, 'id': f'{n:08x}-2222-4222-8222-222222222222', 'name': f'Projeto {n}'}
                      for n in range(21)]
        self.open_projects()
        expect(self.page.locator('#projects-list button')).to_have_count(20)
        self.page.locator('#projects-next').click()
        expect(self.page.locator('#projects-list button')).to_have_count(1)
        expect(self.page.locator('#projects-list')).to_contain_text('Projeto 20')
        self.page.locator('#projects-previous').click()
        expect(self.page.locator('#projects-list button')).to_have_count(20)

    def test_logout_then_other_login_ignores_late_project_response(self):
        result = self.evaluate('''async p=>{
          const {createProjectsController}=await import('/scripts/projects.js');
          let token='A',resolveA;
          const api={list:()=>token==='A'?new Promise(r=>resolveA=r):Promise.resolve({items:[],total:0,limit:20,offset:0})};
          const controller=createProjectsController({api,getToken:()=>token,onUnauthorized:()=>{},onBack:()=>{}});
          const pending=controller.open();controller.clear();token='B';await controller.open();
          resolveA({items:[p],total:1,limit:20,offset:0});await pending;
          const list=document.getElementById('projects-list').textContent;
          controller.clear();
          return {list,cleared:document.getElementById('projects-list').textContent};
        }''', PROJECT)
        self.assertNotIn(PROJECT['name'], result['list'])
        self.assertIn('Você ainda não tem projetos', result['list'])
        self.assertEqual(result['cleared'], '')

    def test_mobile_and_dark_layout(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.emulate_media(color_scheme='dark')
        self.items = [{**PROJECT, 'name': 'A'*120, 'description': 'x'*2000}]
        self.open_projects()
        self.page.locator('#projects-list button').click()
        self.assertTrue(self.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        expect(self.page.locator('#project-detail')).to_be_visible()
