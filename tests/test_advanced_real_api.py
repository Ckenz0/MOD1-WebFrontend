import os
import unittest
import base64
import hashlib
import hmac
import struct
import time
import re
from urllib.parse import urlsplit
from pathlib import Path

from playwright.sync_api import expect

import test_backlog_real_api as real


@unittest.skipUnless(all(os.environ.get(k) for k in (
    'AUTH_BACKEND_PATH', 'PROJECTS_BACKEND_PATH', 'BACKLOG_BACKEND_PATH')),
    'Set backend paths to run the complete local application')
class AdvancedRealApiTests(real.BacklogRealApiTests):
    test_registration_project_stories_progress_restart_and_access_isolation = None

    def additional_auth_settings(self):
        return {'LOCAL_MAILBOX_ENABLED': 'true', 'FRONTEND_ORIGIN': self.base_url,
                'MFA_ENCRYPTION_KEY': base64.urlsafe_b64encode(os.urandom(32)).decode()}

    def test_mfa_recovery_email_confirmation_and_reset_preserve_second_factor(self):
        email = 'security@example.com'
        self.register(email)
        result = self.context.request.post(self.auth_url + '/auth/token', form={
            'username': email, 'password': 'ProjetoMvp!2026'})
        headers = {'Authorization': 'Bearer ' + result.json()['access_token']}
        user = self.context.request.get(self.auth_url + '/auth/me', headers=headers).json()
        self.admin(self.auth_python, self.auth_root, self.auth_env,
            'from mod1_auth.cli import main; raise SystemExit(main(["set-admin", "--user-id", '
            + repr(user['id']) + ', "--admin"]))')
        self.page.goto(self.base_url)
        self.sign_in(email)
        self.page.get_by_role('button', name='Segurança e sessões', exact=True).click()
        self.page.get_by_role('button', name='Segundo fator', exact=True).click()
        self.page.get_by_label('Senha atual para configurar o segundo fator', exact=True).fill('ProjetoMvp!2026')
        self.page.get_by_role('button', name='Configurar segundo fator', exact=True).click()
        seed = self.page.get_by_label('Chave de configuração', exact=True).input_value()
        raw = hmac.new(base64.b32decode(seed), struct.pack('>Q', int(time.time()) // 30), hashlib.sha1).digest()
        offset = raw[-1] & 15
        code = str((struct.unpack('>I', raw[offset:offset+4])[0] & 0x7fffffff) % 1000000).zfill(6)
        self.page.get_by_label('Código do aplicativo autenticador', exact=True).fill(code)
        self.page.get_by_role('button', name='Ativar segundo fator', exact=True).click()
        codes = self.page.get_by_label('Códigos de recuperação', exact=True).input_value().splitlines()
        self.assertEqual(len(codes), 10)
        self.page.get_by_role('button', name='Voltar para minha conta', exact=True).click()
        self.page.get_by_role('button', name='Sair', exact=True).click()
        self.page.get_by_label('E-mail', exact=True).fill(email)
        self.page.get_by_label('Senha', exact=True).fill('ProjetoMvp!2026')
        self.page.get_by_role('button', name='Entrar', exact=True).click()
        expect(self.page.get_by_role('heading', name='Confirmar segundo fator', exact=True)).to_be_visible()
        expect(self.page.locator('#profile-view')).to_be_hidden()
        self.page.get_by_label('Código do autenticador ou de recuperação', exact=True).fill(codes[0])
        self.page.get_by_label('Usar código de recuperação', exact=True).check()
        self.page.get_by_role('button', name='Confirmar acesso', exact=True).click()
        expect(self.page.locator('#profile-view')).to_be_visible()
        self.page.get_by_role('button', name='Segurança e sessões', exact=True).click()
        self.page.get_by_role('button', name='E-mail', exact=True).click()
        self.page.get_by_role('button', name='Enviar link de confirmação', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('confira a caixa')
        mailbox = self.context.request.get(self.auth_url + '/admin/mailbox', headers=headers).json()
        confirmation = next(re.search(r'https?://\S+', m['body']).group() for m in mailbox['items'] if '#verify-email=' in m['body'])
        self.page.goto(confirmation)
        self.page.wait_for_function('location.hash === ""')
        self.assertEqual(urlsplit(self.page.url).fragment, '')
        self.page.get_by_role('button', name='Confirmar meu e-mail', exact=True).click()
        expect(self.page.locator('#recovery-view')).to_contain_text('Endereço de e-mail confirmado')
        self.page.get_by_role('button', name='Voltar para entrar', exact=True).click()
        self.page.get_by_role('button', name='Esqueci minha senha', exact=True).click()
        self.page.get_by_label('E-mail para recuperação', exact=True).fill(email)
        self.page.get_by_role('button', name='Solicitar link de recuperação', exact=True).click()
        expect(self.page.locator('#recovery-status')).to_contain_text('Se o endereço estiver cadastrado')
        mailbox = self.context.request.get(self.auth_url + '/admin/mailbox', headers=headers).json()
        reset = next(re.search(r'https?://\S+', m['body']).group() for m in mailbox['items'] if '#recovery=' in m['body'])
        self.page.goto(reset)
        self.page.wait_for_function('location.hash === ""')
        self.assertEqual(urlsplit(self.page.url).fragment, '')
        self.page.locator('#recovery-view').get_by_label('Nova senha', exact=True).fill('SenhaNova!2026Mod1')
        self.page.locator('#recovery-view').get_by_label('Confirme a nova senha', exact=True).fill('SenhaNova!2026Mod1')
        self.page.get_by_label('Código de recuperação (alternativa ao autenticador)', exact=True).fill(codes[1])
        self.page.get_by_role('button', name='Salvar nova senha', exact=True).click()
        expect(self.page.locator('#recovery-view')).to_contain_text('Senha alterada')
        self.assertEqual(self.context.request.get(self.auth_url + '/auth/me', headers=headers).status, 401)
        self.assertEqual(self.context.request.get(self.projects_url + '/projects', headers=headers).status, 401)
        self.assertEqual(self.context.request.get(self.backlog_url + '/projects/11111111-1111-4111-8111-111111111111/items', headers=headers).status, 401)
        result = self.context.request.post(self.auth_url + '/auth/token', form={
            'username': email, 'password': 'SenhaNova!2026Mod1'})
        self.assertTrue(result.json().get('mfa_required'))

    def test_metadata_custom_role_guided_item_board_and_history(self):
        self.register('advanced@example.com')
        self.page.goto(self.base_url)
        self.sign_in('advanced@example.com')
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_label('Nome do projeto', exact=True).fill('Entrega multicamadas')
        self.page.get_by_role('button', name='Criar projeto', exact=True).click()
        expect(self.page.locator('#projects-status')).to_contain_text('Projeto criado')
        self.page.get_by_role('button', name='Gerenciar projeto e planejamento', exact=True).click()
        self.page.get_by_label('Escopo detalhado', exact=True).fill('Planejamento e acessos')
        self.page.get_by_label('Orçamento disponível', exact=True).fill('12000.50')
        self.page.get_by_label('Etiquetas', exact=True).fill('entrega, engenharia')
        self.page.get_by_label('Stack tecnológica', exact=True).fill('Python, JavaScript')
        self.page.get_by_label('Data prevista de início', exact=True).fill('2026-11-01')
        self.page.get_by_label('Data prevista de término', exact=True).fill('2026-12-01')
        self.stop(self.auth_process)
        self.page.get_by_role('button', name='Salvar contexto do projeto', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('indisponível')
        expect(self.page.get_by_label('Escopo detalhado', exact=True)).to_have_value('Planejamento e acessos')
        expect(self.page.get_by_label('Orçamento disponível', exact=True)).to_have_value('12000.50')
        expect(self.page.locator('#login-view')).to_be_hidden()
        self.auth_process = self.start(self.auth_python, self.auth_root, self.auth_env,
            'mod1_auth.main:create_app', self.auth_port)
        self.page.get_by_role('button', name='Salvar contexto do projeto', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('Contexto atualizado')
        self.page.get_by_role('button', name='Atualizar contexto', exact=True).click()
        expect(self.page.get_by_label('Orçamento disponível', exact=True)).to_have_value('12000.50')
        self.page.get_by_role('button', name='Papéis e acessos', exact=True).click()
        self.page.get_by_role('button', name='Criar papel personalizado', exact=True).click()
        self.page.get_by_label('Nome do papel personalizado', exact=True).fill('Observador')
        self.page.get_by_label('Consultar projeto', exact=True).check()
        self.page.get_by_role('button', name='Salvar papel personalizado', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('Papel salvo')
        self.page.get_by_role('button', name='Quadro e itens', exact=True).click()
        self.page.get_by_role('button', name='Novo item de backlog', exact=True).click()
        self.page.get_by_label('Título do item', exact=True).fill('Consultar planejamento')
        self.page.get_by_label('Persona da história', exact=True).fill('Product Owner')
        self.page.get_by_label('Ação desejada', exact=True).fill('Consultar o quadro')
        self.page.get_by_label('Objetivo ou benefício', exact=True).fill('Planejar a entrega')
        self.page.get_by_label('Critérios de aceitação do item', exact=True).fill('Exibir os itens autorizados')
        self.page.get_by_label('Prioridade MoSCoW do item', exact=True).select_option('must')
        self.page.get_by_label('Estimativa de esforço', exact=True).fill('3.5')
        self.page.get_by_label('Unidade da estimativa', exact=True).select_option('points')
        self.page.get_by_role('button', name='Criar item de backlog', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('Item criado')
        self.page.get_by_role('button', name='Atualizar quadro', exact=True).click()
        self.page.get_by_role('button', name='Novo item de backlog', exact=True).click()
        self.page.get_by_label('Título do item', exact=True).fill('Preparar ambiente')
        self.page.get_by_role('button', name='Criar item de backlog', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('Item criado')
        self.page.get_by_role('button', name='Atualizar quadro', exact=True).click()
        source = self.page.locator('.board-item').filter(has=self.page.get_by_role('button', name='Preparar ambiente', exact=True))
        target = self.page.locator('.board-item').filter(has=self.page.get_by_role('button', name='Consultar planejamento', exact=True))
        with self.page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/items/reorder')) as reordered:
            source.drag_to(target)
        self.assertEqual(reordered.value.status, 200)
        expect(self.page.locator('#workspace-status')).to_contain_text('Ordem salva')
        self.page.get_by_role('button', name='Atualizar quadro', exact=True).click()
        expect(self.page.locator('.board-item').first).to_contain_text('Preparar ambiente')
        self.page.get_by_role('button', name='Consultar planejamento', exact=True).last.click()
        expect(self.page.locator('#workspace-content')).to_contain_text('Planejar a entrega')
        self.page.get_by_label('Nova situação do item', exact=True).select_option('in_progress')
        self.page.get_by_role('button', name='Atualizar situação do item', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('Situação atualizada')
        self.page.get_by_role('button', name='Voltar para o quadro', exact=True).click()
        expect(self.page.get_by_role('region', name='Em andamento', exact=True)).to_contain_text('Consultar planejamento')
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        if os.environ.get('CAPTURE_US_EVIDENCE'):
            directory = Path(os.environ['CAPTURE_US_EVIDENCE'])
            directory.mkdir(parents=True, exist_ok=True)
            for width, height, theme, filename in [
                (1366, 900, 'light', 'planning-desktop-light.png'),
                (390, 844, 'dark', 'planning-mobile-dark.png')]:
                self.page.set_viewport_size({'width': width, 'height': height})
                self.page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;scrollTo(0,0)}', theme)
                self.page.screenshot(path=str(directory / filename), full_page=True)
