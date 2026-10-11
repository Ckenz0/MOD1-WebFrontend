from browser_support import BrowserCase

STORY = {'id': '33333333-3333-4333-8333-333333333333',
         'project_id': '22222222-2222-4222-8222-222222222222',
         'created_by': '11111111-1111-4111-8111-111111111111',
         'title': 'História', 'description': '<b>literal</b>\nlinha 2',
         'acceptance_criteria': 'Dado X\nQuando Y\nEntão Z',
         'priority': 'medium', 'status': 'todo',
         'created_at': '2026-10-11T12:00:00Z', 'updated_at': '2026-10-11T12:00:00Z'}


class BacklogApiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_four_operations_and_safe_error_mapping(self):
        result = self.evaluate('''async s => {
          const {createBacklogApiClient} = await import('/scripts/backlog-api.js');
          const calls=[];
          const api=createBacklogApiClient({baseUrl:'http://127.0.0.1:8002', fetchImpl:async(url,o)=>{
            calls.push({url,...o,signal:undefined});
            return new Response(JSON.stringify(calls.length===2?{items:[s],total:1,limit:20,offset:0}:s));
          }});
          await api.create('token',s.project_id,{title:s.title,description:s.description,acceptance_criteria:s.acceptance_criteria,priority:'medium'});
          await api.list('token',s.project_id); await api.get('token',s.project_id,s.id);
          await api.update('token',s.project_id,s.id,{status:'done'});
          const errors=[];
          for(const status of [401,404,422,503]) {
            const a=createBacklogApiClient({baseUrl:location.origin,fetchImpl:async()=>new Response('secret',{status})});
            try{await a.list('token',s.project_id)}catch(e){errors.push({kind:e.kind,message:e.message})}
          } return {calls,errors};
        }''', STORY)
        base = 'http://127.0.0.1:8002/projects/' + STORY['project_id'] + '/stories'
        self.assertEqual([c['url'] for c in result['calls']], [base, base+'?limit=20&offset=0', base+'/'+STORY['id'], base+'/'+STORY['id']])
        self.assertEqual([c['method'] for c in result['calls']], ['POST', 'GET', 'GET', 'PATCH'])
        self.assertIn('\\n', result['calls'][0]['body'])
        for call in result['calls']:
            self.assertEqual(call['headers']['Authorization'], 'Bearer token')
            self.assertEqual((call['cache'], call['credentials'], call['redirect']), ('no-store', 'omit', 'error'))
        self.assertEqual([e['kind'] for e in result['errors']], ['unauthorized', 'not-found', 'validation', 'unavailable'])
        self.assertTrue(all('secret' not in e['message'] for e in result['errors']))

    def test_untrusted_story_and_page_responses(self):
        result = self.evaluate('''async s=>{
          const {createBacklogApiClient}=await import('/scripts/backlog-api.js'); const out=[];
          for(const data of [{}, {...s,project_id:s.id}, {...s,priority:'urgent'}, {...s,status:'other'}, {...s,title:'😀'.repeat(121)}, {...s,description:5}, {...s,updated_at:'bad'}, {...s,acceptance_criteria:null}, {...s,title:'\u0085'}, {...s,title:'\u001c'}]) {
            const a=createBacklogApiClient({baseUrl:location.origin,fetchImpl:async()=>new Response(JSON.stringify(data))});
            try{await a.get('token',s.project_id,s.id)}catch(e){out.push(e.kind)}
          }
          for(const data of [{items:[s],total:0,limit:20,offset:0}, {items:[s],total:1,limit:20,offset:1}, {items:[s],total:1,limit:10,offset:0}]) {
            const a=createBacklogApiClient({baseUrl:location.origin,fetchImpl:async()=>new Response(JSON.stringify(data))});
            try{await a.list('token',s.project_id)}catch(e){out.push(e.kind)}
          } return out;
        }''', STORY)
        self.assertEqual(result, ['invalid-response'] * 13)

    def test_legacy_unicode_padding_keeps_existing_stories_readable(self):
        result = self.evaluate('''async s=>{
          const {createBacklogApiClient}=await import('/scripts/backlog-api.js');
          const legacy={...s,title:'\ufeffHistória'};
          const api=createBacklogApiClient({baseUrl:location.origin,fetchImpl:async()=>new Response(JSON.stringify({items:[legacy],total:1,limit:20,offset:0}))});
          return (await api.list('token',s.project_id)).items[0].title;
        }''', STORY)
        self.assertEqual(result, '\ufeffHistória')

    def test_timeout_abort_after_json_and_invalid_configuration(self):
        result = self.evaluate('''async s=>{
          const {createBacklogApiClient}=await import('/scripts/backlog-api.js'); const out=[];
          const pending=(_, {signal})=>new Promise((ok,no)=>signal.addEventListener('abort',()=>no(new DOMException('Abort','AbortError'))));
          const a=createBacklogApiClient({baseUrl:location.origin,fetchImpl:pending,timeoutMs:15});
          try{await a.list('token',s.project_id)}catch(e){out.push(e.kind)}
          const c=new AbortController();
          const b=createBacklogApiClient({baseUrl:location.origin,fetchImpl:async()=>({ok:true,json:async()=>{c.abort();return s}})});
          try{await b.get('token',s.project_id,s.id,{signal:c.signal})}catch(e){out.push(e.kind)}
          const d=createBacklogApiClient({baseUrl:location.origin,fetchImpl:async()=>{throw Error('private')}});
          try{await d.list('token',s.project_id)}catch(e){out.push(e.kind)}
          for(const url of ['file:///local','https://u:p@example.com','https://example.com/?q=1']) {
            try{createBacklogApiClient({baseUrl:url})}catch{out.push('config')}
          }
          try{await d.list('token','../../private')}catch(e){out.push(e.kind)}
          return out;
        }''', STORY)
        self.assertEqual(result, ['timeout', 'cancelled', 'network', 'config', 'config', 'config', 'not-found'])
