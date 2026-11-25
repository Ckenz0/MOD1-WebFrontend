"""The sidebar, the project breadcrumb and the browser history all lead to the same screens."""

from playwright.sync_api import expect

from browser_support import BrowserCase


class WorkspaceNavigationUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.mock_auth()
        project = {'id': '55555555-5555-4555-8555-555555555555',
            'owner_id': self.identity['id'], 'name': 'Projeto de navegação',
            'description': 'Entrega compartilhada', 'objective': 'Planejar',
            'created_at': '2026-11-15T12:00:00Z', 'status': 'active', 'archived': False,
            'version': 1, 'permissions': ['project:read']}
        self.page.route('**/auth/session/activity', lambda route: route.fulfill(json={
            'idle_expires_at': '2099-01-01T00:00:00Z', 'absolute_expires_at': '2099-01-01T01:00:00Z'}))
        self.page.route('**/auth/sessions', lambda route: route.fulfill(json={
            'items': [], 'total': 0, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects?*', lambda route: route.fulfill(json={
            'items': [project], 'total': 1, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects/' + project['id'], lambda route: route.fulfill(json=project))
        self.page.route('**/projects/' + project['id'] + '/summary', lambda route: route.fulfill(json={
            'project': project, 'teams': [], 'backlog_available': False, 'backlog': None}))
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def test_leaving_project_workspace_returns_to_projects_with_focus(self):
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto de navegação', exact=True).click()
        self.page.get_by_role('button', name='Planejamento', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')
        self.page.locator('.breadcrumb').get_by_role('link', name='Projetos', exact=True).click()
        expect(self.page.locator('#projects-view')).to_be_visible()
        expect(self.page.locator('#projects-title')).to_be_focused()
        expect(self.page.locator('#profile-view')).to_be_hidden()
        expect(self.page.locator('#workspace-view')).to_be_hidden()

    def test_leaving_account_workspace_returns_to_account_with_focus(self):
        self.page.get_by_role('link', name='Segurança e sessões', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')
        expect(self.page.get_by_role('link', name='Segurança e sessões', exact=True)).to_have_attribute('aria-current', 'page')
        self.page.get_by_role('link', name='Início', exact=True).click()
        expect(self.page.locator('#profile-view')).to_be_visible()
        expect(self.page.locator('#profile-title')).to_be_focused()
        expect(self.page.locator('#projects-view')).to_be_hidden()
        expect(self.page.locator('#workspace-view')).to_be_hidden()

    def test_browser_back_and_forward_follow_sections_and_project_tabs(self):
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        expect(self.page).to_have_url(self.base_url + '/#/projetos')
        self.page.get_by_role('button', name='Projeto de navegação', exact=True).click()
        expect(self.page.locator('#workspace-title')).to_have_text('Projeto de navegação')
        self.page.get_by_role('button', name='Planejamento', exact=True).click()
        expect(self.page).to_have_url(self.base_url + '/#/projetos/55555555-5555-4555-8555-555555555555/planejamento')
        self.page.go_back()
        expect(self.page.locator('.workspace-tab[aria-current="page"]')).to_have_text('Visão geral')
        self.page.go_back()
        expect(self.page.locator('#projects-view')).to_be_visible()
        expect(self.page.locator('#nav-projects')).to_have_attribute('aria-current', 'page')
        self.page.go_forward()
        expect(self.page.locator('#workspace-title')).to_have_text('Projeto de navegação')
        expect(self.page.locator('#projects-view')).to_be_hidden()

    def test_phone_menu_opens_as_a_sheet_and_closes_after_choosing(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        toggle = self.page.get_by_role('button', name='Menu', exact=True)
        expect(toggle).to_have_attribute('aria-expanded', 'false')
        expect(self.page.locator('#nav-projects')).to_be_hidden()
        toggle.click()
        expect(toggle).to_have_attribute('aria-expanded', 'true')
        expect(self.page.locator('#nav-projects')).to_be_in_viewport()
        self.page.locator('#nav-projects').click()
        expect(self.page.locator('#projects-view')).to_be_visible()
        expect(toggle).to_have_attribute('aria-expanded', 'false')
        toggle.click()
        self.page.keyboard.press('Escape')
        expect(toggle).to_be_focused()
        self.assertTrue(self.evaluate('() => document.documentElement.scrollWidth <= innerWidth'))

    def test_access_check_appears_on_security_only_after_sign_in(self):
        check = self.page.locator('#access-check')
        expect(check).to_be_hidden()
        self.page.get_by_role('link', name='Segurança e sessões', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')
        expect(check).to_be_visible()
        workspace_bottom = self.evaluate("() => document.getElementById('workspace-view').getBoundingClientRect().bottom")
        self.assertGreaterEqual(check.bounding_box()['y'], workspace_bottom - 1, 'The check follows the security content')
        self.page.locator('#nav-projects').click()
        expect(check).to_be_hidden()

    def test_tab_indicator_spans_the_label_text(self):
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto de navegação', exact=True).click()
        self.page.get_by_role('button', name='Planejamento', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')
        self.page.wait_for_timeout(350)
        boxes = self.evaluate("""() => {
          const tab = document.querySelector('.workspace-tab[aria-current="page"]');
          const range = document.createRange(); range.selectNodeContents(tab);
          const text = range.getBoundingClientRect(), bar = document.querySelector('.tab-indicator').getBoundingClientRect();
          return {textLeft: text.left, textRight: text.right, barLeft: bar.left, barRight: bar.right};
        }""")
        self.assertAlmostEqual(boxes['barLeft'], boxes['textLeft'], delta=1.5)
        self.assertAlmostEqual(boxes['barRight'], boxes['textRight'], delta=1.5)
