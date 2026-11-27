"""Reload must preserve only a live session and revalidate it before rendering."""

from playwright.sync_api import expect

from browser_support import BrowserCase


class SessionReloadUiTests(BrowserCase):
    def sign_in(self, token=None):
        self.mock_auth(token=token)
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-email')).to_have_text(self.identity['email'])

    def test_reload_restores_login_without_posting_password_again(self):
        self.sign_in()
        self.page.route('**/auth/token', lambda route: self.fail('Reload must not submit a password'))
        self.page.reload()
        expect(self.page.locator('#profile-email')).to_have_text(self.identity['email'])
        expect(self.page.locator('#app-sidebar')).to_be_visible()
        self.assertNotIn('synthetic-token', self.page.content())
        self.assertNotIn('synthetic-token', self.page.evaluate('JSON.stringify(localStorage)'))

    def test_restored_credentials_do_not_show_profile_before_identity_validation(self):
        self.sign_in()
        pending = []
        self.page.route('**/auth/me', lambda route: pending.append(route))
        with self.page.expect_request('**/auth/me'):
            self.page.reload()
        expect(self.page.locator('#profile-view')).to_be_hidden()
        expect(self.page.locator('#app-sidebar')).to_be_hidden()
        pending[0].fulfill(json=self.identity)
        expect(self.page.locator('#profile-email')).to_have_text(self.identity['email'])

    def test_revoked_session_is_removed_on_reload(self):
        self.sign_in()
        self.page.route('**/auth/me', lambda route: route.fulfill(status=401))
        self.page.reload()
        expect(self.page.locator('#login-message')).to_contain_text('sessão terminou')
        expect(self.page.locator('#profile-view')).to_be_hidden()
        self.assertIsNone(self.page.evaluate("sessionStorage.getItem('mod1-session-v1')"))

    def test_logout_removes_credentials_and_reload_stays_signed_out(self):
        self.sign_in()
        self.page.evaluate("sessionStorage.setItem('unrelated-preference', 'keep')")
        self.page.get_by_role('button', name='Sair', exact=True).click()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        self.assertIsNone(self.page.evaluate("sessionStorage.getItem('mod1-session-v1')"))
        self.page.reload()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_enabled()
        expect(self.page.locator('#app-sidebar')).to_be_hidden()
        self.assertEqual(self.page.evaluate("sessionStorage.getItem('unrelated-preference')"), 'keep')

    def test_reload_keeps_original_access_expiry(self):
        self.sign_in()
        original = self.page.evaluate("JSON.parse(sessionStorage.getItem('mod1-session-v1')).accessExpiresAt")
        self.page.reload()
        expect(self.page.locator('#profile-email')).to_have_text(self.identity['email'])
        restored = self.page.evaluate("JSON.parse(sessionStorage.getItem('mod1-session-v1')).accessExpiresAt")
        self.assertEqual(restored, original)

    def test_expired_access_is_rotated_before_restoring_identity(self):
        token = {**self.token_response, 'refresh_token': 'original-refresh',
                 'session_id': '33333333-3333-4333-8333-333333333333',
                 'idle_expires_at': '2099-01-01T00:00:00Z',
                 'absolute_expires_at': '2099-01-01T01:00:00Z'}
        self.sign_in(token)
        self.page.evaluate('''() => {
          const key='mod1-session-v1', saved=JSON.parse(sessionStorage.getItem(key));
          saved.accessExpiresAt=Date.now()-1000; sessionStorage.setItem(key, JSON.stringify(saved));
        }''')
        self.page.route('**/auth/refresh', lambda route: route.fulfill(json={
            **token, 'access_token': 'rotated-access', 'refresh_token': 'rotated-refresh'}))
        self.page.route('**/auth/me', lambda route: route.fulfill(
            json=self.identity if route.request.headers.get('authorization') == 'Bearer rotated-access'
            else {}, status=200 if route.request.headers.get('authorization') == 'Bearer rotated-access' else 401))
        self.page.reload()
        expect(self.page.locator('#profile-email')).to_have_text(self.identity['email'])
        self.assertEqual(self.page.evaluate("JSON.parse(sessionStorage.getItem('mod1-session-v1')).refreshToken"),
                         'rotated-refresh')

    def test_invalid_storage_is_discarded_without_breaking_login(self):
        self.page.goto(self.base_url + '/__test__/')
        self.page.evaluate("sessionStorage.setItem('mod1-session-v1', '{broken-json')")
        self.page.goto(self.base_url)
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_enabled()
        self.assertIsNone(self.page.evaluate("sessionStorage.getItem('mod1-session-v1')"))

    def test_storage_denied_still_allows_current_page_login(self):
        self.page.add_init_script("Object.defineProperty(window, 'sessionStorage', {get(){throw new DOMException('Denied','SecurityError')}})")
        self.sign_in()
        expect(self.page.locator('#app-sidebar')).to_be_visible()

    def test_mfa_challenge_is_not_persisted_as_a_session(self):
        self.mock_auth(token={'mfa_required': True, 'challenge_token': 'private-challenge', 'expires_in': 300})
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_role('heading', name='Confirmar segundo fator')).to_be_visible()
        self.assertIsNone(self.page.evaluate("sessionStorage.getItem('mod1-session-v1')"))
        self.assertNotIn('private-challenge', self.page.evaluate('JSON.stringify(sessionStorage)'))

    def test_recovery_link_takes_precedence_over_saved_login(self):
        self.sign_in()
        self.page.route('**/auth/me', lambda route: self.fail('Recovery must not restore the profile'))
        self.page.goto(self.base_url + '/#recovery=private-recovery')
        expect(self.page.get_by_role('heading', name='Definir nova senha')).to_be_visible()
        expect(self.page.locator('#profile-view')).to_be_hidden()
        self.assertNotIn('private-recovery', self.page.evaluate('JSON.stringify(sessionStorage)'))

    def test_expired_access_without_refresh_is_discarded_on_reload(self):
        self.page.clock.install()
        self.sign_in(token={**self.token_response, 'expires_in': 30})
        self.page.clock.set_system_time(self.page.evaluate('Date.now()+31000'))
        self.page.route('**/auth/me', lambda route: self.fail('Expired credentials must not be restored'))
        self.page.reload()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_enabled()
        expect(self.page.locator('#app-sidebar')).to_be_hidden()
        self.assertIsNone(self.page.evaluate("sessionStorage.getItem('mod1-session-v1')"))

    def test_transient_identity_failure_preserves_saved_session_for_reload_retry(self):
        self.sign_in()
        self.page.route('**/auth/me', lambda route: route.fulfill(status=503))
        self.page.reload()
        expect(self.page.locator('#login-message')).to_contain_text('restaurar')
        expect(self.page.locator('#profile-view')).to_be_hidden()
        self.page.route('**/auth/me', lambda route: route.fulfill(json=self.identity))
        self.page.reload()
        expect(self.page.locator('#profile-email')).to_have_text(self.identity['email'])
