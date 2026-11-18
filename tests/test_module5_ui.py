from playwright.sync_api import expect

from browser_support import BrowserCase


class Module5UiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def open_project(self, permissions=None, archived=False):
        self.evaluate('''async ({permissions, archived}) => {
          document.body.innerHTML = '<main id="main"></main>';
          const {createWorkspaceController} = await import('/scripts/workspace-controller.js');
          const {PlatformApiError} = await import('/scripts/api-errors.js');
          const project = {id:'project-a', name:'Projeto A', owner_id:'owner', archived,
            status:archived?'archived':'active', permissions:permissions ?? ['project:read']};
          window.otherProject = {...project,id:'project-b',name:'Projeto B'};
          window.calls = []; window.sessionKey = 'session-a'; window.signedOut = false;
          window.result = (artigos = [], overrides = {}) => ({
            enabled:true, artigos, total:artigos.length, categoria:'geral',
            fontes_consultadas:[], fontes_indisponiveis:[], truncated:false, ...overrides
          });
          window.article = (titulo, link = 'https://example.com/material', fonte = null) =>
            ({titulo,link,fonte,idioma:'pt',data_publicacao:'2026-11-18T12:00:00Z'});
          window.feed = result(); window.query = result(); window.signals = [];
          window.pendingSummaries = [];
          const projects = {request: async (method,path,token,body,options) => {
            calls.push({method,path,token,body,timeout:options.timeout});
            if (path.includes('/curation/')) {
              signals.push(options.signal);
              const post = method === 'POST';
              const kind = post ? window.queryError : window.feedError;
              if (kind) throw new PlatformApiError(kind);
              if (post && window.holdQuery) {
                return new Promise(resolve => {window.finishQuery = resolve;});
              }
              if (!post && window.holdFeed) {
                return new Promise(resolve => {window.finishFeed = resolve;});
              }
              const value = post ? query : feed;
              if (options.validate && !options.validate(value)) throw new PlatformApiError('invalid-response');
              return value;
            }
            if (path.endsWith('/summary')) {
              if (window.holdSummary) {
                return new Promise(resolve => {pendingSummaries.push({resolve, signal:options.signal});});
              }
              return {teams:[]};
            }
            if (path.includes('/recommendations?')) return {items:[
              {id:'training',kind:'training',status:'approved',summary:'Formação em testes',
                suggestions:[{user_id:'private-person-id',topics:['Testes de contrato','HTTP']}]},
              {id:'skills',kind:'skills_map',status:'approved',summary:'Mapa de competências',
                suggestions:[{user_id:'private-person-id',topics:['Tópico não relacionado']}]},
              {id:'empty',kind:'training',status:'approved',summary:'Treinamento sem tópicos',
                suggestions:[{user_id:'private-person-id',topics:[]}]}
            ]};
            return path.endsWith('/project-b') ? otherProject : project;
          }};
          window.workspace = createWorkspaceController({
            clients:{projects}, account:{accessToken:async()=> 'synthetic-token'},
            session:{getSessionId:()=>window.sessionKey}, getIdentity:()=>({id:'reader'}),
            onEnter:()=>{}, onBack:()=>{}, onUnauthorized:()=>{window.signedOut=true;}
          });
          await workspace.openProject(project);
        }''', {'permissions': permissions, 'archived': archived})

    @property
    def question(self):
        return self.page.get_by_label('Pergunta sobre tecnologia', exact=True)

    @property
    def search(self):
        return self.page.get_by_role('button', name='Buscar artigos', exact=True)

    def open_curation(self):
        entry = self.page.get_by_role('button', name='Curadoria', exact=True)
        expect(entry).to_be_visible()
        entry.click()
        expect(self.page.get_by_role('heading', name='Curadoria', exact=True)).to_be_visible()

    def curation_calls(self):
        return self.evaluate("()=>calls.filter(call=>call.path.includes('/curation/'))")

    def test_archived_reader_opens_feed_on_demand_and_sends_only_explicit_trimmed_question(self):
        self.open_project(archived=True)
        self.assertEqual(self.curation_calls(), [])
        self.open_curation()
        expect(self.page.get_by_text('Nenhum artigo disponível no feed.', exact=True)).to_be_visible()
        expect(self.question).to_be_editable()
        self.assertEqual([(row['method'], row['path']) for row in self.curation_calls()],
                         [('GET', '/projects/project-a/curation/feed')])
        self.question.fill('  Materiais de teste  ')
        self.assertEqual(len(self.curation_calls()), 1)
        self.search.click()
        expect(self.page.get_by_text('Nenhum artigo encontrado para esta pergunta.', exact=True)).to_be_visible()
        self.assertEqual(self.curation_calls()[-1], {
            'method': 'POST', 'path': '/projects/project-a/curation/queries',
            'token': 'synthetic-token', 'body': {'pergunta': 'Materiais de teste'}, 'timeout': 70000
        })

    def test_permission_controls_entry_and_feed_denial_blocks_form(self):
        self.open_project(['project:members:manage'])
        expect(self.page.get_by_role('button', name='Curadoria', exact=True)).to_have_count(0)
        self.assertEqual(self.curation_calls(), [])
        self.open_project()
        self.evaluate("()=>{window.feedError='forbidden';}")
        self.open_curation()
        expect(self.page.get_by_text('Você não tem permissão para acessar a curadoria deste projeto.')).to_be_visible()
        expect(self.search).to_have_count(0)

    def test_training_prefills_editable_focused_question_without_sending_it(self):
        self.open_project(['project:read', 'project:members:manage', 'project:members:read', 'backlog:read'])
        self.page.get_by_role('button', name='Recomendações', exact=True).click()
        materials = self.page.get_by_role('button', name='Buscar materiais de estudo', exact=True)
        expect(materials).to_have_count(1)
        self.assertEqual(self.curation_calls(), [])
        materials.click()
        expect(self.question).to_have_value('Quais materiais de estudo abordam Testes de contrato e HTTP?')
        expect(self.question).to_be_focused()
        expect(self.question).to_be_editable()
        self.assertEqual([row['method'] for row in self.curation_calls()], ['GET'])
        self.assertNotIn('private-person-id', self.question.input_value())

    def test_article_text_and_links_are_safe_and_partial_feed_is_explained(self):
        self.open_project()
        self.evaluate('''()=>{window.feed=result([
          article('<img src=x onerror=alert(1)>','https://example.com/artigo','<b>Fonte</b>'),
          article('Código', 'javascript:alert(1)'),
          article('Sem protocolo', '//example.com'),
          article('Com credencial', 'https://user@example.com'),
          article('Com controle', 'https://exam\\tple.com'),
          article('Com barra invertida', 'https://example.com\\\\@unsafe.example')
        ], {total:51,truncated:true,fontes_indisponiveis:['<i>Fonte ausente</i>']});}''')
        self.open_curation()
        link = self.page.get_by_role('link', name='<img src=x onerror=alert(1)>', exact=True)
        expect(link).to_have_attribute('href', 'https://example.com/artigo')
        expect(link).to_have_attribute('target', '_blank')
        expect(link).to_have_attribute('rel', 'noopener noreferrer')
        expect(self.page.locator('#workspace-content a')).to_have_count(1)
        expect(self.page.locator('#workspace-content img, #workspace-content b, #workspace-content i')).to_have_count(0)
        expect(self.page.get_by_text('<b>Fonte</b>', exact=False)).to_be_visible()
        expect(self.page.get_by_text('de 51 artigos', exact=False)).to_be_visible()
        expect(self.page.get_by_text('Fontes indisponíveis', exact=False)).to_contain_text('<i>Fonte ausente</i>')

    def test_disabled_and_unavailable_feed_have_distinct_states(self):
        self.open_project()
        self.evaluate('()=>{window.feed=result([], {enabled:false});}')
        self.open_curation()
        expect(self.page.get_by_text('A curadoria está desativada.', exact=True)).to_be_visible()
        expect(self.search).to_have_count(0)
        self.page.get_by_role('button', name='Contexto', exact=True).click()
        self.evaluate("()=>{window.feedError='unavailable';}")
        self.open_curation()
        expect(self.page.get_by_text('O feed está indisponível no momento.', exact=True)).to_be_visible()

    def test_invalid_question_never_posts_and_request_is_not_repeated_on_failure(self):
        self.open_project()
        self.open_curation()
        self.question.fill('   ')
        self.search.click()
        expect(self.page.get_by_text('Digite uma pergunta de 1 a 2.000 caracteres.', exact=True)).to_be_visible()
        self.evaluate("()=>{const field=document.querySelector('#curation-pergunta');field.value='a'.repeat(2001);}")
        self.search.click()
        expect(self.page.get_by_text('Digite uma pergunta de 1 a 2.000 caracteres.', exact=True)).to_be_visible()
        self.assertEqual([row['method'] for row in self.curation_calls()], ['GET'])
        self.evaluate('()=>{window.holdQuery=true;}')
        self.question.fill('Qual artigo devo ler?')
        self.search.click()
        self.page.wait_for_function('Boolean(window.finishQuery)')
        expect(self.page.get_by_text('Buscando artigos…', exact=True)).to_be_visible()
        self.evaluate('''()=>{const form=document.querySelector('#curation-pergunta').form;
          form.requestSubmit(); window.finishQuery({unexpected:true});}''')
        expect(self.page.get_by_text('A consulta pode ter sido registrada', exact=False)).to_be_visible()
        expect(self.question).to_have_value('Qual artigo devo ler?')
        self.assertEqual([row['method'] for row in self.curation_calls()], ['GET', 'POST'])
        self.evaluate("()=>{window.queryError='timeout';}")
        self.search.click()
        expect(self.page.get_by_text('A consulta pode ter sido registrada', exact=False)).to_be_visible()
        self.assertEqual([row['method'] for row in self.curation_calls()], ['GET', 'POST', 'POST'])

    def test_navigation_aborts_pending_feed_and_discards_late_results_for_another_project(self):
        self.open_project()
        self.evaluate('()=>{window.holdFeed=true;}')
        self.open_curation()
        expect(self.page.get_by_text('Carregando feed…', exact=True)).to_be_visible()
        self.page.wait_for_function('Boolean(window.finishFeed)')
        self.page.get_by_role('button', name='Contexto', exact=True).click()
        expect(self.page.get_by_text('Carregando feed…', exact=True)).to_have_count(0)
        self.evaluate('''async ()=>{await workspace.openProject(otherProject);
          window.finishFeed(result([article('Resultado do projeto anterior')]));}''')
        self.assertTrue(self.evaluate('()=>signals[0].aborted'))
        expect(self.page.get_by_role('heading', name='Projeto B', exact=True)).to_be_visible()
        expect(self.page.get_by_text('Resultado do projeto anterior', exact=True)).to_have_count(0)

    def test_curation_releases_context_loading_and_late_context_cannot_unlock_a_new_load(self):
        self.open_project()
        workspace = self.page.locator('#workspace-view')
        back = self.page.get_by_role('button', name='Voltar para projetos', exact=True)
        context = self.page.get_by_role('button', name='Contexto', exact=True)
        self.evaluate('()=>{window.holdSummary=true;window.holdFeed=true;}')
        context.click()
        self.page.wait_for_function('window.pendingSummaries.length === 1')
        expect(workspace).to_have_attribute('aria-busy', 'true')
        expect(back).to_be_disabled()

        self.open_curation()
        self.page.wait_for_function('Boolean(window.finishFeed)')
        expect(self.page.get_by_text('Carregando feed…', exact=True)).to_be_visible()
        self.assertTrue(self.evaluate('()=>pendingSummaries[0].signal.aborted'))
        expect(workspace).to_have_attribute('aria-busy', 'false')
        expect(back).to_be_enabled()
        self.evaluate("()=>{window.finishFeed(result());}")
        expect(self.question).to_be_editable()
        expect(workspace).to_have_attribute('aria-busy', 'false')
        expect(back).to_be_enabled()

        context.click()
        self.page.wait_for_function('window.pendingSummaries.length === 2')
        self.evaluate('''async ()=>{
          pendingSummaries[0].resolve({teams:[{name:'Equipe de resposta obsoleta'}]});
          await new Promise(resolve=>requestAnimationFrame(resolve));
        }''')
        expect(workspace).to_have_attribute('aria-busy', 'true')
        expect(back).to_be_disabled()
        self.evaluate("()=>{pendingSummaries[1].resolve({teams:[{name:'Equipe atual'}]});}")
        expect(self.page.get_by_text('Equipe atual', exact=True)).to_be_visible()
        expect(self.page.get_by_text('Equipe de resposta obsoleta', exact=True)).to_have_count(0)
        expect(workspace).to_have_attribute('aria-busy', 'false')
        expect(back).to_be_enabled()

    def test_session_change_discards_an_in_flight_query_result(self):
        self.open_project()
        self.open_curation()
        self.evaluate('()=>{window.holdQuery=true;}')
        self.question.fill('Materiais de teste')
        self.search.click()
        self.page.wait_for_function('Boolean(window.finishQuery)')
        self.evaluate('''async ()=>{
          window.sessionKey='session-b';
          window.finishQuery(result([article('Resultado da sessão anterior')]));
          await new Promise(resolve=>requestAnimationFrame(resolve));
        }''')
        expect(self.page.get_by_text('Resultado da sessão anterior', exact=True)).to_have_count(0)
        self.evaluate('''async ()=>{workspace.clear(); await workspace.openProject(otherProject);}''')
        expect(self.page.get_by_role('heading', name='Projeto B', exact=True)).to_be_visible()
        expect(self.page.get_by_text('Resultado da sessão anterior', exact=True)).to_have_count(0)
        self.assertEqual([row['method'] for row in self.curation_calls()], ['GET', 'POST'])

    def test_unauthorized_query_ends_session_without_repeating_post(self):
        self.open_project()
        self.open_curation()
        self.evaluate("()=>{window.queryError='unauthorized';}")
        self.question.fill('Materiais de teste')
        self.search.click()
        expect(self.page.locator('#workspace-view')).to_be_hidden()
        self.assertTrue(self.evaluate('()=>window.signedOut'))
        self.assertEqual([row['method'] for row in self.curation_calls()], ['GET', 'POST'])
