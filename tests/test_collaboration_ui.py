from playwright.sync_api import expect

from browser_support import BrowserCase
from test_backlog_api import STORY
from test_projects_api import PROJECT


ALL = ['project:read', 'project:update', 'project:delete', 'project:members:read',
       'project:members:manage', 'backlog:read', 'backlog:create', 'backlog:update', 'backlog:update_status']
DEV = ['project:read', 'project:members:read', 'backlog:read', 'backlog:update_status']
OTHER = '44444444-4444-4444-8444-444444444444'
CODE = 'a' * 43


class CollaborationUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.mock_auth()
        self.project = {**PROJECT, 'permissions': ALL}
        self.member = {'user_id': OTHER, 'roles': ['developer'], 'expires_at': None, 'is_owner': False}
        self.profile = {'user_id': self.identity['id'], 'summary': '', 'seniority': 'not_informed',
                        'weekly_availability_hours': 0, 'skills': []}
        self.writes = []
        self.page.route('**/auth/profile', self.profile_response)
        self.page.route('**/projects?*', lambda r: r.fulfill(json={'items': [self.project], 'total': 1, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects/' + PROJECT['id'], lambda r: r.fulfill(json=self.project))
        self.page.route('**/projects/*/members**', self.members_response)
        self.page.route('**/projects/*/roles', lambda r: r.fulfill(json={'items': [
            {'key': 'product_owner', 'name': 'Product Owner', 'permissions': [p for p in ALL if p not in ('project:delete', 'project:members:manage')]},
            {'key': 'project_manager', 'name': 'PM/Scrum Master', 'permissions': [p for p in ALL if p != 'project:delete']},
            {'key': 'developer', 'name': 'Desenvolvedor', 'permissions': DEV}]}))
        self.page.route('**/projects/*/invitations', self.invite_response)
        self.page.route('**/invitations/accept', self.accept_response)
        self.page.route('**/invitations/decline', self.decline_response)
        self.page.route('**/projects/*/stories**', self.story_response)
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-view')).to_be_visible()

    def profile_response(self, route):
        if route.request.method == 'PATCH':
            self.writes.append(('profile', route.request.post_data_json))
            self.profile.update(route.request.post_data_json)
        route.fulfill(json=self.profile)

    def members_response(self, route):
        if route.request.method == 'PATCH':
            self.writes.append(('member', route.request.post_data_json))
            self.member.update(route.request.post_data_json)
            route.fulfill(json=self.member)
        elif route.request.method == 'DELETE':
            self.writes.append(('remove', OTHER))
            route.fulfill(status=204)
        else:
            route.fulfill(json={'items': [
                {'user_id': self.identity['id'], 'roles': ['owner'], 'expires_at': None, 'is_owner': True},
                self.member], 'total': 2, 'limit': 20, 'offset': 0})

    def invite_response(self, route):
        data = route.request.post_data_json
        self.writes.append(('invite', data))
        route.fulfill(status=201, json={'id': '55555555-5555-4555-8555-555555555555',
            'project_id': PROJECT['id'], **data, 'expires_at': data.get('expires_at'),
            'code': CODE, 'code_expires_at': '2030-01-01T00:00:00Z'})

    def accept_response(self, route):
        self.writes.append(('accept', route.request.post_data_json))
        route.fulfill(json={'project_id': PROJECT['id'], 'user_id': self.identity['id'],
            'is_owner': False, 'roles': ['developer'], 'permissions': DEV})

    def decline_response(self, route):
        self.writes.append(('decline', route.request.post_data_json))
        route.fulfill(status=204)

    def story_response(self, route):
        if route.request.method == 'PATCH':
            self.writes.append(('story', route.request.post_data_json))
            route.fulfill(json={**STORY, **route.request.post_data_json})
        elif route.request.url.split('?')[0].endswith('/stories'):
            route.fulfill(json={'items': [STORY], 'total': 1, 'limit': 20, 'offset': 0})
        else:
            route.fulfill(json=STORY)

    def open_project(self):
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name=PROJECT['name'], exact=True).click()

    def test_edit_profile_skills_levels_and_availability(self):
        expect(self.page.locator('#profile-user-id')).to_have_text(self.identity['id'])
        self.page.get_by_role('button', name='Editar perfil profissional', exact=True).click()
        expect(self.page.locator('#professional-profile-form')).to_be_visible()
        self.page.get_by_label('Resumo profissional', exact=True).fill('Experiência com APIs e testes.')
        self.page.get_by_label('Senioridade', exact=True).select_option('mid')
        self.page.get_by_label('Disponibilidade semanal em horas', exact=True).fill('20')
        self.page.get_by_role('button', name='Adicionar competência', exact=True).click()
        self.page.get_by_label('Competência 1', exact=True).fill('  Python  ')
        self.page.get_by_label('Domínio da competência 1', exact=True).select_option('4')
        self.page.get_by_role('button', name='Salvar perfil', exact=True).click()
        expect(self.page.locator('#professional-profile-status')).to_contain_text('Perfil atualizado')
        self.assertEqual(self.writes[-1], ('profile', {'summary': 'Experiência com APIs e testes.',
            'seniority': 'mid', 'weekly_availability_hours': 20, 'skills': [{'name': 'Python', 'level': 4}]}))
        self.page.locator('#logout-button').click()
        expect(self.page.locator('#profile-summary')).to_have_value('')

    def test_invite_code_accept_and_decline_without_url_or_storage(self):
        self.page.get_by_label('Código do convite', exact=True).fill(CODE)
        self.page.get_by_role('button', name='Aceitar convite', exact=True).click()
        expect(self.page.locator('#invitation-status')).to_contain_text('Convite aceito')
        expect(self.page.get_by_label('Código do convite', exact=True)).to_have_value('')
        self.assertEqual(self.writes[-1], ('accept', {'code': CODE}))
        self.page.get_by_label('Código do convite', exact=True).fill(CODE)
        self.page.get_by_role('button', name='Recusar convite', exact=True).click()
        expect(self.page.locator('#invitation-status')).to_contain_text('Convite recusado')
        self.assertNotIn(CODE, self.page.url)
        self.assertNotIn(CODE, self.page.evaluate('JSON.stringify(localStorage)'))

    def test_owner_invites_and_changes_multiple_roles(self):
        self.open_project()
        self.page.get_by_role('button', name='Membros e papéis', exact=True).click()
        expect(self.page.locator('#members-list')).to_contain_text(OTHER)
        self.page.get_by_label('ID da conta convidada', exact=True).fill(OTHER)
        self.page.locator('#invite-role-developer').check()
        self.page.get_by_role('button', name='Gerar código de convite', exact=True).click()
        expect(self.page.locator('#generated-invite-code')).to_have_value(CODE)
        self.assertEqual(self.writes[-1][1]['user_id'], OTHER)
        self.page.get_by_role('button', name='Editar acessos de ' + OTHER, exact=True).click()
        self.page.locator('#member-role-product_owner').check()
        self.page.locator('#member-role-developer').check()
        self.page.get_by_role('button', name='Salvar acessos', exact=True).click()
        expect(self.page.locator('#members-status')).to_contain_text('Acessos atualizados')
        self.assertEqual(set(self.writes[-1][1]['roles']), {'product_owner', 'developer'})
        self.assertEqual(self.page.get_by_role('button', name='Editar acessos de ' + self.identity['id'], exact=True).count(), 0)

    def test_developer_only_updates_status_and_cannot_edit_project(self):
        self.project = {**PROJECT, 'owner_id': OTHER, 'permissions': DEV}
        self.open_project()
        expect(self.page.get_by_role('button', name='Editar projeto', exact=True)).to_be_hidden()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        expect(self.page.get_by_role('button', name='Criar história', exact=True)).to_be_hidden()
        self.page.get_by_role('button', name=STORY['title'], exact=True).click()
        expect(self.page.locator('#story-update-title')).to_be_disabled()
        expect(self.page.locator('#story-update-priority')).to_be_disabled()
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('Alterações salvas')
        self.assertEqual(self.writes[-1], ('story', {'status': 'done'}))

    def test_403_explains_permissions_without_logging_out(self):
        self.open_project()
        self.page.get_by_role('button', name='Backlog', exact=True).click()
        self.page.get_by_role('button', name=STORY['title'], exact=True).click()
        self.page.route('**/projects/*/stories/' + STORY['id'], lambda r: r.fulfill(status=403))
        self.page.get_by_label('Status da história', exact=True).select_option('done')
        self.page.get_by_role('button', name='Salvar alterações', exact=True).click()
        expect(self.page.locator('#backlog-status')).to_contain_text('permissão')
        expect(self.page.locator('#login-view')).to_be_hidden()

    def test_late_profile_response_after_logout_is_discarded(self):
        pending = []
        self.page.route('**/auth/profile', lambda r: pending.append(r))
        self.page.get_by_role('button', name='Editar perfil profissional', exact=True).click()
        self.page.locator('#logout-button').click()
        pending[0].fulfill(json={**self.profile, 'summary': 'Private late response'})
        expect(self.page.locator('#profile-summary')).to_have_value('')
        expect(self.page.locator('#professional-profile')).to_be_hidden()

    def test_editing_roles_preserves_unchanged_expiry_seconds(self):
        self.member['expires_at'] = '2030-01-01T12:34:56Z'
        self.open_project()
        self.page.get_by_role('button', name='Membros e papéis', exact=True).click()
        self.page.get_by_role('button', name='Editar acessos de ' + OTHER, exact=True).click()
        self.page.locator('#member-role-product_owner').check()
        self.page.get_by_role('button', name='Salvar acessos', exact=True).click()
        expect(self.page.locator('#members-status')).to_contain_text('Acessos atualizados')
        self.assertNotIn('expires_at', self.writes[-1][1])
        self.assertEqual(self.member['expires_at'], '2030-01-01T12:34:56Z')

    def test_duplicate_skills_are_rejected_without_writing(self):
        self.page.get_by_role('button', name='Editar perfil profissional', exact=True).click()
        expect(self.page.locator('#profile-save')).to_be_enabled()
        for index, value in [(1, 'Python'), (2, ' python ')]:
            self.page.get_by_role('button', name='Adicionar competência', exact=True).click()
            self.page.get_by_label('Competência ' + str(index), exact=True).fill(value)
        self.page.get_by_role('button', name='Salvar perfil', exact=True).click()
        expect(self.page.locator('#professional-profile-status')).to_contain_text('competências distintas')
        self.assertEqual(self.writes, [])

    def test_invitation_response_after_logout_does_not_restore_state(self):
        pending = []
        self.page.route('**/invitations/accept', lambda r: pending.append(r))
        self.page.get_by_label('Código do convite', exact=True).fill(CODE)
        self.page.get_by_role('button', name='Aceitar convite', exact=True).click()
        expect(self.page.locator('#invitation-accept')).to_be_disabled()
        self.page.locator('#logout-button').click()
        pending[0].fulfill(json={'project_id': PROJECT['id'], 'user_id': self.identity['id'],
            'is_owner': False, 'roles': ['developer'], 'permissions': DEV})
        expect(self.page.locator('#invitation-code')).to_have_value('')
        expect(self.page.locator('#invitation-status')).to_have_text('')
        expect(self.page.locator('#profile-view')).to_be_hidden()

    def test_non_owner_missing_permissions_does_not_get_owner_actions(self):
        self.project = {**PROJECT, 'owner_id': OTHER}
        self.open_project()
        expect(self.page.get_by_role('button', name='Editar projeto', exact=True)).to_be_hidden()
        expect(self.page.get_by_role('button', name='Membros e papéis', exact=True)).to_be_hidden()
        expect(self.page.get_by_role('button', name='Backlog', exact=True)).to_be_hidden()
