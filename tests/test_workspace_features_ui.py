from playwright.sync_api import expect

from browser_support import BrowserCase


class WorkspaceFeaturesUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.mock_auth(identity={**self.identity, 'is_admin': True, 'email_verified': False})
        self.page.route('**/auth/logout', lambda route: route.fulfill(status=204))
        self.page.route('**/auth/session/activity', lambda route: route.fulfill(json={
            'idle_expires_at': '2099-01-01T00:00:00Z', 'absolute_expires_at': '2099-01-01T01:00:00Z'}))
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def test_security_lists_and_revokes_another_session(self):
        sessions = [
            {'id': '33333333-3333-4333-8333-333333333333', 'client_label': 'Este navegador', 'is_current': True,
             'created_at': '2026-10-30T12:00:00Z', 'last_activity_at': '2026-10-30T12:01:00Z'},
            {'id': '44444444-4444-4444-8444-444444444444', 'client_label': 'Navegador de teste', 'is_current': False,
             'created_at': '2026-10-30T12:00:00Z', 'last_activity_at': '2026-10-30T12:01:00Z'}]
        revoked = []
        self.page.route('**/auth/sessions', lambda route: route.fulfill(json={'items': sessions, 'total': len(sessions), 'limit': 20, 'offset': 0}))
        def revoke(route):
            revoked.append(route.request.method)
            sessions.pop()
            route.fulfill(status=204)
        self.page.route('**/auth/sessions/44444444-4444-4444-8444-444444444444', revoke)
        self.page.get_by_role('button', name='Segurança e sessões', exact=True).click()
        expect(self.page.get_by_role('heading', name='Sessões ativas', exact=True)).to_be_visible()
        self.page.get_by_role('button', name='Revogar sessão de Navegador de teste', exact=True).click()
        expect(self.page.get_by_role('button', name='Revogar sessão de Navegador de teste', exact=True)).to_have_count(0)
        self.assertEqual(revoked, ['DELETE'])

    def test_create_team_and_accept_team_invite_are_distinct_from_project_invite(self):
        teams, writes = [], []
        def team_route(route):
            if route.request.method == 'POST':
                draft = route.request.post_data_json
                writes.append(draft)
                teams.append({'id': '55555555-5555-4555-8555-555555555555', 'name': draft['name'],
                    'description': draft.get('description', ''), 'cost_center': draft.get('cost_center'),
                    'owner_id': self.identity['id'], 'version': 1})
                route.fulfill(status=201, json=teams[-1])
            else:
                route.fulfill(json={'items': teams, 'total': len(teams), 'limit': 20, 'offset': 0})
        self.page.route('**/teams', team_route)
        self.page.route('**/teams?*', team_route)
        accepted = []
        self.page.route('**/team-invitations/accept', lambda route: (
            accepted.append(route.request.post_data_json), route.fulfill(json={'team_id': '55555555-5555-4555-8555-555555555555'})))
        self.page.get_by_role('button', name='Equipes e alocação', exact=True).click()
        self.page.get_by_label('Nome da equipe', exact=True).fill('Equipe de integração')
        self.page.get_by_label('Descrição da equipe', exact=True).fill('Fluxos do módulo 1')
        self.page.get_by_label('Centro de custo', exact=True).fill('ENG-01')
        self.page.get_by_role('button', name='Criar equipe', exact=True).click()
        expect(self.page.get_by_role('button', name='Equipe de integração', exact=True)).to_be_visible()
        self.assertEqual(writes, [{'name': 'Equipe de integração', 'description': 'Fluxos do módulo 1', 'cost_center': 'ENG-01'}])
        self.page.get_by_label('Código de convite de equipe', exact=True).fill('t' * 43)
        self.page.get_by_role('button', name='Aceitar convite de equipe', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('Convite de equipe aceito')
        self.assertEqual(accepted, [{'code': 't' * 43}])

    def test_admin_is_not_visible_for_a_non_admin(self):
        self.mock_auth(identity={**self.identity, 'is_admin': False})
        self.page.get_by_role('button', name='Sair', exact=True).click()
        self.login()
        expect(self.page.get_by_role('button', name='Administração', exact=True)).to_be_hidden()

    def test_dark_workspace_keyboard_focus_has_visible_contrast(self):
        self.page.route('**/auth/sessions', lambda route: route.fulfill(json={
            'items': [], 'total': 0, 'limit': 20, 'offset': 0}))
        self.page.locator('html').evaluate("node => node.dataset.theme = 'dark'")
        self.page.get_by_role('button', name='Segurança e sessões', exact=True).click()
        button = self.page.get_by_role('button', name='Sessões', exact=True)
        expect(button).to_be_enabled()
        self.page.keyboard.press('Tab')
        button.focus()
        expect(button).to_be_focused()
        result = button.evaluate('''node => {
          const style = getComputedStyle(node);
          let parent = node.parentElement;
          while (parent && getComputedStyle(parent).backgroundColor === 'rgba(0, 0, 0, 0)') parent = parent.parentElement;
          const background = getComputedStyle(parent).backgroundColor;
          const luminance = value => {
            const c = value.match(/\\d+/g).slice(0, 3).map(Number).map(v => v / 255)
              .map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
            return c[0] * .2126 + c[1] * .7152 + c[2] * .0722;
          };
          const levels = [luminance(style.outlineColor), luminance(background)].sort((a, b) => a - b);
          return { visible: node.matches(':focus-visible') && style.outlineStyle !== 'none',
            contrast: (levels[1] + .05) / (levels[0] + .05) };
        }''')
        self.assertTrue(result['visible'])
        self.assertGreaterEqual(result['contrast'], 3,
                                'Keyboard focus must contrast with the surrounding dark surface')

    def test_notification_inbox_marks_only_selected_message_as_read(self):
        notification = {'id': '44444444-4444-4444-8444-444444444444',
            'title': 'Equipe aprovada', 'message': 'Você participa da equipe de entrega.',
            'created_at': '2026-10-30T12:00:00Z', 'read_at': None}
        writes = []
        self.page.route('**/notifications?*', lambda route: route.fulfill(json={
            'items': [notification], 'total': 1, 'limit': 20, 'offset': 0}))
        def mark(route):
            writes.append(route.request.method)
            notification['read_at'] = '2026-10-30T12:01:00Z'
            route.fulfill(json=notification)
        self.page.route('**/notifications/44444444-4444-4444-8444-444444444444/read', mark)
        self.page.get_by_role('button', name='Notificações', exact=True).click()
        expect(self.page.get_by_role('table', name='Minhas notificações')).to_contain_text('Equipe aprovada')
        self.page.get_by_role('button', name='Marcar como lida', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('Mensagem marcada como lida')
        self.page.get_by_role('button', name='Atualizar notificações', exact=True).click()
        expect(self.page.get_by_role('button', name='Marcar como lida', exact=True)).to_have_count(0)
        self.assertEqual(writes, ['POST'])

    def test_recovery_request_is_generic_and_does_not_echo_server_contents(self):
        calls = []
        self.page.route('**/auth/password/reset/request', lambda route: (
            calls.append(route.request.post_data_json), route.fulfill(status=202, json={'message': 'private account state'})))
        self.page.get_by_role('button', name='Sair', exact=True).click()
        self.page.get_by_role('button', name='Esqueci minha senha', exact=True).click()
        self.page.get_by_label('E-mail para recuperação', exact=True).fill('conta@example.com')
        self.page.get_by_role('button', name='Solicitar link de recuperação', exact=True).click()
        expect(self.page.locator('#recovery-status')).to_contain_text('Se o endereço estiver cadastrado')
        self.assertNotIn('private account state', self.page.content())
        self.assertEqual(calls, [{'email': 'conta@example.com'}])

    def test_leaving_public_token_flow_clears_previous_identity_before_recovery(self):
        self.page.goto(self.base_url + '#verify-email=' + 'local-synthetic-token')
        expect(self.page.get_by_role('button', name='Confirmar meu e-mail', exact=True)).to_be_visible()
        self.page.get_by_role('button', name='Voltar para entrar', exact=True).click()
        self.page.get_by_role('button', name='Esqueci minha senha', exact=True).click()
        self.page.get_by_label('E-mail para recuperação', exact=True).fill('security@example.com')
        self.page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        expect(self.page.get_by_label('E-mail para recuperação', exact=True)).to_have_value('security@example.com')

    def test_simulated_access_recommendation_exposes_window_and_requires_human_approval(self):
        pid = '55555555-5555-4555-8555-555555555555'
        rid = '66666666-6666-4666-8666-666666666666'
        project = {'id': pid, 'owner_id': self.identity['id'], 'name': 'Projeto de revisão',
            'description': '', 'objective': '', 'created_at': '2026-10-30T12:00:00Z',
            'permissions': [], 'status': 'active', 'version': 1, 'archived': False}
        proposal = {'id': rid, 'kind': 'access_revocation', 'status': 'pending', 'version': 1,
            'summary': 'Revisar acesso observado', 'justification': 'Janela observada e evidência identificada',
            'simulated': True, 'provider': 'structured-http', 'model': 'local-test',
            'created_at': '2026-10-30T12:00:00Z', 'evidence': ['project:' + pid], 'suggestions': []}
        calls, approvals = [], []
        self.page.route('**/projects?*', lambda route: route.fulfill(json={
            'items': [project], 'total': 1, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects/' + pid, lambda route: route.fulfill(json=project))
        self.page.route('**/projects/' + pid + '/summary', lambda route: route.fulfill(json={
            'project': project, 'teams': [], 'backlog_available': False, 'backlog': None}))
        self.page.route('**/projects/' + pid + '/recommendations?*', lambda route: route.fulfill(json={
            'items': [], 'total': 0, 'limit': 20, 'offset': 0}))
        def generate(route):
            calls.append(route.request.post_data_json)
            route.fulfill(status=201, json=proposal)
        self.page.route('**/projects/' + pid + '/recommendations', generate)
        def approve(route):
            approvals.append(route.request.post_data_json)
            route.fulfill(json={**proposal, 'status': 'approved', 'version': 2})
        self.page.route('**/projects/' + pid + '/recommendations/' + rid + '/approve', approve)
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name='Projeto de revisão', exact=True).click()
        self.page.get_by_role('button', name='Gerenciar projeto e planejamento', exact=True).click()
        self.page.get_by_role('button', name='Recomendações', exact=True).click()
        self.page.get_by_label('Tipo de recomendação', exact=True).select_option('access_revocation')
        self.page.get_by_label('Dias sem atividade autorizada observada', exact=True).fill('45')
        self.page.get_by_role('button', name='Solicitar recomendação', exact=True).click()
        expect(self.page.locator('#workspace-content')).to_contain_text('Simulação local')
        self.assertEqual(calls, [{'kind': 'access_revocation', 'constraints': {'unused_days': 45}}])
        self.assertEqual(approvals, [])
        self.page.get_by_role('button', name='Aprovar recomendação', exact=True).click()
        expect(self.page.locator('#workspace-content')).to_contain_text('Aprovada')
        self.assertEqual(approvals, [{'expected_version': 1}])
