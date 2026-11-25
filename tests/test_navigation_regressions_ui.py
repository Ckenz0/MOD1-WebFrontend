"""Navigation must preserve one authorized screen and a reachable focus target."""

from playwright.sync_api import expect

from browser_support import BrowserCase


class NavigationRegressionsUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.mock_auth()
        self.project_status = 200
        self.available = True
        self.project = {
            'id': '55555555-5555-4555-8555-555555555555',
            'owner_id': '22222222-2222-4222-8222-222222222222',
            'name': 'Projeto compartilhado', 'description': 'PRIVATE cached project description',
            'objective': 'PRIVATE cached project objective',
            'created_at': '2026-11-15T12:00:00Z', 'status': 'active',
            'archived': False, 'version': 1, 'permissions': ['project:read', 'project:update'],
        }
        self.page.route('**/auth/session/activity', lambda route: route.fulfill(json={
            'idle_expires_at': '2099-01-01T00:00:00Z',
            'absolute_expires_at': '2099-01-01T01:00:00Z'}))
        self.page.route('**/auth/sessions', lambda route: route.fulfill(json={
            'items': [], 'total': 0, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects?*', lambda route: route.fulfill(json={
            'items': [self.project] if self.available else [],
            'total': 1 if self.available else 0, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects/' + self.project['id'], self.project_reply)

    def project_reply(self, route):
        if self.project_status != 200:
            self.available = False
            route.fulfill(status=self.project_status, json={'detail': 'Access revoked'})
        else:
            route.fulfill(json=self.project)

    def sign_in(self, path=''):
        self.page.goto(self.base_url + '/' + path)
        self.login()

    def test_login_restores_initial_security_address(self):
        self.sign_in('#/seguranca')
        expect(self.page.locator('#workspace-view')).to_be_visible()
        expect(self.page.locator('#profile-view')).to_be_hidden()
        expect(self.page.locator('#nav-security')).to_have_attribute('aria-current', 'page')
        expect(self.page).to_have_url(self.base_url + '/#/seguranca')

    def test_denied_project_overview_erases_private_cache_and_actions(self):
        for status in (403, 404):
            with self.subTest(status=status):
                self.available = True
                self.project_status = status
                self.sign_in()
                self.page.locator('#nav-projects').click()
                self.page.get_by_role('button', name=self.project['name'], exact=True).click()
                expect(self.page.locator('#projects-status')).to_have_attribute('data-tone', 'error')
                expect(self.page.locator('#projects-view')).to_be_visible()
                expect(self.page.locator('#workspace-view')).to_be_hidden()
                expect(self.page.locator('#project-detail-description')).to_have_text('')
                expect(self.page.locator('#project-detail-objective')).to_have_text('')
                expect(self.page.get_by_role('button', name='Editar projeto', exact=True)).to_be_hidden()
                self.assertNotIn('PRIVATE cached', self.page.locator('body').inner_text())
                self.page.go_back()
                expect(self.page.locator('#projects-view')).to_be_visible()
                self.assertNotIn('PRIVATE cached', self.page.locator('body').inner_text())

    def test_signed_in_public_link_is_cleared_on_app_navigation(self):
        self.sign_in()
        expect(self.page.locator('#profile-view')).to_be_visible()
        for destination in ('#nav-projects', '#nav-home', '#nav-security'):
            with self.subTest(destination=destination):
                self.page.evaluate("location.hash = 'verify-email=synthetic-verification-token'")
                expect(self.page.locator('#recovery-view')).to_be_visible()
                self.page.locator(destination).click()
                expect(self.page.locator('#recovery-view')).to_be_hidden()
                self.assertNotIn('synthetic-verification-token', self.page.url)

    def test_phone_menu_keeps_focus_and_releases_content_on_close_and_resize(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.sign_in()
        toggle = self.page.locator('#sidebar-toggle')
        toggle.click()
        for key in ('Tab',) * 12 + ('Shift+Tab',) * 12:
            self.page.keyboard.press(key)
            self.assertTrue(self.page.evaluate(
                "document.getElementById('sidebar-panel').contains(document.activeElement)"))
        self.assertTrue(self.page.locator('#main').evaluate('node => node.inert'))
        self.page.keyboard.press('Escape')
        expect(toggle).to_be_focused()
        self.assertFalse(self.page.locator('#main').evaluate('node => node.inert'))
        toggle.click()
        self.page.set_viewport_size({'width': 1366, 'height': 900})
        expect(toggle).to_have_attribute('aria-expanded', 'false')
        self.assertFalse(self.page.locator('#main').evaluate('node => node.inert'))

    def test_phone_menu_logout_releases_login_form(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.sign_in()
        self.page.locator('#sidebar-toggle').click()
        self.page.locator('#logout-button').click()
        expect(self.page.locator('#login-view')).to_be_visible()
        self.assertFalse(self.page.locator('#main').evaluate('node => node.inert'))
        expect(self.page.get_by_label('E-mail', exact=True)).to_be_editable()
