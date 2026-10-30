"""User story acceptance with browser, all three real APIs and temporary data."""

import os
from pathlib import Path

from playwright.sync_api import expect

import test_backlog_real_api as backlog_real


class ManagementRealApiTests(backlog_real.BacklogRealApiTests):
    test_registration_project_stories_progress_restart_and_access_isolation = None

    def capture_management(self, surface):
        if not (capture := os.environ.get('CAPTURE_MANAGEMENT_EVIDENCE')):
            return
        target = Path(capture).resolve()
        target.mkdir(parents=True, exist_ok=True)
        for width, height, theme, device in [(1366, 900, 'light', 'desktop'), (390, 844, 'dark', 'mobile')]:
            self.page.set_viewport_size({'width': width, 'height': height})
            self.page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;scrollTo(0,0)}', theme)
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            self.page.screenshot(path=str(target / (surface + '-' + device + '.png')), full_page=True, animations='disabled')
        self.page.set_viewport_size({'width': 1366, 'height': 900})
        self.page.evaluate("document.documentElement.dataset.theme='light'")

    def test_edit_search_filter_and_change_password_with_real_apis(self):
        self.register('management@example.com')
        self.page.goto(self.base_url)
        self.sign_in('management@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_label('Nome do projeto', exact=True).fill('Atendimento')
        self.page.get_by_label('Objetivo do projeto', exact=True).fill('Reduzir tempo de resposta')
        self.page.get_by_role('button', name='Criar projeto', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('Projeto criado')
        self.page.get_by_role('button', name='Editar projeto', exact=True).click()
        self.page.get_by_label('Nome do projeto para edição', exact=True).fill('Portal de atendimento')
        self.page.get_by_label('Descrição do projeto para edição', exact=True).fill('<b>Conteúdo literal</b>\nContexto da equipe')
        self.page.get_by_label('Objetivo do projeto para edição', exact=True).fill('Entregar respostas rastreáveis')
        self.capture_management('project')
        self.page.get_by_role('button', name='Salvar projeto', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('Projeto atualizado')
        expect(self.page.locator('#project-detail-objective')).to_have_text('Entregar respostas rastreáveis')
        self.page.get_by_label('Buscar projetos pelo nome', exact=True).fill('PORTAL')
        self.page.get_by_role('button', name='Buscar projetos', exact=True).click()
        self.page.get_by_role('button', name='Portal de atendimento', exact=True).click()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        self.page.get_by_label('Título da história', exact=True).fill('Consultar uma solicitação')
        self.page.get_by_label('Descrição da história', exact=True).fill('Como cliente, quero acompanhar o atendimento.')
        self.page.get_by_role('button', name='Criar história', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('História criada')
        self.page.get_by_label('Editar título da história', exact=True).fill('Acompanhar minhas solicitações')
        self.page.get_by_label('Editar descrição da história', exact=True).fill('Consultar protocolo e situação atual.')
        self.page.get_by_label('Editar critérios de aceite', exact=True).fill('Listar somente protocolos da minha conta.')
        self.page.get_by_label('Prioridade da história', exact=True).select_option('high')
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('Alterações salvas')
        self.page.get_by_label('Buscar histórias', exact=True).fill('protocolo')
        self.page.get_by_label('Filtrar por status', exact=True).select_option('done')
        self.page.get_by_label('Filtrar por prioridade', exact=True).select_option('high')
        self.page.get_by_role('button', name='Aplicar filtros', exact=True).click()
        expect(self.page.locator('#backlog-list')).to_contain_text('Acompanhar minhas solicitações')
        expect(self.page.locator('#backlog-list')).to_contain_text('Alta · Concluído')

        self.stop(self.backlog_process)
        self.backlog_process = self.start(self.backlog_python, self.backlog_root, self.backlog_env,
            'backlog_service.app:create_app', self.backlog_port)
        self.page.get_by_role('button', name='Atualizar histórias', exact=True).click()
        self.page.get_by_role('button', name='Acompanhar minhas solicitações', exact=True).click()
        expect(self.page.get_by_label('Editar critérios de aceite', exact=True)).to_have_value('Listar somente protocolos da minha conta.')

        if capture := os.environ.get('CAPTURE_MANAGEMENT_EVIDENCE'):
            target = Path(capture).resolve()
            target.mkdir(parents=True, exist_ok=True)
            for width, height, theme, filename in [(1366, 900, 'light', 'desktop.png'), (390, 844, 'dark', 'mobile.png')]:
                self.page.set_viewport_size({'width': width, 'height': height})
                self.page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;scrollTo(0,0)}', theme)
                expect(self.page.locator('#story-detail')).to_be_visible()
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                self.page.screenshot(path=str(target / filename), full_page=True, animations='disabled')

        self.page.get_by_role('button', name='Voltar para projetos', exact=True).click()
        self.page.get_by_role('button', name='Voltar para minha conta', exact=True).click()
        self.page.get_by_role('button', name='Alterar senha', exact=True).click()
        self.page.get_by_label('Senha atual', exact=True).fill('ProjetoMvp!2026')
        self.page.get_by_label('Nova senha', exact=True).fill('Uma-nova-senha!2026')
        self.page.get_by_label('Confirme a nova senha', exact=True).fill('Uma-nova-senha!2026')
        self.capture_management('password')
        self.page.get_by_role('button', name='Salvar nova senha', exact=True).click()
        expect(self.page.locator('#login-message')).to_contain_text('Senha alterada')
        self.page.get_by_label('E-mail', exact=True).fill('management@example.com')
        self.page.get_by_label('Senha', exact=True).fill('ProjetoMvp!2026')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.locator('#login-message')).to_contain_text('E-mail ou senha inválidos')
        self.page.get_by_label('Senha', exact=True).fill('Uma-nova-senha!2026')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.locator('#profile-view')).to_be_visible()
