import os
from pathlib import Path

from playwright.sync_api import expect

import test_backlog_real_api as backlog_real


class CollaborationRealApiTests(backlog_real.BacklogRealApiTests):
    test_registration_project_stories_progress_restart_and_access_isolation = None

    def capture(self, surface):
        if not (directory := os.environ.get('CAPTURE_COLLABORATION_EVIDENCE')):
            return
        target = Path(directory).resolve()
        target.mkdir(parents=True, exist_ok=True)
        for width, height, theme, device in [(1366, 900, 'light', 'desktop'), (390, 844, 'dark', 'mobile')]:
            self.page.set_viewport_size({'width': width, 'height': height})
            self.page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;scrollTo(0,0)}', theme)
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            self.page.screenshot(path=str(target / (surface + '-' + device + '.png')), full_page=True, animations='disabled')
        self.page.set_viewport_size({'width': 1366, 'height': 900})
        self.page.evaluate("document.documentElement.dataset.theme='light'")

    def test_code_invitation_multiple_roles_and_revocation_with_real_apis(self):
        self.register('rbac-owner@example.com')
        self.register('rbac-member@example.com')
        token_b = self.context.request.post(self.auth_url + '/auth/token', form={
            'username': 'rbac-member@example.com', 'password': 'ProjetoMvp!2026'}).json()['access_token']
        auth_b = {'Authorization': 'Bearer ' + token_b}
        user_b = self.context.request.get(self.auth_url + '/auth/me', headers=auth_b).json()['id']

        self.page.goto(self.base_url)
        self.sign_in('rbac-owner@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_label('Nome do projeto', exact=True).fill('Projeto compartilhado')
        self.page.get_by_role('button', name='Criar projeto', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('Projeto criado')
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        self.page.get_by_label('Título da história', exact=True).fill('Entrega colaborativa')
        with self.page.expect_response(lambda r: r.request.method == 'POST' and '/stories' in r.url) as created:
            self.page.get_by_role('button', name='Criar história', exact=True).click()
        story = created.value.json()
        self.page.get_by_role('button', name='Voltar para projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto compartilhado', exact=True).click()
        self.page.get_by_role('button', name='Membros e papéis', exact=True).click()
        self.page.get_by_label('ID da conta convidada', exact=True).fill(user_b)
        self.page.get_by_role('button', name='Gerar código de convite', exact=True).click()
        expect(self.page.locator('#members-status')).to_contain_text('Convite criado')
        code = self.page.locator('#generated-invite-code').input_value()
        self.assertTrue(len(code) >= 43)
        self.page.locator('#projects-logout').click()

        self.sign_in('rbac-member@example.com')
        self.page.get_by_label('Código do convite', exact=True).fill(code)
        self.page.get_by_role('button', name='Aceitar convite', exact=True).click()
        expect(self.page.locator('#invitation-status')).to_contain_text('Convite aceito')
        self.page.get_by_role('button', name='Editar perfil profissional', exact=True).click()
        expect(self.page.locator('#profile-save')).to_be_enabled()
        self.page.get_by_label('Resumo profissional', exact=True).fill('Desenvolvimento de APIs e testes.')
        self.page.get_by_label('Senioridade', exact=True).select_option('mid')
        self.page.get_by_label('Disponibilidade semanal em horas', exact=True).fill('20')
        self.page.get_by_role('button', name='Adicionar competência', exact=True).click()
        self.page.get_by_label('Competência 1', exact=True).fill('Python')
        self.page.get_by_label('Domínio da competência 1', exact=True).select_option('4')
        self.page.get_by_role('button', name='Salvar perfil', exact=True).click()
        expect(self.page.locator('#professional-profile-status')).to_contain_text('Perfil atualizado')
        self.capture('profile')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto compartilhado', exact=True).click()
        expect(self.page.get_by_role('button', name='Editar projeto', exact=True)).to_be_hidden()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        expect(self.page.get_by_role('button', name='Criar história', exact=True)).to_be_hidden()
        self.page.get_by_role('button', name='Entrega colaborativa', exact=True).click()
        expect(self.page.locator('#story-update-title')).to_be_disabled()
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('Alterações salvas')
        self.capture('developer')
        base = self.backlog_url + '/projects/' + story['project_id'] + '/stories'
        self.assertEqual(self.context.request.post(base, headers=auth_b, data={'title': 'Forbidden'}).status, 403)
        self.assertEqual(self.context.request.patch(base + '/' + story['id'], headers=auth_b, data={'title': 'Forbidden'}).status, 403)
        self.page.locator('#backlog-logout').click()

        self.sign_in('rbac-owner@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto compartilhado', exact=True).click()
        self.page.get_by_role('button', name='Membros e papéis', exact=True).click()
        self.page.get_by_role('button', name='Editar acessos de ' + user_b, exact=True).click()
        self.page.locator('#member-role-product_owner').check()
        self.page.get_by_role('button', name='Salvar acessos', exact=True).click()
        expect(self.page.locator('#members-status')).to_contain_text('Acessos atualizados')
        self.capture('members')
        self.assertEqual(self.context.request.patch(base + '/' + story['id'], headers=auth_b, data={'title': 'Permitida após papel PO'}).status, 200)
        self.page.locator('#projects-logout').click()
        self.sign_in('rbac-member@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto compartilhado', exact=True).click()
        expect(self.page.get_by_role('button', name='Editar projeto', exact=True)).to_be_visible()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        self.page.get_by_role('button', name='Permitida após papel PO', exact=True).click()
        expect(self.page.locator('#story-update-title')).to_be_enabled()
        self.page.locator('#backlog-logout').click()
        self.sign_in('rbac-owner@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto compartilhado', exact=True).click()
        self.page.get_by_role('button', name='Membros e papéis', exact=True).click()
        self.page.get_by_role('button', name='Editar acessos de ' + user_b, exact=True).click()
        self.page.once('dialog', lambda dialog: dialog.accept())
        self.page.get_by_role('button', name='Remover integrante', exact=True).click()
        expect(self.page.locator('#members-status')).to_contain_text('Integrante removido')
        self.assertEqual(self.context.request.get(base, headers=auth_b).status, 404)
        self.assertEqual(self.context.request.post(self.projects_url + '/invitations/accept', headers=auth_b, data={'code': code}).status, 404)
