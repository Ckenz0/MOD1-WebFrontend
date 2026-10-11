from playwright.sync_api import expect

from browser_support import BrowserCase


class RegistrationUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url)

    def open_registration(self):
        opener = self.page.get_by_role('button', name='Criar conta', exact=True)
        self.assertEqual(opener.count(), 1, 'Users need a way to open registration')
        opener.click()

    def fill_registration(self):
        self.page.get_by_label('Nome', exact=True).fill('Pessoa nova')
        self.page.get_by_label('E-mail de cadastro', exact=True).fill('nova@example.com')
        self.page.get_by_label('Crie uma senha', exact=True).fill('  senha-nova-12345  ')
        self.page.get_by_label('Confirme sua senha', exact=True).fill('  senha-nova-12345  ')

    def test_login_validation_focuses_first_invalid_field_without_request(self):
        requests = []
        self.page.route('**/auth/token', lambda route: requests.append(route))
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.locator('#email-error')).to_be_visible()
        expect(self.page.get_by_label('E-mail', exact=True)).to_be_focused()
        expect(self.page.get_by_label('E-mail', exact=True)).to_have_attribute('aria-invalid', 'true')
        self.page.get_by_label('E-mail', exact=True).fill('invalid')
        self.page.get_by_label('Senha', exact=True).fill('literal-password')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        self.assertEqual(len(requests), 0)
        self.page.get_by_label('E-mail', exact=True).fill('conta@example.com')
        expect(self.page.locator('#email-error')).to_be_hidden()

    def test_confirmation_and_password_length_block_registration(self):
        requests = []
        self.page.route('**/auth/register', lambda route: requests.append(route))
        self.open_registration()
        self.fill_registration()
        self.page.get_by_label('Crie uma senha', exact=True).fill('curta')
        self.page.get_by_role('button', name='Cadastrar', exact=True).click()
        expect(self.page.locator('#register-password-error')).to_be_visible()
        self.page.get_by_label('Crie uma senha', exact=True).fill('  senha-nova-12345  ')
        self.page.get_by_label('Confirme sua senha', exact=True).fill('senha-nova-12345')
        self.page.get_by_role('button', name='Cadastrar', exact=True).click()
        expect(self.page.locator('#register-confirm-error')).to_be_visible()
        self.assertEqual(len(requests), 0)

    def test_mobile_submit_focuses_invalid_password_on_first_click(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open_registration()
        self.page.get_by_label('Nome', exact=True).fill('Pessoa nova')
        self.page.get_by_label('E-mail de cadastro', exact=True).fill('nova@example.com')
        self.page.get_by_label('Crie uma senha', exact=True).fill('curta')
        self.page.get_by_label('Confirme sua senha', exact=True).fill('diferente')
        self.page.get_by_role('button', name='Cadastrar', exact=True).click()
        expect(self.page.get_by_label('Crie uma senha', exact=True)).to_be_focused()
        expect(self.page.locator('#register-message')).to_be_visible()

    def test_registration_rejects_email_without_domain_suffix(self):
        requests = []
        self.page.route('**/auth/register', lambda route: requests.append(route))
        self.open_registration()
        self.fill_registration()
        self.page.get_by_label('E-mail de cadastro', exact=True).fill('ana@localhost')
        self.page.get_by_role('button', name='Cadastrar', exact=True).click()
        expect(self.page.locator('#register-email-error')).to_be_visible()
        expect(self.page.get_by_label('E-mail de cadastro', exact=True)).to_be_focused()
        self.assertEqual(len(requests), 0)

    def test_registration_sends_literal_password_and_clears_secrets(self):
        self.open_registration()
        self.fill_registration()
        pending = []
        self.page.route('**/auth/register', lambda route: pending.append(route))
        with self.page.expect_request('**/auth/register') as sent:
            self.page.get_by_role('button', name='Cadastrar', exact=True).click()
        self.assertEqual(sent.value.post_data_json, {
            'display_name': 'Pessoa nova', 'email': 'nova@example.com',
            'password': '  senha-nova-12345  '})
        expect(self.page.get_by_role('button', name='Cadastrando…', exact=True)).to_be_disabled()
        pending[0].fulfill(status=202, json={'message': 'Try signing in.'})
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        self.assertEqual(self.page.get_by_label('E-mail', exact=True).input_value(), 'nova@example.com')
        self.assertEqual(self.page.locator('#register-password').input_value(), '')
        self.assertEqual(self.page.locator('#register-confirm').input_value(), '')
        self.assertEqual(self.page.evaluate('sessionStorage.length'), 0)

    def test_access_probe_checks_api_before_showing_blocked_state(self):
        pending = []
        self.page.route('**/auth/me', lambda route: pending.append(route))
        button = self.page.get_by_role('button', name='Verificar acesso', exact=True)
        self.assertEqual(button.count(), 1, 'The demo must allow an anonymous access check')
        with self.page.expect_request('**/auth/me') as sent:
            button.click()
        self.assertNotIn('authorization', sent.value.headers)
        expect(self.page.locator('#access-result')).to_contain_text('Verificando')
        pending[0].fulfill(status=401, json={'detail': 'Invalid authentication credentials'})
        expect(self.page.locator('#access-result')).to_contain_text('Acesso bloqueado')

    def test_access_probe_network_failure_is_not_denial(self):
        self.page.route('**/auth/me', lambda route: route.abort('connectionrefused'))
        button = self.page.get_by_role('button', name='Verificar acesso', exact=True)
        self.assertEqual(button.count(), 1, 'Users must be able to request an access check')
        button.click()
        expect(self.page.locator('#access-result')).to_contain_text('Não foi possível verificar')
        expect(self.page.locator('#access-result')).not_to_contain_text('Acesso bloqueado')
