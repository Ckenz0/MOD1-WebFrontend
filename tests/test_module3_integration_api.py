"""Actual browser -> two isolated M1 APIs -> read-only loopback artifact provider."""
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect

import test_projects_real_api as real


class ArtifactProvider(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.calls.append((self.command, self.path, self.headers.get('Authorization')))
        paths = {
            '/projects/': [{'id': 7, 'name': 'Documentação do projeto', 'description': None}],
            '/projects/7/artifacts/': [{'id': 41, 'project_id': 7, 'name': 'Requisitos.md',
                'artifact_type': 'MARKDOWN', 'version': 1, 'created_at': '2026-11-24T00:00:00Z',
                'file_path': '/private/internal/file.md'}],
            '/projects/7/artifacts/41/versions': [{'id': 81, 'artifact_id': 41,
                'version_number': 1, 'created_at': '2026-11-24T00:00:00Z', 'file_path': '/private/file.md'}],
            '/projects/7/artifacts/41/download': b'# Requisitos\n',
        }
        value = paths.get(urlsplit(self.path).path)
        self.send_response(200 if value is not None else 404)
        self.send_header('Content-Type', 'application/octet-stream' if isinstance(value, bytes) else 'application/json')
        self.end_headers()
        self.wfile.write(value if isinstance(value, bytes) else json.dumps(value).encode())


@unittest.skipUnless(os.environ.get('AUTH_BACKEND_PATH') and os.environ.get('PROJECTS_BACKEND_PATH'),
                     'Set two backend paths for isolated Module 3 browser acceptance')
class Module3IntegrationApiTests(real.ProjectsRealApiTests):
    test_register_login_create_restart_and_second_account_denied = None

    # Use the current permitted interpreter with each fixture's own dependencies.
    def admin(self, python, cwd, env, script):
        return super().admin(sys.executable, cwd, env, script)

    def start(self, python, cwd, env, factory, port):
        return super().start(sys.executable, cwd, env, factory, port)

    def package_path(self, key):
        root = Path(os.environ[key])
        site = root / '.venv' / ('Lib/site-packages' if os.name == 'nt' else 'lib/python3.12/site-packages')
        return os.pathsep.join([str(root / 'src'), str(site)])

    def additional_auth_settings(self):
        return {'MAIL_PROVIDER': 'disabled', 'LOCAL_MAILBOX_ENABLED': 'false',
                'PYTHONPATH': self.package_path('AUTH_BACKEND_PATH'),
                'AI_PROVIDER': 'structured-http', 'AI_BASE_URL': 'http://127.0.0.1:9'}

    def additional_projects_settings(self):
        self.provider = ThreadingHTTPServer(('127.0.0.1', 0), ArtifactProvider)
        self.provider.calls = []
        thread = threading.Thread(target=self.provider.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (self.provider.shutdown(), self.provider.server_close(), thread.join()))
        return {'MODULE3_ENABLED': 'true', 'MODULE3_BASE_URL': f'http://127.0.0.1:{self.provider.server_port}',
                'MODULE5_ENABLED': 'false', 'MODULE6_ENABLED': 'false',
                'PYTHONPATH': self.package_path('PROJECTS_BACKEND_PATH'),
                'AI_PROVIDER': 'structured-http', 'AI_BASE_URL': 'http://127.0.0.1:9'}

    def test_artifacts_link_versions_download_isolation_and_responsive_ui(self):
        self.page.set_default_timeout(10000)
        self.context.route('**/*', lambda route: route.continue_()
            if urlsplit(route.request.url).hostname == '127.0.0.1' else route.abort())
        self.register('artefatos@example.com')
        login = self.context.request.post(self.auth_url + '/auth/token', form={
            'username': 'artefatos@example.com', 'password': 'ProjetoMvp!2026'})
        self.assertEqual(login.status, 200)
        headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
        created = self.context.request.post(self.projects_url + '/projects', headers=headers,
            data={'name': 'Artefatos de um projeto de estudo'})
        self.assertEqual(created.status, 201)
        project_url = self.projects_url + '/projects/' + created.json()['id']
        self.page.goto(self.base_url)
        self.sign_in('artefatos@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Artefatos de um projeto de estudo', exact=True).click()
        self.page.get_by_role('button', name='Gerenciar projeto e planejamento', exact=True).click()
        self.page.get_by_role('button', name='Artefatos', exact=True).click()
        expect(self.page.get_by_text('Nenhum projeto do Módulo 3 vinculado.', exact=True)).to_be_visible()
        self.assertEqual(self.provider.calls, [])
        self.page.get_by_role('button', name='Escolher projeto', exact=True).click()
        self.page.get_by_label('Projeto do Módulo 3', exact=True).select_option('7')
        self.page.get_by_role('button', name='Vincular projeto', exact=True).click()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_be_visible()
        persisted = self.context.request.get(project_url, headers=headers)
        self.assertEqual(persisted.json()['module3_project_id'], 7)
        self.page.get_by_role('button', name='Versões', exact=True).click()
        expect(self.page.get_by_text('Versão 1', exact=False)).to_be_visible()
        with self.page.expect_download() as event:
            self.page.get_by_role('button', name='Baixar versão atual', exact=True).click()
        download = event.value
        self.assertEqual(download.suggested_filename, 'artifact-41.md')
        self.assertEqual(Path(download.path()).read_bytes(), b'# Requisitos\n')
        self.assertTrue(all(method == 'GET' and token is None for method, _, token in self.provider.calls))
        self.assertNotIn('/private/', self.page.locator('#workspace-content').inner_text())
        expect(self.page.get_by_role('button', name='Baixar versão atual', exact=True)).to_be_enabled()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')
        for width, theme in [(1366, 'light'), (390, 'dark')]:
            self.page.set_viewport_size({'width': width, 'height': 900})
            self.page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;}', theme)
            self.assertTrue(self.page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'))
            expect(self.page.get_by_role('button', name='Baixar versão atual', exact=True)).to_be_visible()
            capture = os.environ.get('CAPTURE_MODULE3_EVIDENCE')
            if capture:
                directory = Path(capture); directory.mkdir(parents=True, exist_ok=True)
                self.page.screenshot(path=str(directory / f'module3-{width}-{theme}.png'), full_page=True)
        self.register('outro-artefatos@example.com')
        other = self.context.request.post(self.auth_url + '/auth/token', form={
            'username': 'outro-artefatos@example.com', 'password': 'ProjetoMvp!2026'})
        before = len(self.provider.calls)
        denied = self.context.request.get(project_url + '/artifacts',
            headers={'Authorization': 'Bearer ' + other.json()['access_token']})
        self.assertEqual(denied.status, 404)
        self.assertEqual(len(self.provider.calls), before)
