"""Curation acceptance with three disposable APIs and a loopback Module 5."""

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect

import test_backlog_real_api as real


ARTICLE = {
    'titulo': 'Testes de contrato para APIs HTTP',
    'link': 'https://example.org/testes-de-contrato',
    'fonte': 'Engenharia de Software',
    'idioma': 'pt',
    'data_publicacao': '2026-11-18T12:00:00Z',
}
QUESTION = 'Como testar um contrato HTTP em uma aplicação de exemplo?'


class CurationProviderHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, payload):
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def record(self, body):
        self.server.calls.append({
            'method': self.command, 'path': self.path, 'body': body,
            'authorization': self.headers.get('Authorization'),
            'has_cookie': 'Cookie' in self.headers,
        })

    def do_GET(self):
        self.record(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        if self.server.feed_unavailable:
            self.reply(503, {'erro': 'Detalhe privado do provedor'})
        else:
            self.reply(200, {
                'artigos': [], 'total': 0, 'categoria': 'geral',
                'fontes_consultadas': ['Engenharia de Software'],
                'fontes_indisponiveis': ['Boletim semanal'],
            })

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        self.record(body)
        if self.server.query_mode == 'unavailable':
            self.reply(503, {'erro': 'Detalhe privado do provedor'})
        else:
            articles = [ARTICLE] if self.server.query_mode == 'success' else []
            self.reply(200, {'artigos': articles, 'chat_id': 'internal-provider-chat'})


@unittest.skipUnless(all(os.environ.get(key) for key in (
    'AUTH_BACKEND_PATH', 'PROJECTS_BACKEND_PATH', 'BACKLOG_BACKEND_PATH'
)), 'Set all three backend paths for isolated Module 5 browser acceptance')
class Module5IntegrationApiTests(real.BacklogRealApiTests):
    test_registration_project_stories_progress_restart_and_access_isolation = None

    def additional_auth_settings(self):
        return {'MAIL_PROVIDER': 'disabled', 'LOCAL_MAILBOX_ENABLED': 'false',
                'MODULE6_ENABLED': 'false', 'AI_PROVIDER': 'structured-http',
                'AI_BASE_URL': 'http://127.0.0.1:9'}

    def additional_projects_settings(self):
        self.provider = ThreadingHTTPServer(('127.0.0.1', 0), CurationProviderHandler)
        self.provider.calls = []
        self.provider.feed_unavailable = False
        self.provider.query_mode = 'success'
        self.provider_thread = threading.Thread(target=self.provider.serve_forever, daemon=True)
        self.provider_thread.start()
        self.addCleanup(self.stop_provider)
        return {'MODULE5_ENABLED': 'true',
                'MODULE5_BASE_URL': f'http://127.0.0.1:{self.provider.server_port}',
                'MODULE6_ENABLED': 'false', 'AI_PROVIDER': 'structured-http',
                'AI_BASE_URL': 'http://127.0.0.1:9'}

    def additional_backlog_settings(self):
        return {'MODULE4_ENABLED': 'false', 'MODULE6_ENABLED': 'false',
                'AI_PROVIDER': 'structured-http', 'AI_BASE_URL': 'http://127.0.0.1:9'}

    def stop_provider(self):
        self.provider.shutdown()
        self.provider.server_close()
        self.provider_thread.join()

    def setUp(self):
        super().setUp()
        self.page.set_default_timeout(10000)
        self.context.route('**/*', lambda route: route.continue_()
                           if urlsplit(route.request.url).hostname == '127.0.0.1' else route.abort())
        self.register('curadoria@example.com')
        sign_in = self.context.request.post(self.auth_url + '/auth/token', form={
            'username': 'curadoria@example.com', 'password': 'ProjetoMvp!2026'})
        self.assertEqual(sign_in.status, 200)
        self.headers = {'Authorization': 'Bearer ' + sign_in.json()['access_token']}
        created = self.context.request.post(self.projects_url + '/projects', headers=self.headers,
            data={'name': 'Curadoria de um projeto de estudo'})
        self.assertEqual(created.status, 201)
        self.project_url = self.projects_url + '/projects/' + created.json()['id']
        self.curation_url = self.project_url + '/curation'
        self.page.goto(self.base_url)
        self.sign_in('curadoria@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Curadoria de um projeto de estudo', exact=True).click()
        self.page.get_by_role('button', name='Gerenciar projeto e planejamento', exact=True).click()
        expect(self.page.get_by_role('heading', name='Contexto do projeto', exact=True)).to_be_visible()

    def open_feed(self, status=200):
        entry = self.page.get_by_role('button', name='Curadoria', exact=True)
        expect(entry).to_be_visible()
        with self.page.expect_response(lambda response: response.url == self.curation_url + '/feed') as response:
            entry.click()
        self.assertEqual(response.value.status, status)
        return response.value

    def submit_question(self, question, status=200):
        self.page.get_by_label('Pergunta sobre tecnologia', exact=True).fill(question)
        with self.page.expect_response(lambda response: response.url == self.curation_url + '/queries') as response:
            self.page.get_by_role('button', name='Buscar artigos', exact=True).click()
        self.assertEqual(response.value.status, status)
        return response.value

    def test_curation_routes_send_minimal_requests_without_modifying_project(self):
        before = self.context.request.get(self.project_url, headers=self.headers)
        self.assertEqual(before.status, 200)
        self.assertEqual(self.provider.calls, [])

        feed = self.open_feed()
        expect(self.page.get_by_text('Nenhum artigo disponível no feed.', exact=True)).to_be_visible()
        self.assertEqual(feed.json()['total'], 0)
        expect(self.page.get_by_text('Boletim semanal', exact=False)).to_be_visible()
        self.assertEqual(self.provider.calls, [
            {'method': 'GET', 'path': '/feed', 'body': b'', 'authorization': None, 'has_cookie': False},
        ])

        query = self.submit_question('  ' + QUESTION + '  ')
        result = query.json()
        self.assertEqual(result['artigos'], [ARTICLE])
        self.assertEqual(set(result), {'enabled', 'artigos', 'total', 'categoria',
                                      'fontes_consultadas', 'fontes_indisponiveis', 'truncated'})
        browser_auth = query.request.header_value('authorization')
        remote = self.provider.calls[1]
        self.assertTrue(bool(browser_auth and browser_auth.startswith('Bearer ')))
        self.assertTrue(browser_auth == remote['authorization'], 'Module 5 must receive the browser session bearer')
        self.assertFalse(remote['has_cookie'])
        self.assertEqual(remote['body'], {'pergunta': QUESTION})
        expect(self.page.get_by_role('link', name=ARTICLE['titulo'])).to_have_attribute('href', ARTICLE['link'])
        self.verify_layout()

        self.provider.query_mode = 'empty'
        self.submit_question('Exemplo de pesquisa sem resultados')
        expect(self.page.get_by_text('Nenhum artigo encontrado para esta pergunta.', exact=True)).to_be_visible()
        self.provider.query_mode = 'unavailable'
        self.submit_question('Exemplo de pesquisa indisponível', status=503)
        expect(self.page.get_by_text('A consulta pode ter sido registrada', exact=False)).to_be_visible()
        expect(self.page.get_by_text('Detalhe privado', exact=False)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Buscar artigos', exact=True)).to_be_enabled()

        self.page.get_by_role('button', name='Contexto', exact=True).click()
        self.provider.feed_unavailable = True
        self.open_feed(status=503)
        expect(self.page.get_by_text('O feed está indisponível no momento.', exact=True)).to_be_visible()
        self.assertEqual([(call['method'], call['path']) for call in self.provider.calls], [
            ('GET', '/feed'), ('POST', '/consultas'), ('POST', '/consultas'),
            ('POST', '/consultas'), ('GET', '/feed'),
        ])
        after = self.context.request.get(self.project_url, headers=self.headers)
        self.assertEqual(after.status, 200)
        self.assertEqual(after.json(), before.json())

    def verify_layout(self):
        capture = os.environ.get('CAPTURE_MODULE5_EVIDENCE')
        for width, theme in [(1366, 'light'), (390, 'dark')]:
            self.page.set_viewport_size({'width': width, 'height': 900})
            if theme == 'dark':
                self.page.get_by_role('button', name='Ativar tema escuro', exact=True).click()
            expect(self.page.get_by_label('Pergunta sobre tecnologia', exact=True)).to_be_editable()
            expect(self.page.get_by_role('button', name='Buscar artigos', exact=True)).to_be_enabled()
            expect(self.page.get_by_role('button', name='Contexto', exact=True)).to_be_enabled()
            self.assertTrue(self.page.evaluate('''() =>
                document.documentElement.scrollWidth === window.innerWidth &&
                Array.from(document.querySelectorAll('#workspace-view, #workspace-content form, #workspace-content ul'))
                  .every(node => node.scrollWidth <= node.clientWidth)
            '''), f'Curation overflows at {width}px')
            if capture:
                directory = Path(capture)
                directory.mkdir(parents=True, exist_ok=True)
                self.page.screenshot(path=str(directory / f'module5-{width}-{theme}.png'),
                                     full_page=True, animations='disabled')
