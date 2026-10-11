import os
import unittest
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect

import test_projects_real_api as projects_real


@unittest.skipUnless(all(os.environ.get(k) for k in ('AUTH_BACKEND_PATH', 'PROJECTS_BACKEND_PATH', 'BACKLOG_BACKEND_PATH')),
                     'Set all three backend paths to verify real backlog integration')
class BacklogRealApiTests(projects_real.ProjectsRealApiTests):
    # Reuse the isolated-service fixture, without running its unrelated test twice.
    test_register_login_create_restart_and_second_account_denied = None

    def setUp(self):
        super().setUp()
        self.backlog_root = Path(os.environ['BACKLOG_BACKEND_PATH']).resolve()
        executable = 'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
        self.backlog_python = str(self.backlog_root / '.venv' / executable)
        self.backlog_port = projects_real.free_port()
        self.backlog_url = f'http://127.0.0.1:{self.backlog_port}'
        self.backlog_env = dict(self.projects_env, DATABASE_SCHEMA='backlog',
            DATABASE_URL=f"sqlite:///{(Path(self.temp.name)/'backlog.db').as_posix()}",
            PROJECTS_API_BASE_URL=self.projects_url)
        self.backlog_process = None
        self.addCleanup(lambda: self.stop(self.backlog_process))
        self.addCleanup(lambda: setattr(self.server, 'backlog_api_url', None))
        self.admin(self.backlog_python, self.backlog_root, self.backlog_env,
            'from backlog_service.cli import main; raise SystemExit(main(["init"]))')
        self.backlog_process = self.start(self.backlog_python, self.backlog_root, self.backlog_env,
            'backlog_service.app:create_app', self.backlog_port)
        self.server.backlog_api_url = self.backlog_url

    def test_registration_project_stories_progress_restart_and_access_isolation(self):
        self.page.goto(self.base_url)
        self.page.get_by_role('button', name='Criar conta', exact=True).click()
        self.page.get_by_label('Nome', exact=True).fill('Pessoa do backlog')
        self.page.get_by_label('E-mail de cadastro', exact=True).fill('backlog-a@example.com')
        self.page.get_by_label('Crie uma senha', exact=True).fill('ProjetoMvp!2026')
        self.page.get_by_label('Confirme sua senha', exact=True).fill('ProjetoMvp!2026')
        self.page.get_by_role('button', name='Cadastrar', exact=True).click()
        expect(self.page.locator('#login-message')).to_contain_text('Cadastro recebido')
        self.sign_in('backlog-a@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_label('Nome do projeto', exact=True).fill('Portal de atendimento')
        with self.page.expect_response(lambda r: r.request.method == 'POST' and r.url == self.projects_url+'/projects') as created:
            self.page.get_by_role('button', name='Criar projeto', exact=True).click()
        project = created.value.json()
        expect(self.page.locator('#projects-status')).to_contain_text('Projeto criado')
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        expect(self.page.get_by_role('button', name='Criar história', exact=True)).to_be_enabled()
        self.page.get_by_label('Título da história', exact=True).fill('Consultar minhas solicitações')
        self.page.get_by_label('Descrição da história', exact=True).fill('Como usuário, quero ver minhas solicitações\npara acompanhar o atendimento.')
        self.page.get_by_label('Critérios de aceite', exact=True).fill('Listar apenas as solicitações da minha conta.\nExibir o estado atual de cada solicitação.')
        with self.page.expect_response(lambda r: r.request.method == 'POST' and '/stories' in r.url) as created_story:
            self.page.get_by_role('button', name='Criar história', exact=True).click()
        story = created_story.value.json()
        self.assertEqual(created_story.value.status, 201)
        expect(self.page.locator('#backlog-status')).to_contain_text('História criada')
        self.page.get_by_label('Título da história', exact=True).fill('Receber uma atualização por e-mail')
        self.page.get_by_label('Prioridade', exact=True).select_option('low')
        self.page.get_by_role('button', name='Criar história', exact=True).click()
        expect(self.page.locator('#backlog-count')).to_contain_text('2 histórias')
        self.page.get_by_role('button', name='Consultar minhas solicitações', exact=True).click()
        self.page.get_by_label('Prioridade da história', exact=True).select_option('high')
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('Alterações salvas')
        expect(self.page.locator('#backlog-list li').first).to_contain_text('Consultar minhas solicitações')
        expect(self.page.locator('#backlog-list li').first).to_contain_text('Alta · Concluído')
        capture = os.environ.get('CAPTURE_BACKLOG_EVIDENCE')
        if capture:
            directory = Path(capture).resolve()
            directory.mkdir(parents=True, exist_ok=True)
            for width, height, theme, filename in [(1366, 900, 'light', 'backlog-desktop-light.png'), (390, 844, 'dark', 'backlog-mobile-dark.png')]:
                self.page.set_viewport_size({'width': width, 'height': height})
                self.page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;scrollTo(0,0)}', theme)
                self.page.screenshot(path=str(directory/filename), full_page=True)
        self.stop(self.backlog_process)
        self.backlog_process = self.start(self.backlog_python, self.backlog_root, self.backlog_env,
            'backlog_service.app:create_app', self.backlog_port)
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        expect(self.page.locator('#backlog-list')).to_contain_text('Alta · Concluído')
        self.page.get_by_role('button', name='Consultar minhas solicitações', exact=True).click()
        expect(self.page.get_by_label('Status da história', exact=True)).to_have_value('done')
        self.page.locator('#backlog-logout').click()
        self.register('backlog-b@example.com')
        token_b = self.context.request.post(self.auth_url+'/auth/token', form={
            'username': 'backlog-b@example.com', 'password': 'ProjetoMvp!2026'}).json()['access_token']
        auth_b = {'Authorization': 'Bearer '+token_b}
        base = self.backlog_url+'/projects/'+project['id']+'/stories'
        for method, url, data in [('get', base, None), ('get', base+'/'+story['id'], None), ('post', base, {'title': 'B'}), ('patch', base+'/'+story['id'], {'status': 'todo'})]:
            response = getattr(self.context.request, method)(url, headers=auth_b, data=data)
            self.assertEqual(response.status, 404)
        other_project = self.context.request.post(self.projects_url+'/projects', headers=auth_b, data={'name': 'Projeto B'}).json()
        wrong = self.context.request.get(self.backlog_url+'/projects/'+other_project['id']+'/stories/'+story['id'], headers=auth_b)
        missing = self.context.request.get(base+'/'+str(uuid4()), headers=auth_b)
        self.assertEqual(wrong.status, 404)
        self.assertEqual(wrong.json(), missing.json())
        self.assertEqual(self.context.request.get(base).status, 401)
