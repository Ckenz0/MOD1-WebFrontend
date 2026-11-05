"""Human decisions and honest empty/error states for backend Gemini proposals."""

from playwright.sync_api import expect

from browser_support import BrowserCase


class GeminiRecommendationsUiTests(BrowserCase):
    pid = '55555555-5555-4555-8555-555555555555'
    rid = '66666666-6666-4666-8666-666666666666'
    member = '77777777-7777-4777-8777-777777777777'

    def setUp(self):
        super().setUp()
        self.mock_auth()
        self.page.route('**/auth/logout', lambda route: route.fulfill(status=204))
        self.page.route('**/auth/session/activity', lambda route: route.fulfill(json={
            'idle_expires_at': '2099-01-01T00:00:00Z', 'absolute_expires_at': '2099-01-01T01:00:00Z'}))
        project = {'id': self.pid, 'owner_id': self.identity['id'], 'name': 'Projeto Gemini de teste',
            'description': 'Dados fictícios', 'objective': '', 'created_at': '2026-11-03T12:00:00Z',
            'permissions': [], 'status': 'active', 'version': 1, 'archived': False}
        self.page.route('**/projects?*', lambda route: route.fulfill(json={
            'items': [project], 'total': 1, 'limit': 20, 'offset': 0}))
        self.page.route('**/projects/' + self.pid, lambda route: route.fulfill(json=project))
        self.page.route('**/projects/' + self.pid + '/summary', lambda route: route.fulfill(json={
            'project': project, 'teams': [], 'backlog_available': False, 'backlog': None}))
        self.base = '**/projects/' + self.pid + '/recommendations'
        self.page.route(self.base + '?*', lambda route: route.fulfill(json={
            'items': [], 'total': 0, 'limit': 20, 'offset': 0}))
        self.page.goto(self.base_url)
        self.login()
        expect(self.page.locator('#profile-view')).to_be_visible()
        self.page.get_by_role('button', name='Meus projetos', exact=True).click()
        self.page.get_by_role('button', name=project['name'], exact=True).click()
        self.page.get_by_role('button', name='Gerenciar projeto e planejamento', exact=True).click()
        self.page.get_by_role('button', name='Recomendações', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar recomendação', exact=True)).to_be_enabled()

    def proposal(self, suggestions=None, **extra):
        return {'id': self.rid, 'kind': 'roles', 'status': 'pending', 'version': 1,
            'summary': 'Revisar acesso de desenvolvimento',
            'justification': 'As tarefas fictícias exigem consulta e atualização do andamento.',
            'provider': 'gemini', 'model': 'gemini-3.5-flash-lite', 'simulated': False,
            'created_at': '2026-11-03T12:00:00Z', 'evidence': ['project:' + self.pid],
            'suggestions': suggestions if suggestions is not None else [
                {'user_id': self.member, 'roles': ['developer']}], **extra}

    def test_gemini_proposal_has_readable_roles_and_requires_explicit_approval(self):
        proposal = self.proposal()
        writes, generations = [], []
        def generate(route):
            generations.append(route.request.post_data_json)
            route.fulfill(status=201, json=proposal)
        self.page.route(self.base, generate)
        def approve(route):
            writes.append(route.request.post_data_json)
            route.fulfill(json={**proposal, 'status': 'approved', 'version': 2})
        self.page.route(self.base + '/' + self.rid + '/approve', approve)
        expect(self.page.locator('#workspace-content')).to_contain_text('contexto autorizado')
        expect(self.page.get_by_label('Tipo de recomendação', exact=True)).to_have_value('roles')
        self.page.get_by_role('button', name='Solicitar recomendação', exact=True).click()
        content = self.page.locator('#workspace-content')
        expect(content).to_contain_text('Google Gemini')
        expect(content).to_contain_text('gemini-3.5-flash-lite')
        expect(content).to_contain_text('Desenvolvedor')
        expect(content).not_to_contain_text('Nenhuma recomendação registrada.')
        self.assertEqual(generations, [{'kind': 'roles', 'constraints': {}}])
        self.assertEqual(writes, [])
        self.page.get_by_role('button', name='Aprovar recomendação', exact=True).click()
        expect(content).to_contain_text('Aprovada')
        self.assertEqual(writes, [{'expected_version': 1}])

    def test_empty_analysis_cannot_be_applied_and_can_be_dismissed(self):
        proposal = self.proposal([], summary='Sem alterações sugeridas',
            justification='Não há evidência suficiente para propor mudanças.')
        approvals, rejections, generations = [], [], []
        def generate(route):
            generations.append(route.request.post_data_json)
            route.fulfill(status=201, json=proposal)
        self.page.route(self.base, generate)
        self.page.route(self.base + '/' + self.rid + '/approve', lambda route: (
            approvals.append(route.request.post_data_json), route.fulfill(status=409)))
        def reject(route):
            rejections.append(route.request.post_data_json)
            route.fulfill(json={**proposal, 'status': 'rejected', 'version': 2})
        self.page.route(self.base + '/' + self.rid + '/reject', reject)
        self.page.get_by_label('Tipo de recomendação', exact=True).select_option('teams')
        expect(self.page.get_by_label('Foco da formação de equipe', exact=True)).to_have_value('availability')
        self.page.get_by_role('button', name='Solicitar recomendação', exact=True).click()
        content = self.page.locator('#workspace-content')
        expect(content).to_contain_text('Esta análise não trouxe sugestões aplicáveis')
        expect(content).not_to_contain_text('Nenhuma recomendação registrada.')
        expect(self.page.get_by_label('Tipo de recomendação', exact=True)).to_have_value('teams')
        self.assertEqual(generations, [{'kind': 'teams', 'constraints': {'preference': 'availability'}}])
        expect(self.page.get_by_role('button', name='Aprovar recomendação', exact=True)).to_have_count(0)
        self.page.get_by_role('button', name='Dispensar análise', exact=True).click()
        expect(content).to_contain_text('Rejeitada')
        self.assertEqual(approvals, [])
        self.assertEqual(rejections, [{'expected_version': 1}])

    def test_provider_failure_keeps_workspace_and_never_offers_fake_proposal(self):
        requests = []
        def fail(route):
            requests.append(route.request.post_data_json)
            route.fulfill(status=503, json={'detail': 'Recommendation provider unavailable'})
        self.page.route(self.base, fail)
        self.page.get_by_role('button', name='Solicitar recomendação', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_be_visible()
        expect(self.page.get_by_role('button', name='Solicitar recomendação', exact=True)).to_be_enabled()
        expect(self.page.locator('#workspace-title')).to_contain_text('Projeto Gemini de teste')
        expect(self.page.locator('#workspace-content')).to_contain_text('Nenhuma recomendação registrada.')
        expect(self.page.get_by_role('button', name='Aprovar recomendação', exact=True)).to_have_count(0)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['kind'], 'roles')

    def test_model_text_is_displayed_as_text_and_does_not_execute_html(self):
        unsafe = '<img src=x onerror="window.geminiExecuted=true">'
        proposal = self.proposal(summary=unsafe, justification=unsafe)
        self.page.route(self.base, lambda route: route.fulfill(status=201, json=proposal))
        self.page.get_by_role('button', name='Solicitar recomendação', exact=True).click()
        expect(self.page.locator('#workspace-content')).to_contain_text(unsafe)
        expect(self.page.locator('#workspace-content img')).to_have_count(0)
        self.assertTrue(self.page.evaluate('window.geminiExecuted === undefined'))
