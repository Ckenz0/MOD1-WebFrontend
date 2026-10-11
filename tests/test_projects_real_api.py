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
from test_real_api import SEED


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


@unittest.skipUnless(os.environ.get('AUTH_BACKEND_PATH') and os.environ.get('PROJECTS_BACKEND_PATH'),
                     'Set both backend paths to verify real projects integration')
class ProjectsRealApiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory(prefix='projects-real-integration-')
        self.addCleanup(self.cleanup_temp)
        root = Path(self.temp.name)
        self.flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        self.auth_root = Path(os.environ['AUTH_BACKEND_PATH']).resolve()
        self.projects_root = Path(os.environ['PROJECTS_BACKEND_PATH']).resolve()
        executable = 'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
        self.auth_python = str(self.auth_root / '.venv' / executable)
        self.projects_python = str(self.projects_root / '.venv' / executable)
        self.auth_port, self.projects_port = free_port(), free_port()
        self.auth_url = f'http://127.0.0.1:{self.auth_port}'
        self.projects_url = f'http://127.0.0.1:{self.projects_port}'
        self.auth_env = dict(os.environ, DATABASE_URL=f"sqlite:///{(root/'users.db').as_posix()}",
            DATABASE_SCHEMA='mod1_identity', JWT_PRIVATE_KEY_PATH=str(root/'key.pem'),
            JWT_ISSUER='mod1-auth-local', JWT_AUDIENCE='engenharia-software-api',
            CORS_ORIGINS=json.dumps([self.base_url]))
        self.projects_env = dict(os.environ,
            DATABASE_URL=f"sqlite:///{(root/'projects.db').as_posix()}", DATABASE_SCHEMA='projects',
            JWT_ISSUER='mod1-auth-local', JWT_AUDIENCE='engenharia-software-api',
            JWKS_URL=self.auth_url+'/.well-known/jwks.json', CORS_ORIGINS=json.dumps([self.base_url]))
        self.auth_process = self.projects_process = None
        self.addCleanup(lambda: self.stop(self.auth_process))
        self.addCleanup(lambda: self.stop(self.projects_process))
        self.addCleanup(lambda: setattr(self.server, 'api_url', None))
        self.addCleanup(lambda: setattr(self.server, 'projects_api_url', None))
        self.admin(self.auth_python, self.auth_root, self.auth_env, SEED)
        self.admin(self.projects_python, self.projects_root, self.projects_env,
            'from projects_service.cli import main; raise SystemExit(main(["init"]))')
        self.auth_process = self.start(self.auth_python, self.auth_root, self.auth_env,
                                       'mod1_auth.main:create_app', self.auth_port)
        self.projects_process = self.start(self.projects_python, self.projects_root, self.projects_env,
                                           'projects_service.app:create_app', self.projects_port)
        self.server.api_url = self.auth_url
        self.server.projects_api_url = self.projects_url

    def admin(self, python, cwd, env, script):
        result = subprocess.run([python, '-c', script], cwd=cwd, env=env, capture_output=True,
                                timeout=30, creationflags=self.flags)
        self.assertEqual(result.returncode, 0, 'Synthetic database/key initialization failed')

    def cleanup_temp(self):
        # Windows can release a killed interpreter's SQLite handles after its launcher exits.
        # Retry only this fixture's temporary directory, after both owned process trees stop.
        deadline = time.monotonic() + 5
        while True:
            try:
                self.temp.cleanup()
                return
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)

    def start(self, python, cwd, env, factory, port):
        process = subprocess.Popen([python, '-m', 'uvicorn', factory, '--factory', '--host',
            '127.0.0.1', '--port', str(port), '--log-level', 'error', '--no-access-log'],
            cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=self.flags)
        deadline = time.monotonic()+15
        try:
            while time.monotonic() < deadline:
                self.assertIsNone(process.poll(), 'Synthetic service exited')
                try:
                    with urlopen(f'http://127.0.0.1:{port}/health/ready', timeout=0.5) as response:
                        if response.status == 200:
                            return process
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            self.fail('Synthetic service readiness timed out')
        except BaseException:
            self.stop(process)
            raise

    def stop(self, process):
        if process is None or process.poll() is not None:
            return
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=10, creationflags=self.flags, check=True)
        else:
            process.terminate()
        process.wait(timeout=10)

    def register(self, email):
        result = self.context.request.post(self.auth_url+'/auth/register', data={
            'display_name': 'Pessoa de projetos', 'email': email, 'password': 'ProjetoMvp!2026'})
        self.assertEqual(result.status, 202)

    def sign_in(self, email):
        self.page.get_by_label('E-mail', exact=True).fill(email)
        self.page.get_by_label('Senha', exact=True).fill('ProjetoMvp!2026')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def test_register_login_create_restart_and_second_account_denied(self):
        self.register('projetos-a@example.com')
        self.page.goto(self.base_url)
        self.sign_in('projetos-a@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_label('Nome do projeto', exact=True).fill('Projeto persistente')
        self.page.get_by_label('Descrição', exact=True).fill('Minha primeira entrega')
        with self.page.expect_response(lambda r: '/projects' in r.url and r.request.method == 'POST') as created:
            self.page.get_by_role('button', name='Criar projeto', exact=True).click()
        self.assertEqual(created.value.status, 201)
        project = created.value.json()
        expect(self.page.locator('#project-detail')).to_contain_text('Minha primeira entrega')
        self.assertEqual(created.value.headers['access-control-allow-origin'], self.base_url)
        self.stop(self.projects_process)
        self.projects_process = self.start(self.projects_python, self.projects_root, self.projects_env,
            'projects_service.app:create_app', self.projects_port)
        self.page.reload()
        self.sign_in('projetos-a@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto persistente', exact=True).click()
        expect(self.page.locator('#project-detail')).to_contain_text('Minha primeira entrega')
        self.page.locator('#projects-logout').click()
        self.register('projetos-b@example.com')
        self.sign_in('projetos-b@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        expect(self.page.locator('#projects-list')).to_contain_text('Você ainda não tem projetos')
        token_b = self.context.request.post(self.auth_url+'/auth/token', form={
            'username':'projetos-b@example.com', 'password':'ProjetoMvp!2026'}).json()['access_token']
        forbidden = self.context.request.get(self.projects_url+'/projects/'+project['id'],
                                            headers={'Authorization': 'Bearer '+token_b})
        self.assertEqual(forbidden.status, 404)
        self.assertEqual(self.context.request.get(self.projects_url+'/projects').status, 401)
