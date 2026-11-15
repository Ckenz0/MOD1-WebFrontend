"""Project controls follow the independent permissions enforced by the APIs."""

from playwright.sync_api import expect

from browser_support import BrowserCase


class WorkspacePermissionsUiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def open_project(self, permissions, initial='context', archived=False):
        self.evaluate('''async ({permissions, initial, archived}) => {
          document.body.innerHTML = '<main id="main"></main>';
          const {createWorkspaceController} = await import('/scripts/workspace-controller.js');
          const project = {id:'project-a', owner_id:'owner-a', name:'Projeto compartilhado',
            description:'Planejamento', objective:'Entrega', status:archived?'completed':'active', archived,
            version:1, permissions};
          window.permissionRequests = [];
          const projects = {request: async (method, path) => {
            window.permissionRequests.push(path);
            if (path.endsWith('/summary')) return {project, teams:[], backlog_available:false, backlog:null};
            if (path.endsWith('/teams')) return {items:[
              {team_id:'team-a', team_name:'Equipe de entrega', roles:['developer']}], total:1};
            if (path.endsWith('/allocations')) {
              if (!permissions.includes('project:members:manage')) throw new Error('403: alocações restritas');
              return {items:[], total:0};
            }
            if (path === '/teams?limit=100&offset=0') return {items:[{id:'team-a', name:'Equipe de entrega'}], total:1};
            if (path === '/projects/project-a/recommendations?limit=20&offset=0') return {items:[
              {id:'proposal-a', kind:'roles', status:'pending', version:1, summary:'Papel sugerido',
                justification:'Tarefas autorizadas', provider:'gemini', model:'test-model',
                created_at:'2026-11-15T12:00:00Z', evidence:['project:project-a'],
                suggestions:[{user_id:'member-b', roles:['developer']}]}], total:1, limit:20, offset:0};
            if (path === '/projects/project-a') return project;
            throw new Error('Unexpected project request: ' + path);
          }};
          const backlog = {request: async (method, path) => {
            window.permissionRequests.push(path);
            if (path.endsWith('/board')) return {version:1, columns:{todo:[], in_progress:[], done:[]}};
            if (path.includes('/items?')) return {items:[], total:0, limit:100, offset:0};
            throw new Error('Unexpected backlog request: ' + path);
          }};
          const workspace = createWorkspaceController({clients:{projects, backlog},
            account:{accessToken:async () => 'synthetic-token'},
            session:{getSessionId:() => 'synthetic-session'}, getIdentity:() => ({id:'member-a'}),
            onEnter:() => {}, onBack:() => {}, onUnauthorized:() => {}});
          await workspace.openProject(project, initial);
        }''', {'permissions': permissions, 'initial': initial, 'archived': archived})

    def open_teams(self):
        self.page.get_by_role('button', name='Equipes', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')

    def test_member_can_read_linked_teams_without_manager_allocation_request(self):
        self.open_project(['project:read', 'project:members:read', 'backlog:read'])
        self.open_teams()
        expect(self.page.get_by_role('table', name='Equipes do projeto')).to_contain_text('Equipe de entrega')
        expect(self.page.get_by_role('button', name='Vincular equipe', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Salvar alocação', exact=True)).to_have_count(0)
        self.assertNotIn('/projects/project-a/allocations', self.evaluate('() => window.permissionRequests'))

    def test_team_manager_controls_do_not_require_or_offer_allocation_management(self):
        self.open_project(['project:read', 'project:members:read', 'project:teams:manage'])
        self.open_teams()
        expect(self.page.get_by_role('button', name='Vincular equipe', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Desvincular equipe', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Salvar alocação', exact=True)).to_have_count(0)
        self.assertNotIn('/projects/project-a/allocations', self.evaluate('() => window.permissionRequests'))

    def test_member_manager_can_manage_allocations_without_team_link_controls(self):
        self.open_project(['project:read', 'project:members:read', 'project:members:manage'])
        self.open_teams()
        expect(self.page.get_by_role('button', name='Salvar alocação', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Vincular equipe', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Desvincular equipe', exact=True)).to_have_count(0)
        self.assertNotIn('/teams?limit=100&offset=0', self.evaluate('() => window.permissionRequests'))

    def test_project_reader_is_not_offered_sections_requiring_other_permissions(self):
        self.open_project(['project:read'])
        for label in ['Quadro e itens', 'Equipes', 'Papéis e acessos', 'Histórico', 'Recomendações']:
            expect(self.page.get_by_role('button', name=label, exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Contexto', exact=True)).to_be_visible()

    def test_backlog_reader_is_not_offered_backlog_generation(self):
        self.open_project(['project:read', 'backlog:read'], initial='board')
        expect(self.page.get_by_role('button', name='Atualizar quadro', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Sugerir backlog inicial', exact=True)).to_have_count(0)

    def test_recommendation_kinds_require_each_kind_permission_and_backlog_context(self):
        for extra, expected in [
            ([], ['access_revocation']),
            (['backlog:read'], ['access_revocation', 'skills_map', 'training']),
            (['backlog:read', 'project:roles:manage'], ['roles', 'access_revocation', 'skills_map', 'training']),
            (['backlog:read', 'project:teams:manage'], ['access_revocation', 'teams', 'skills_map', 'training']),
        ]:
            with self.subTest(permissions=extra):
                self.open_project(['project:read', 'project:members:read', 'project:members:manage', *extra])
                self.page.get_by_role('button', name='Recomendações', exact=True).click()
                select = self.page.get_by_label('Tipo de recomendação', exact=True)
                expect(select).to_be_visible()
                self.assertEqual(select.locator('option').evaluate_all('(options) => options.map(o => o.value)'), expected)

    def test_member_manager_can_reject_a_role_proposal_without_permission_to_approve_it(self):
        self.open_project(['project:read', 'project:members:manage', 'backlog:read'])
        self.page.get_by_role('button', name='Recomendações', exact=True).click()
        expect(self.page.get_by_role('button', name='Rejeitar recomendação', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Aprovar recomendação', exact=True)).to_have_count(0)

    def test_member_manager_without_context_read_can_only_review_existing_proposals(self):
        self.open_project(['project:read', 'project:members:manage', 'project:roles:manage', 'backlog:read'])
        self.page.get_by_role('button', name='Recomendações', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar recomendação', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Aprovar recomendação', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Rejeitar recomendação', exact=True)).to_be_visible()

    def test_archived_project_keeps_proposals_readable_and_rejectable(self):
        self.open_project(['project:read', 'project:members:read', 'project:members:manage',
                           'project:roles:manage', 'backlog:read'], archived=True)
        self.page.get_by_role('button', name='Recomendações', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar recomendação', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Aprovar recomendação', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Rejeitar recomendação', exact=True)).to_be_visible()
