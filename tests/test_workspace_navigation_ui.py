"""Leaving a project workspace returns to the project list; account tools return home."""

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
        self.page.get_by_role('button', name='Gerenciar projeto e planejamento', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')
        self.page.get_by_role('button', name='Voltar para projetos', exact=True).click()
        expect(self.page.locator('#projects-view')).to_be_visible()
        expect(self.page.locator('#projects-title')).to_be_focused()
        expect(self.page.locator('#profile-view')).to_be_hidden()
        expect(self.page.locator('#workspace-view')).to_be_hidden()

    def test_leaving_account_workspace_returns_to_account_with_focus(self):
        self.page.get_by_role('button', name='Segurança e sessões', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')
        self.page.get_by_role('button', name='Voltar para minha conta', exact=True).click()
        expect(self.page.locator('#profile-view')).to_be_visible()
        expect(self.page.locator('#profile-title')).to_be_focused()
        expect(self.page.locator('#projects-view')).to_be_hidden()
        expect(self.page.locator('#workspace-view')).to_be_hidden()
