from playwright.sync_api import expect

from browser_support import BrowserCase


class Module3UiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def open_project(self, permissions=None, linked=7):
        self.evaluate('''async ({permissions,linked}) => {
          document.body.innerHTML='<main id="main"></main>';
          const {createWorkspaceController}=await import('/scripts/workspace-controller.js');
          const {PlatformApiError}=await import('/scripts/api-errors.js');
          const project={id:'project-a',name:'Projeto A',owner_id:'owner',status:'active',
            module3_project_id:linked,permissions:permissions ?? ['project:read','project:update']};
          window.calls=[];window.downloadCalls=[];window.createdBlobs=[];window.savedFiles=[];
          window.signals=[];window.sessionKey='session-a';window.signedOut=false;
          window.rows=[{id:41,project_id:7,name:'Requisitos.md',artifact_type:'MARKDOWN',version:1,
            created_at:'2026-11-24T00:00:00Z'}];
          window.artifactPage=()=>({enabled:true,module3_project_id:project.module3_project_id,
            items:project.module3_project_id ? rows : [],total:project.module3_project_id ? rows.length : 0,truncated:false});
          const original=HTMLAnchorElement.prototype.click;
          HTMLAnchorElement.prototype.click=function(){
            if(this.download) savedFiles.push({name:this.download,url:this.href});
            else original.call(this);
          };
          URL.createObjectURL=blob=>{createdBlobs.push(blob.size);return 'blob:test-download';};
          URL.revokeObjectURL=url=>{window.revokedUrl=url;};
          const clients={projects:{
            request:async(method,path,token,body,options={})=>{
              calls.push({method,path,token,body});
              if(path.includes('/artifacts')) {
                signals.push(options.signal);
                if(window.holdArtifacts) return new Promise(resolve=>{window.finishArtifacts=resolve;});
                if(window.artifactsError) throw new PlatformApiError(artifactsError);
                let result=path.endsWith('/catalog') ? {enabled:true,items:[{id:7,name:'Projeto remoto',description:null}],total:1,truncated:false}
                  :path.includes('/versions?') ? {module3_project_id:7,artifact_id:41,items:[{id:81,artifact_id:41,version_number:1,created_at:'2026-11-24T00:00:00Z'}],total:1,truncated:false}
                  :artifactPage();
                if(options.validate && !options.validate(result)) throw new PlatformApiError('invalid-response');
                return result;
              }
              if(method==='PATCH') {project.module3_project_id=body.module3_project_id;return {...project};}
              if(path.endsWith('/summary')) return {teams:[]};
              return {...project};
            },
            download:async(path,token,options={})=>{
              downloadCalls.push({path,token});signals.push(options.signal);
              if(window.downloadError) throw new PlatformApiError(downloadError);
              if(window.holdDownload) return new Promise(resolve=>{window.finishDownload=resolve;});
              return new Blob(['# Requisitos'],{type:'application/octet-stream'});
            }
          }};
          window.workspace=createWorkspaceController({clients,
            account:{accessToken:async()=> 'synthetic-token'},session:{getSessionId:()=>sessionKey},
            getIdentity:()=>({id:'reader'}),onEnter:()=>{},onBack:()=>{},onUnauthorized:()=>{signedOut=true;}});
          window.otherProject={...project,id:'project-b',name:'Projeto B'};
          await workspace.openProject(project);
        }''', {'permissions': permissions, 'linked': linked})

    def open_artifacts(self):
        self.page.get_by_role('button', name='Artefatos', exact=True).click()
        expect(self.page.get_by_role('heading', name='Artefatos', exact=True)).to_be_visible()

    def test_manager_explicitly_selects_and_links_project_without_automatic_matching(self):
        self.open_project(linked=None)
        self.open_artifacts()
        expect(self.page.get_by_text('Nenhum projeto do Módulo 3 vinculado.', exact=True)).to_be_visible()
        self.assertFalse(self.evaluate("()=>calls.some(c=>c.path.endsWith('/catalog'))"))
        self.page.get_by_role('button', name='Escolher projeto', exact=True).click()
        self.page.get_by_label('Projeto do Módulo 3', exact=True).select_option('7')
        self.page.get_by_role('button', name='Vincular projeto', exact=True).click()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_be_visible()
        patch = self.evaluate("()=>calls.filter(c=>c.method==='PATCH')")
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]['body'], {'module3_project_id': 7})
        self.assertTrue(all(row['path'].startswith('/projects/project-a')
                            for row in self.evaluate('()=>calls')))

    def test_reader_filters_lists_versions_and_explicitly_downloads_current_file(self):
        self.open_project(['project:read'])
        self.open_artifacts()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Escolher projeto', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Desvincular projeto', exact=True)).to_have_count(0)
        self.page.get_by_label('Pesquisar arquivos', exact=True).fill('Requisitos')
        self.page.get_by_label('Tipo de arquivo', exact=True).select_option('MARKDOWN')
        self.page.get_by_role('button', name='Filtrar arquivos', exact=True).click()
        self.page.get_by_role('button', name='Versões', exact=True).click()
        expect(self.page.get_by_text('Versão 1', exact=False)).to_be_visible()
        self.page.get_by_role('button', name='Baixar versão atual', exact=True).click()
        self.page.wait_for_function('savedFiles.length===1')
        self.assertEqual(self.evaluate('()=>savedFiles[0].name'), 'artifact-41.md')
        self.assertTrue(all(row['method'] == 'GET' for row in self.evaluate('()=>calls')))
        self.assertNotIn('synthetic-token', self.evaluate('()=>downloadCalls[0].path'))

    def test_provider_failure_preserves_session_and_offer_retry(self):
        self.open_project(['project:read'])
        self.evaluate("()=>{window.artifactsError='unavailable';}")
        self.open_artifacts()
        expect(self.page.get_by_text('Os artefatos estão indisponíveis no momento.', exact=True)).to_be_visible()
        expect(self.page.get_by_role('button', name='Tentar novamente', exact=True)).to_be_visible()
        self.assertFalse(self.evaluate('()=>signedOut'))

    def test_stale_download_after_project_change_creates_no_blob_or_file(self):
        self.open_project(['project:read'])
        self.open_artifacts()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_be_visible()
        self.evaluate('()=>{window.holdDownload=true;}')
        self.page.get_by_role('button', name='Baixar versão atual', exact=True).click()
        self.page.wait_for_function('typeof finishDownload==="function"')
        self.evaluate('''async()=>{
          await workspace.openProject(otherProject);
          finishDownload(new Blob(['private old file']));
        }''')
        self.page.wait_for_timeout(80)
        self.assertEqual(self.evaluate('()=>savedFiles.length'), 0)
        self.assertEqual(self.evaluate('()=>createdBlobs.length'), 0)
        self.assertTrue(self.evaluate('()=>signals[signals.length-1].aborted'))

    def test_reader_without_project_permission_has_no_entry(self):
        self.open_project(['project:members:manage'])
        expect(self.page.get_by_role('button', name='Artefatos', exact=True)).to_have_count(0)

    def test_mobile_file_actions_fit_without_horizontal_scrolling(self):
        self.page.set_viewport_size({'width': 390, 'height': 1100})
        for name in ['tokens', 'app', 'workspace', 'premium']:
            self.page.add_style_tag(url=self.base_url + '/styles/' + name + '.css')
        self.open_project(['project:read'])
        self.open_artifacts()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_be_visible()
        self.page.locator('#workspace-content').scroll_into_view_if_needed()
        expect(self.page.get_by_role('button', name='Baixar versão atual', exact=True)).to_be_in_viewport(ratio=.99)

    def test_denied_version_read_clears_previous_artifact_metadata(self):
        self.open_project()
        self.open_artifacts()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_be_visible()
        self.evaluate("()=>{window.artifactsError='not-found';}")
        self.page.get_by_role('button', name='Versões', exact=True).click()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Escolher projeto', exact=True)).to_have_count(0)

    def test_failed_download_finishes_loading_state(self):
        self.open_project(['project:read'])
        self.open_artifacts()
        expect(self.page.get_by_text('Requisitos.md', exact=True)).to_be_visible()
        self.evaluate("()=>{window.downloadError='unavailable';}")
        self.page.get_by_role('button', name='Baixar versão atual', exact=True).click()
        expect(self.page.get_by_text('Não foi possível baixar o arquivo. Tente novamente.', exact=True)).to_be_visible()
        expect(self.page.get_by_text('Preparando o arquivo para download…', exact=True)).to_have_count(0)


class ArtifactBinaryClientTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_binary_download_uses_authorized_get_without_token_in_url(self):
        result = self.evaluate('''async()=>{
          const {createPlatformClient}=await import('/scripts/platform-api.js');
          const calls=[];
          const api=createPlatformClient({baseUrl:'https://projects.example',fetchImpl:async(url,options)=>{
            calls.push({url,method:options.method,headers:options.headers,credentials:options.credentials});
            return new Response('# Requisitos',{headers:{'Content-Type':'application/octet-stream'}});
          }});
          const blob=await api.download('/projects/project-a/artifacts/41/download?module3_project_id=7','private-token');
          return {calls,text:await blob.text(),type:blob.type};
        }''')
        self.assertEqual(result['text'], '# Requisitos')
        self.assertEqual(result['calls'][0]['method'], 'GET')
        self.assertEqual(result['calls'][0]['headers']['Authorization'], 'Bearer private-token')
        self.assertNotIn('private-token', result['calls'][0]['url'])

    def test_oversize_or_html_download_is_rejected(self):
        result = self.evaluate('''async()=>{
          const {createPlatformClient}=await import('/scripts/platform-api.js');
          const kinds=[];
          for(const headers of [{'Content-Type':'text/html'},
            {'Content-Type':'application/octet-stream','Content-Length':'10485761'}]) {
            const api=createPlatformClient({baseUrl:'https://projects.example',fetchImpl:async()=>new Response('data',{headers})});
            try{await api.download('/projects/project-a/artifacts/41/download?module3_project_id=7','token');}
            catch(error){kinds.push(error.kind);}
          }
          return kinds;
        }''')
        self.assertEqual(result, ['invalid-response', 'invalid-response'])
