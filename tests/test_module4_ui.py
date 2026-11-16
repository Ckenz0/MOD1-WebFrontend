from playwright.sync_api import expect

from browser_support import BrowserCase


class Module4UiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def open_item(self, permissions=None, enabled=True, archived=False):
        self.evaluate('''async ({permissions, enabled, archived}) => {
          document.body.innerHTML = '<main id="main"></main>';
          const {createWorkspaceController} = await import('/scripts/workspace-controller.js');
          const project = {id:'project-a', owner_id:'owner-a', name:'Revisões', status:'active', archived,
            permissions:permissions || ['project:read','backlog:read','backlog:update_status']};
          window.calls=[]; window.records=[]; window.failPost=false; window.failList=false;
          window.item={id:'item-a', project_id:'project-a', title:'Validar código', kind:'story', status:'todo', version:3};
          window.sessionKey='session-a';
          const backlog = {request:async (method,path,token,body,options)=>{
            window.calls.push({method,path,body,timeout:options.timeout});
            if(path.includes('/code-reviews')) {
              if(method==='POST') {
                if(window.failPost) {const e=new Error('Conexão interrompida');e.kind='network';throw e;}
                if(window.conflictMode==='before') {
                  window.conflictMode=false;window.item={...window.item,version:4};
                  const e=new Error('Versão alterada');e.kind='conflict';throw e;
                }
                const row={id:'22222222-2222-4222-8222-222222222222',request_id:body.request_id,
                  project_id:'project-a',item_id:'item-a',status:'succeeded',
                  created_at:'2026-11-16T12:00:00Z',updated_at:'2026-11-16T12:00:01Z',
                  source:{kind:body.pr_url?'pull_request':'files',pr_url:body.pr_url,files:body.arquivos?.map(f=>f.caminho)||[]},
                  arquitetura:body.arquitetura,usar_ia:body.usar_ia,status_effect:'started',item_version:4,error:null,
                  result:{id:'33333333-3333-4333-8333-333333333333',criado_em:'2026-11-16T12:00:00Z',
                    arquitetura:'multicamadas',arquivos:1,achados:[{arquivo:'demo.py',linha:1,categoria:'Estilo',gravidade:'baixa',titulo:'<img src=x onerror=alert(1)>',sugestao:'Revisar nome'}],
                    testes:[],testes_executados:false,pr:null,ia:{status:'disabled',texto:'<script>bad()</script>'},markdown:'# Relatório <b>seguro</b>'}};
                window.records.push(row);window.item={...window.item,status:'in_progress',version:4};
                if(window.conflictMode==='after') {window.conflictMode=false;const e=new Error('Conflito após análise');e.kind='conflict';throw e;}
                return row;
              }
              if(window.failList) throw new Error('Consulta indisponível');
              const offset=Number(new URL(path,'http://local').searchParams.get('offset')||0);
              return {items:window.records.slice(offset,offset+20),total:window.records.length,limit:20,offset,enabled};
            }
            if(path.endsWith('/board')) return {version:1,columns:{todo:[],in_progress:[],done:[]}};
            if(path.includes('/items?')) return {items:[window.item],total:1,limit:100,offset:0};
            if(path.endsWith('/dependencies') || path.includes('/history?')) return {items:[],total:0};
            if(path.endsWith('/items/item-a')) return window.item;
            throw new Error('Unexpected request '+path);
          }};
          window.workspace=createWorkspaceController({clients:{backlog, projects:{request:async()=>window.revokeReviewPermission
            ? {...project,permissions:['project:read','backlog:read']} : project}}, account:{accessToken:async()=> 'synthetic-token'},
            session:{getSessionId:()=>window.sessionKey},getIdentity:()=>({id:'member-a'}),onEnter:()=>{},onBack:()=>{},onUnauthorized:()=>{}});
          await window.workspace.openProject(project,'board');
        }''', {'permissions': permissions, 'enabled': enabled, 'archived': archived})
        self.page.get_by_role('table', name='Itens do projeto').get_by_role('button', name='Validar código', exact=True).click()
        expect(self.page.locator('#workspace-view')).to_have_attribute('aria-busy', 'false')

    def open_reviews(self):
        self.page.get_by_role('button', name='Revisões de código', exact=True).click()
        expect(self.page.get_by_role('heading', name='Revisões de código', exact=True)).to_be_visible()

    def test_reader_opens_only_item_scoped_history_on_demand(self):
        self.open_item(['project:read', 'backlog:read'])
        self.assertFalse(self.evaluate("()=>calls.some(c=>c.path.includes('code-reviews'))"))
        self.open_reviews()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        expect(self.page.get_by_text('Nenhuma revisão registrada para este item.', exact=True)).to_be_visible()
        self.assertEqual(self.evaluate("()=>calls.filter(c=>c.path.includes('code-reviews')).map(c=>c.path)"),
                         ['/projects/project-a/items/item-a/code-reviews?limit=20&offset=0'])

    def test_disabled_or_archived_project_keeps_history_without_form(self):
        for enabled, archived in [(False, False), (True, True)]:
            self.open_item(enabled=enabled, archived=archived)
            self.open_reviews()
            expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)

    def test_valid_upload_uses_version_and_explicit_ai_and_renders_safe_result(self):
        self.open_item(); self.open_reviews()
        expect(self.page.get_by_label('Usar IA nesta revisão', exact=True)).not_to_be_checked()
        self.page.get_by_label('Arquivos Python', exact=True).set_input_files({'name':'demo.py','mimeType':'text/x-python','buffer':b'print(1)\n'})
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        expect(self.page.get_by_text('<img src=x onerror=alert(1)>', exact=True)).to_be_visible()
        expect(self.page.get_by_text('# Relatório <b>seguro</b>', exact=True)).to_be_visible()
        expect(self.page.locator('#workspace-content img, #workspace-content script')).to_have_count(0)
        payload = self.evaluate("()=>calls.find(c=>c.method==='POST').body")
        self.assertEqual(payload['expected_version'], 3)
        self.assertEqual(payload['arquivos'], [{'caminho':'demo.py','conteudo':'print(1)\n'}])
        self.assertEqual(payload['arquitetura'], 'multicamadas')
        self.assertFalse(payload['usar_ia'])
        self.assertRegex(payload['request_id'], r'^[a-f0-9-]{36}$')
        self.assertEqual(self.evaluate("()=>calls.find(c=>c.method==='POST').timeout"), 75000)
        self.assertTrue(self.evaluate("()=>calls.filter(c=>c.path.endsWith('/items/item-a')).length>=3"))

    def test_ambiguous_failure_retains_request_id_and_never_automatically_posts(self):
        self.open_item(); self.open_reviews()
        self.evaluate('()=>{window.failPost=true;window.failList=true;}')
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.get_by_text('Resultado incerto. Consulte o histórico antes de solicitar outra análise.', exact=True)).to_be_visible()
        request_id = self.evaluate("()=>calls.find(c=>c.method==='POST').body.request_id")
        expect(self.page.get_by_text(request_id, exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Nova análise mesmo com risco de duplicidade', exact=True)).to_have_count(0)
        self.evaluate('()=>{window.failList=false;}')
        self.page.get_by_role('button', name='Atualizar revisões', exact=True).click()
        expect(self.page.get_by_role('button', name='Nova análise mesmo com risco de duplicidade', exact=True)).to_be_visible()
        self.assertEqual(self.evaluate("()=>calls.filter(c=>c.method==='POST').length"), 1)
        self.page.get_by_role('button', name='Nova análise mesmo com risco de duplicidade', exact=True).click()
        self.evaluate('()=>{window.failPost=false;}')
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        self.assertNotEqual(request_id, self.evaluate("()=>calls.filter(c=>c.method==='POST')[1].body.request_id"))

    def test_session_change_during_file_read_prevents_post(self):
        self.open_item(); self.open_reviews()
        self.page.get_by_label('Arquivos Python', exact=True).set_input_files({'name':'demo.py','mimeType':'text/x-python','buffer':b'print(1)'})
        self.evaluate("()=>{File.prototype.text=async function(){window.sessionKey='session-b';return 'print(1)';}}")
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        self.assertFalse(self.evaluate("()=>calls.some(c=>c.method==='POST')"))

    def test_invalid_file_or_two_sources_never_send_code(self):
        self.open_item(); self.open_reviews()
        self.page.get_by_label('Arquivos Python', exact=True).set_input_files({'name':'demo.js','mimeType':'text/javascript','buffer':b'print(1)'})
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('arquivos .py')
        self.assertFalse(self.evaluate("()=>calls.some(c=>c.method==='POST')"))
        self.page.get_by_label('Arquivos Python', exact=True).set_input_files({'name':'demo.py','mimeType':'text/x-python','buffer':b'print(1)'})
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.locator('#workspace-status')).to_contain_text('apenas uma origem')
        self.assertFalse(self.evaluate("()=>calls.some(c=>c.method==='POST')"))

    def test_navigation_while_reading_upload_cancels_post(self):
        self.open_item(); self.open_reviews()
        self.page.get_by_label('Arquivos Python', exact=True).set_input_files({'name':'demo.py','mimeType':'text/x-python','buffer':b'print(1)'})
        self.evaluate("()=>{File.prototype.text=()=>new Promise(resolve=>{window.finishRead=resolve;});}")
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        self.page.wait_for_function('window.finishRead !== undefined')
        self.evaluate("()=>{window.workspace.clear();window.finishRead('print(1)');}")
        expect(self.page.locator('#workspace-view')).to_be_hidden()
        self.assertFalse(self.evaluate("()=>calls.some(c=>c.method==='POST')"))

    def test_pending_record_requires_explicit_duplicate_warning_before_new_form(self):
        self.open_item(); self.open_reviews()
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        self.evaluate("()=>{window.records[0]={...window.records[0],status:'pending',result:null,status_effect:'not_applied_error'};}")
        self.page.get_by_role('button', name='Atualizar revisões', exact=True).click()
        expect(self.page.get_by_role('heading', name='Em processamento', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        self.page.get_by_role('button', name='Nova análise mesmo com risco de duplicidade', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_be_visible()
        self.assertEqual(self.evaluate("()=>calls.filter(c=>c.method==='POST').length"), 1)

    def test_current_project_permission_is_refreshed_before_review_form(self):
        self.open_item()
        self.evaluate("()=>{window.revokeReviewPermission=true;}")
        self.open_reviews()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)

    def test_persisted_terminal_review_after_conflict_refreshes_and_uses_new_request_id(self):
        self.open_item(); self.open_reviews()
        self.evaluate("()=>{window.conflictMode='after';}")
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_be_enabled()
        self.assertEqual(self.evaluate("()=>calls.filter(c=>c.method==='POST').length"), 1)
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/2')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        self.page.wait_for_function("calls.filter(c=>c.method==='POST').length===2")
        first, second = self.evaluate("()=>calls.filter(c=>c.method==='POST').map(c=>c.body)")
        self.assertNotEqual(first['request_id'], second['request_id'])
        self.assertEqual(second['expected_version'], 4)

    def test_stale_version_conflict_before_provider_refreshes_and_allows_new_valid_attempt(self):
        self.open_item(); self.open_reviews()
        self.evaluate("()=>{window.conflictMode='before';}")
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        self.page.wait_for_function("calls.some((c,i)=>c.method==='POST'&&calls.slice(i+1).some(n=>n.path.includes('code-reviews')&&n.method==='GET'))")
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        self.page.get_by_role('button', name='Nova análise mesmo com risco de duplicidade', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_be_enabled()
        self.assertEqual(self.evaluate("()=>calls.filter(c=>c.method==='POST').length"), 1)
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        first, second = self.evaluate("()=>calls.filter(c=>c.method==='POST').map(c=>c.body)")
        self.assertNotEqual(first['request_id'], second['request_id'])
        self.assertEqual(second['expected_version'], 4)

    def test_pagination_preserves_known_pending_warning_and_never_opens_unacknowledged_form(self):
        self.open_item(); self.open_reviews()
        self.page.get_by_label('URL do Pull Request', exact=True).fill('https://github.com/example/demo/pull/1')
        self.page.get_by_role('button', name='Solicitar revisão', exact=True).click()
        expect(self.page.get_by_text('Item iniciado; conclusão manual.', exact=True)).to_be_visible()
        self.evaluate("""()=>{
          const template=window.records[0];
          window.records=Array.from({length:21},(_,i)=>({...template,
            request_id:'11111111-1111-4111-8111-'+String(i).padStart(12,'0'),
            status:i===0?'pending':'succeeded',result:i===0?null:template.result}));
        }""")
        self.page.get_by_role('button', name='Atualizar revisões', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        self.page.get_by_role('button', name='Próxima página', exact=True).click()
        expect(self.page.get_by_role('button', name='Página anterior', exact=True)).to_be_visible()
        expect(self.page.get_by_text('Resultado incerto. Consulte o histórico antes de solicitar outra análise.', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        self.page.get_by_role('button', name='Página anterior', exact=True).click()
        expect(self.page.get_by_role('button', name='Solicitar revisão', exact=True)).to_have_count(0)
        self.assertEqual(self.evaluate("()=>calls.filter(c=>c.method==='POST').length"), 1)


class Module4DomainTests(BrowserCase):
    def setUp(self):
        super().setUp(); self.page.goto(self.base_url + '/__test__/')

    def test_source_byte_limits_paths_and_architecture_are_validated(self):
        result = self.evaluate('''async()=>{
          const {module4Draft}=await import('/scripts/module4-domain.js');
          const base={request_id:'11111111-1111-4111-8111-111111111111',expected_version:3,arquitetura:'multicamadas',usar_ia:false};
          const errors=[];
          for(const change of [{},{pr_url:'http://github.com/a/b/pull/1'},{pr_url:'https://github.com/a/b/pull/1?x=1'},
            {arquivos:[{caminho:'../a.py',conteudo:'a'}]},{arquivos:[{caminho:'a.js',conteudo:'a'}]},
            {arquivos:[{caminho:'a.py',conteudo:'á'.repeat(50001)}]},
            {arquivos:[{caminho:'a.py',conteudo:'a'},{caminho:'a.py',conteudo:'b'}]},
            {arquivos:Array.from({length:21},(_,i)=>({caminho:i+'.py',conteudo:''}))},
            {pr_url:'https://github.com/a/b/pull/1',arquivos:[{caminho:'a.py',conteudo:'a'}]},
            {pr_url:'https://github.com/a/b/pull/1',arquitetura:'unknown'}]) {
              try{module4Draft({...base,...change});errors.push(false)}catch{errors.push(true)}
          }
          return {errors,value:module4Draft({...base,arquivos:[{caminho:'a.py',conteudo:'á'.repeat(50000)}]})};
        }''')
        self.assertTrue(all(result['errors']))
        self.assertEqual(len(result['value']['arquivos'][0]['conteudo']), 50000)
