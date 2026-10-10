from playwright.sync_api import expect

from browser_support import BrowserCase


class UiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.page.goto(self.base_url).status, 200,
                         'The login page must exist before user flows can run')
        self.assertEqual(self.page.get_by_role('heading', name='Entrar', exact=True).count(), 1,
                         'The page must present the login form')

    def test_login_displays_identity_without_exposing_token(self):
        self.mock_auth()
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        self.assertNotIn('synthetic-token', self.page.content())
        self.assertEqual(self.page.evaluate('sessionStorage.length'), 0)
        self.assertNotIn('synthetic-token', self.page.evaluate('JSON.stringify(localStorage)'))
        self.page.get_by_role('button', name='Sair', exact=True).click()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        self.assertEqual(self.page.get_by_label('Senha', exact=True).input_value(), '')

    def test_identity_required_before_showing_profile(self):
        pending = []
        self.page.route('**/auth/token', lambda route: route.fulfill(json=self.token_response))
        self.page.route('**/auth/me', lambda route: pending.append(route))
        self.page.goto(self.base_url)
        with self.page.expect_request('**/auth/me'):
            self.login()
        expect(self.page.get_by_role('button', name='Sair', exact=True)).to_be_hidden()
        pending[0].fulfill(json=self.identity)
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()

    def test_login_errors_and_duplicate_submit(self):
        pending = []
        self.page.route('**/auth/token', lambda route: pending.append(route))
        self.page.goto(self.base_url)
        self.page.get_by_label('E-mail', exact=True).fill('conta@example.com')
        self.page.get_by_label('Senha', exact=True).fill('password12345')
        with self.page.expect_request('**/auth/token'):
            self.page.evaluate('document.querySelector("form").requestSubmit(); document.querySelector("form").requestSubmit()')
        expect(self.page.get_by_role('button', name='Entrando…', exact=True)).to_be_disabled()
        self.assertEqual(len(pending), 1)
        pending[0].fulfill(status=401, json={'detail': 'Invalid credentials'})
        expect(self.page.get_by_role('alert')).to_contain_text('E-mail ou senha inválidos')
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_enabled()

    def test_unavailable_service_can_be_retried(self):
        self.page.route('**/auth/token', lambda route: route.fulfill(status=503))
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_role('alert')).to_contain_text('indisponível')
        self.mock_auth()
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()

    def test_network_failure_is_explained(self):
        self.page.route('**/auth/token', lambda route: route.abort('connectionrefused'))
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_role('alert')).to_contain_text('conectar')
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_enabled()

    def test_logout_ignores_late_identity(self):
        self.mock_auth()
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        pending = []
        self.page.route('**/auth/me', lambda route: pending.append(route))
        with self.page.expect_request('**/auth/me'):
            self.page.get_by_role('button', name='Atualizar dados', exact=True).click()
        self.page.get_by_role('button', name='Sair', exact=True).click()
        pending[0].fulfill(json={**self.identity, 'display_name': 'Late response'})
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Sair', exact=True)).to_be_hidden()
        expect(self.page.get_by_text('Late response')).to_be_hidden()

    def test_expiration_after_hidden_tab(self):
        self.page.clock.install()
        self.mock_auth(token={**self.token_response, 'expires_in': 30})
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        self.page.clock.set_system_time(self.page.evaluate('Date.now() + 31000'))
        self.page.evaluate('document.dispatchEvent(new Event("visibilitychange"))')
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        expect(self.page.get_by_role('alert')).to_contain_text('sessão')

    def test_unauthorized_update_returns_to_login(self):
        self.mock_auth()
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        self.page.route('**/auth/me', lambda route: route.fulfill(status=401))
        self.page.get_by_role('button', name='Atualizar dados', exact=True).click()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()

    def test_update_network_failure_preserves_identity(self):
        self.mock_auth()
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        self.page.route('**/auth/me', lambda route: route.abort('connectionrefused'))
        self.page.get_by_role('button', name='Atualizar dados', exact=True).click()
        expect(self.page.get_by_role('alert')).to_contain_text('conectar')
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()

    def test_refresh_success_is_announced(self):
        self.mock_auth()
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        self.page.get_by_role('button', name='Atualizar dados', exact=True).click()
        expect(self.page.locator('#profile-progress')).to_have_text('Dados atualizados.')

    def test_untrusted_long_identity_is_plain_text(self):
        name = '<img src=x onerror=alert(1)>'
        email = 'x' * 100 + '@example.com'
        self.mock_auth(identity={**self.identity, 'display_name': name, 'email': email})
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text(email, exact=True)).to_be_visible()
        expect(self.page.get_by_role('heading').filter(has_text=name)).to_be_visible()
        self.assertEqual(self.page.locator('img').count(), 0)
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))

    def test_theme_when_storage_is_blocked(self):
        self.page.add_init_script('''Storage.prototype.getItem=()=>{throw new Error('blocked')};
          Storage.prototype.setItem=()=>{throw new Error('blocked')};''')
        self.mock_auth()
        self.page.goto(self.base_url)
        self.page.get_by_role('button', name='Ativar tema escuro').click()
        self.assertEqual(self.page.locator('html').get_attribute('data-theme'), 'dark')
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()

    def test_selected_text_contrast_in_both_themes(self):
        for theme in ('light', 'dark'):
            self.page.locator('html').evaluate('(el, theme) => el.dataset.theme = theme', theme)
            contrast = self.page.evaluate('''() => {
              const style = getComputedStyle(document.body, '::selection');
              const luminance = color => {
                const channels = color.match(/\\d+/g).slice(0,3).map(Number)
                  .map(value => value / 255)
                  .map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
                return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
              };
              const values = [luminance(style.color), luminance(style.backgroundColor)].sort((a,b)=>a-b);
              return (values[1] + .05) / (values[0] + .05);
            }''')
            self.assertGreaterEqual(contrast, 4.5, f'Selected text must be readable in {theme} theme')

    def test_reload_loses_session_and_preserves_theme(self):
        self.mock_auth()
        self.page.goto(self.base_url)
        self.page.get_by_role('button', name='Ativar tema escuro').click()
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        self.page.reload()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        self.assertEqual(self.page.locator('html').get_attribute('data-theme'), 'dark')

    def test_password_toggle_and_keyboard_submission(self):
        self.mock_auth()
        self.page.goto(self.base_url)
        field = self.page.get_by_label('Senha', exact=True)
        self.page.get_by_label('E-mail', exact=True).fill('conta@example.com')
        field.fill('  password12345  ')
        self.page.get_by_role('button', name='Mostrar senha', exact=True).click()
        self.assertEqual(field.get_attribute('type'), 'text')
        self.assertEqual(field.input_value(), '  password12345  ')
        self.page.get_by_role('button', name='Ocultar senha', exact=True).click()
        self.assertEqual(field.get_attribute('type'), 'password')
        field.press('Enter')
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
