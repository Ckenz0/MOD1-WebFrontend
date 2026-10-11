import json
import os
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import expect

from browser_support import BrowserCase

SEED = '''
from mod1_auth.config import Settings
from mod1_auth.database import create_engine_for_url, create_session_factory, initialize_database
from mod1_auth.repositories import UserRepository
from mod1_auth.security import generate_private_key
from mod1_auth.services import UserService
s = Settings(_env_file=None)
generate_private_key(s.jwt_private_key_path)
engine = create_engine_for_url(s.database_url.get_secret_value())
initialize_database(engine)
with create_session_factory(engine)() as session:
    UserService(UserRepository(session)).create_user(email='conta@example.com', display_name='Conta de teste', password='  password12345  ')
engine.dispose()
'''

DEACTIVATE = '''
from mod1_auth.config import Settings
from mod1_auth.database import create_engine_for_url, create_session_factory
from mod1_auth.repositories import UserRepository
s = Settings(_env_file=None)
engine = create_engine_for_url(s.database_url.get_secret_value())
with create_session_factory(engine)() as session:
    users = UserRepository(session)
    users.set_active(users.get_by_email('conta@example.com').id, False)
engine.dispose()
'''


@unittest.skipUnless(os.environ.get('AUTH_BACKEND_PATH'),
                     'AUTH_BACKEND_PATH absent: real API integration not verified')
class RealApiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.backend = Path(os.environ['AUTH_BACKEND_PATH']).resolve()
        python = self.backend / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        self.assertTrue(python.is_file(), 'Prepare the backend virtual environment first')
        self.python = str(python)
        self.temp = tempfile.TemporaryDirectory(prefix='mod1-ui-integration-')
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.env = dict(os.environ, DATABASE_URL=f"sqlite:///{(root / 'users.db').as_posix()}",
                        DATABASE_SCHEMA='mod1_identity', JWT_PRIVATE_KEY_PATH=str(root / 'key.pem'),
                        JWT_ISSUER='frontend-integration', JWT_AUDIENCE='engenharia-software-api',
                        ACCESS_TOKEN_EXPIRE_MINUTES='30', CORS_ORIGINS=json.dumps([self.base_url]))
        self.flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        self.run_admin(SEED)
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            self.port = reserved.getsockname()[1]
        self.server.api_url = f'http://127.0.0.1:{self.port}'
        self.process = None
        self.addCleanup(self.stop_backend)
        self.addCleanup(lambda: setattr(self.server, 'api_url', None))
        self.start_backend()

    def run_admin(self, script):
        result = subprocess.run([self.python, '-c', script], cwd=self.backend, env=self.env,
                                capture_output=True, text=True, timeout=30, creationflags=self.flags)
        self.assertEqual(result.returncode, 0, 'Synthetic backend fixture failed: ' + result.stderr)

    def start_backend(self):
        self.stop_backend()
        self.process = subprocess.Popen([
            self.python, '-m', 'uvicorn', 'mod1_auth.main:create_app', '--factory',
            '--host', '127.0.0.1', '--port', str(self.port), '--log-level', 'error', '--no-access-log'],
            cwd=self.backend, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=self.flags)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            self.assertIsNone(self.process.poll(), 'Synthetic API exited before readiness')
            try:
                with urlopen(self.server.api_url + '/health/ready', timeout=0.5) as response:
                    if response.status == 200:
                        return
            except (URLError, TimeoutError):
                time.sleep(0.1)
        self.fail('Synthetic API readiness timed out')

    def stop_backend(self):
        if self.process is not None:
            # Windows virtualenv launchers can have a child interpreter holding SQLite.
            # End only the process tree this fixture launched, before removing its files.
            if os.name == 'nt' and self.process.poll() is None:
                subprocess.run(['taskkill', '/PID', str(self.process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=10, creationflags=self.flags, check=True)
            elif self.process.poll() is None:
                self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
            self.process = None

    def test_real_login_identity_update_and_logout(self):
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        with self.page.expect_response('**/auth/me') as refreshed:
            self.page.get_by_role('button', name='Atualizar dados', exact=True).click()
        self.assertEqual(refreshed.value.status, 200)
        self.assertEqual(refreshed.value.headers['access-control-allow-origin'], self.base_url)
        self.page.get_by_role('button', name='Sair', exact=True).click()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        self.page.get_by_label('Senha', exact=True).fill('wrong-password')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.get_by_role('alert')).to_contain_text('E-mail ou senha inválidos')

    def test_public_registration_and_access_check_before_login_and_after_logout(self):
        self.page.goto(self.base_url)
        opener = self.page.get_by_role('button', name='Criar conta', exact=True)
        self.assertEqual(opener.count(), 1, 'Public registration must be available')
        self.page.get_by_role('button', name='Verificar acesso', exact=True).click()
        expect(self.page.locator('#access-result')).to_contain_text('Acesso bloqueado')
        opener.click()
        self.page.get_by_label('Nome', exact=True).fill('Pessoa nova')
        self.page.get_by_label('E-mail de cadastro', exact=True).fill('nova@example.com')
        self.page.get_by_label('Crie uma senha', exact=True).fill('  senha-nova-12345  ')
        self.page.get_by_label('Confirme sua senha', exact=True).fill('  senha-nova-12345  ')
        with self.page.expect_response('**/auth/register') as registered:
            self.page.get_by_role('button', name='Cadastrar', exact=True).click()
        self.assertEqual(registered.value.status, 202)
        self.page.get_by_label('Senha', exact=True).fill('  senha-nova-12345  ')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.get_by_text('nova@example.com', exact=True)).to_be_visible()
        self.page.get_by_role('button', name='Verificar acesso', exact=True).click()
        expect(self.page.locator('#access-result')).to_contain_text('Acesso permitido')
        self.page.get_by_role('button', name='Sair', exact=True).click()
        self.page.get_by_role('button', name='Verificar acesso', exact=True).click()
        expect(self.page.locator('#access-result')).to_contain_text('Acesso bloqueado')

    def test_disallowed_origin_cannot_complete_login(self):
        self.env['CORS_ORIGINS'] = '[]'
        self.start_backend()
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_role('alert')).to_contain_text('conectar')
        expect(self.page.get_by_role('button', name='Sair', exact=True)).to_be_hidden()

    def test_real_inactive_user_rejected(self):
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.get_by_text('conta@example.com', exact=True)).to_be_visible()
        self.run_admin(DEACTIVATE)
        self.page.get_by_role('button', name='Atualizar dados', exact=True).click()
        expect(self.page.get_by_role('button', name='Entrar', exact=True)).to_be_visible()
        self.login()
        expect(self.page.get_by_role('alert')).to_contain_text('E-mail ou senha inválidos')
