from browser_support import BrowserCase

PROJECT = {'id': '22222222-2222-4222-8222-222222222222',
           'owner_id': '11111111-1111-4111-8111-111111111111', 'name': 'Projeto de teste',
           'description': 'linha 1\nlinha 2', 'created_at': '2026-10-11T12:00:00Z'}


class ProjectsApiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_projects_api_contract_and_error_mapping(self):
        result = self.evaluate('''async p => {
          const {createProjectsApiClient}=await import('/scripts/projects-api.js');
          const calls=[];
          const api=createProjectsApiClient({baseUrl:'http://127.0.0.1:8001',
            fetchImpl:async(url,options)=>{
              calls.push({url,...options,signal:undefined});
              return new Response(JSON.stringify(calls.length===2?{items:[p],total:1,limit:20,offset:0}:p));
            }});
          await api.create('token',{name:'A',description:''});
          await api.list('token'); await api.get('token',p.id);
          const errors=[];
          for(const status of [401,404,422,503]) {
            const a=createProjectsApiClient({baseUrl:'http://127.0.0.1',fetchImpl:async()=>new Response('private-token-sql',{status})});
            try{await a.list('token')}catch(e){errors.push({kind:e.kind,message:e.message})}
          }
          return {calls,errors};
        }''', PROJECT)
        self.assertEqual(result['calls'][0]['headers']['Authorization'], 'Bearer token')
        self.assertEqual(result['calls'][0]['body'], '{"name":"A","description":""}')
        self.assertEqual(result['calls'][1]['url'], 'http://127.0.0.1:8001/projects?limit=20&offset=0')
        self.assertEqual(result['calls'][2]['url'], 'http://127.0.0.1:8001/projects/' + PROJECT['id'])
        self.assertEqual([e['kind'] for e in result['errors']],
                         ['unauthorized', 'not-found', 'validation', 'unavailable'])
        for e in result['errors']:
            self.assertNotIn('private-token-sql', e['message'])

    def test_malformed_responses_and_cancel_timeout(self):
        result = self.evaluate('''async p=>{
          const {createProjectsApiClient}=await import('/scripts/projects-api.js');
          const out=[];
          for(const value of [{}, {...p,id:'bad'}, {...p,created_at:'bad'}, {...p,description:5}]){
            const a=createProjectsApiClient({baseUrl:'http://127.0.0.1',fetchImpl:async()=>new Response(JSON.stringify(value))});
            try{await a.get('token',p.id)}catch(e){out.push(e.kind)}
          }
          const pending=(_, {signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError'))));
          const c=new AbortController();c.abort();
          for(const options of [{timeoutMs:20},{signal:c.signal}]){
            const {signal,...rest}=options;
            const a=createProjectsApiClient({baseUrl:'http://127.0.0.1',fetchImpl:pending,...rest});
            try{await a.list('token',{signal})}catch(e){out.push(e.kind)}
          }
          const a=createProjectsApiClient({baseUrl:'http://127.0.0.1',fetchImpl:async()=>{throw new TypeError('private')}});
          try{await a.list('token')}catch(e){out.push(e.kind)}
          return out;
        }''', PROJECT)
        self.assertEqual(result, ['invalid-response']*4 + ['timeout', 'cancelled', 'network'])

    def test_invalid_configuration_and_project_ids(self):
        result = self.evaluate('''async ()=>{
          const {createProjectsApiClient}=await import('/scripts/projects-api.js');
          let blocked=0;
          for(const url of ['file:///local','https://user:pass@example.com','https://example.com/?x=1']){
            try{createProjectsApiClient({baseUrl:url})}catch{blocked++}
          }
          return blocked;
        }''')
        self.assertEqual(result, 3)
