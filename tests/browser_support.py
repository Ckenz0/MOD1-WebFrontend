import functools
import json
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Error, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class StaticHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.js': 'text/javascript'}

    def do_GET(self):
        if self.path.split('?')[0] == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        elif self.path.split('?')[0] == '/__test__/':
            body = b'<!doctype html><title>Module tests</title>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(body)
        elif self.path.split('?')[0] == '/config.js' and self.server.api_url:
            body = ('export const API_BASE_URL = ' + json.dumps(self.server.api_url) + ';\n'
                    + 'export const PROJECTS_API_BASE_URL = '
                    + json.dumps(self.server.projects_api_url or 'http://127.0.0.1:8001') + ';').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript')
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def log_message(self, *args):
        pass


class BrowserCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
            StaticHandler, directory=str(ROOT / 'public')))
        cls.server.api_url = None
        cls.server.projects_api_url = None
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(channel='msedge', headless=True)
        except BaseException:
            cls.playwright.stop()
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(locale='pt-BR', color_scheme='light')
        self.page = self.context.new_page()
        self.page.set_default_timeout(4000)
        self.addCleanup(self.context.close)
        self.token_response = {'access_token': 'synthetic-token', 'token_type': 'bearer',
                               'expires_in': 1800}
        self.identity = {'id': '11111111-1111-4111-8111-111111111111',
                         'email': 'conta@example.com', 'display_name': 'Conta de teste',
                         'is_active': True, 'created_at': '2026-10-10T12:00:00Z'}

    def evaluate(self, script, arg=None):
        try:
            return self.page.evaluate(script, arg)
        except Error as exc:
            self.fail('JavaScript product behavior failed: ' + str(exc))

    def mock_auth(self, identity=None, token=None):
        self.page.route('**/auth/token', lambda route: route.fulfill(
            json=token or self.token_response))
        self.page.route('**/auth/me', lambda route: route.fulfill(json=identity or self.identity))

    def login(self):
        self.page.get_by_label('E-mail', exact=True).fill('conta@example.com')
        self.page.get_by_label('Senha', exact=True).fill('  password12345  ')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
