from browser_support import BrowserCase


class ServiceReadinessTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_prepares_dependencies_in_parallel_and_shares_work(self):
        result = self.evaluate('''async () => {
          const {createServiceReadiness}=await import('/scripts/service-readiness.js');
          const urls=[], pending=[];
          const gate=createServiceReadiness({baseUrls:['https://auth.test','https://projects.test'],
            fetchImpl:(url,options)=>{urls.push({url,method:options.method,credentials:options.credentials,
              authorization:options.headers?.Authorization});
              return new Promise(resolve=>pending.push(()=>resolve(new Response('{}'))));}});
          const a=gate.prepare(), b=gate.prepare();
          await new Promise(resolve=>setTimeout(resolve,0));
          const parallel=urls.length; pending.forEach(resolve=>resolve());
          await Promise.all([a,b]); await gate.prepare();
          return {urls,parallel};
        }''')
        self.assertEqual(result['parallel'], 2)
        self.assertEqual([x['url'] for x in result['urls']],
                         ['https://auth.test/health/ready', 'https://projects.test/health/ready'])
        self.assertTrue(all(x['method'] == 'GET' and x['credentials'] == 'omit'
                            and x.get('authorization') is None for x in result['urls']))

    def test_transient_readiness_failure_retries_only_health_checks(self):
        result = self.evaluate('''async () => {
          const {createServiceReadiness}=await import('/scripts/service-readiness.js');
          const calls=[];
          const gate=createServiceReadiness({baseUrls:['https://auth.test'],retryDelayMs:1,
            fetchImpl:async url=>{calls.push(url);return new Response('{}',{status:calls.length===1?503:200})}});
          await gate.prepare(); return calls;
        }''')
        self.assertEqual(result, ['https://auth.test/health/ready'] * 2)

    def test_total_deadline_and_cancelled_waiter_do_not_leave_background_polling(self):
        result = self.evaluate('''async () => {
          const {createServiceReadiness}=await import('/scripts/service-readiness.js');
          let calls=0;
          const gate=createServiceReadiness({baseUrls:['https://auth.test'],timeoutMs:35,
            requestTimeoutMs:10,retryDelayMs:1,fetchImpl:(_, {signal})=>{
              calls++;return new Promise((resolve,reject)=>signal.addEventListener('abort',
                ()=>reject(new DOMException('aborted','AbortError')),{once:true}));}});
          let kind;try{await gate.prepare()}catch(e){kind=e.kind}
          const after=calls;await new Promise(resolve=>setTimeout(resolve,45));
          const c=new AbortController();c.abort();let cancelled;
          try{await gate.prepare({signal:c.signal})}catch(e){cancelled=e.kind}
          return {kind,cancelled,after,final:calls};
        }''')
        self.assertEqual(result['kind'], 'timeout')
        self.assertEqual(result['cancelled'], 'cancelled')
        self.assertGreater(result['after'], 0)
        self.assertEqual(result['after'], result['final'])

    def test_one_cancelled_waiter_does_not_cancel_another(self):
        result = self.evaluate('''async () => {
          const {createServiceReadiness}=await import('/scripts/service-readiness.js');
          let release, aborted=false;
          const gate=createServiceReadiness({baseUrls:['https://auth.test'],fetchImpl:(_, {signal})=>{
            signal.addEventListener('abort',()=>{aborted=true});
            return new Promise(resolve=>{release=()=>resolve(new Response('{}'))});}});
          const c=new AbortController();
          const a=gate.prepare({signal:c.signal}).catch(e=>e.kind),b=gate.prepare();
          c.abort(); const kind=await a;release();await b;return {kind,aborted};
        }''')
        self.assertEqual(result, {'kind': 'cancelled', 'aborted': False})

    def test_failed_preparation_never_sends_business_write(self):
        result = self.evaluate('''async () => {
          const {createServiceReadiness}=await import('/scripts/service-readiness.js');
          const {createApiClient}=await import('/scripts/api.js');
          let writes=0;
          const readiness=createServiceReadiness({baseUrls:['https://auth.test'],timeoutMs:20,
            retryDelayMs:1,fetchImpl:async()=>new Response('{}',{status:503})});
          const api=createApiClient({baseUrl:'https://auth.test',readiness,
            fetchImpl:async()=>{writes++;return new Response('{}')}});
          let kind;try{await api.login('a@example.com','password12345')}catch(e){kind=e.kind}
          return {writes,kind};
        }''')
        self.assertEqual(result, {'writes': 0, 'kind': 'unavailable'})

    def test_uncertain_write_is_not_replayed_and_next_action_prepares_again(self):
        result = self.evaluate('''async () => {
          const {createServiceReadiness}=await import('/scripts/service-readiness.js');
          const {createApiClient}=await import('/scripts/api.js');
          let health=0,writes=0;
          const readiness=createServiceReadiness({baseUrls:['https://auth.test'],
            fetchImpl:async()=>{health++;return new Response('{}')}});
          const api=createApiClient({baseUrl:'https://auth.test',readiness,
            fetchImpl:async()=>{writes++;return new Response('{}',{status:503})}});
          for(let i=0;i<2;i++)try{await api.login('a@example.com','password12345')}catch{}
          return {health,writes};
        }''')
        self.assertEqual(result, {'health': 2, 'writes': 2})

    def test_cancelled_preparation_never_sends_write_and_new_request_can_recover(self):
        result = self.evaluate('''async () => {
          const {createServiceReadiness}=await import('/scripts/service-readiness.js');
          const {createApiClient}=await import('/scripts/api.js');
          let writes=0;
          const readiness=createServiceReadiness({baseUrls:['https://auth.test'],
            fetchImpl:(_, {signal})=>new Promise((resolve,reject)=>{
              const timer=setTimeout(()=>resolve(new Response('{}')),15);
              signal.addEventListener('abort',()=>{clearTimeout(timer);
                reject(new DOMException('aborted','AbortError'))},{once:true});})});
          const api=createApiClient({baseUrl:'https://auth.test',readiness,fetchImpl:async()=>{
            writes++;return new Response(JSON.stringify({access_token:'ok',token_type:'bearer',expires_in:30}))}});
          const c=new AbortController();const a=api.login('a@b.com','password12345',{signal:c.signal}).catch(e=>e.kind);
          c.abort();const kind=await a;
          await api.login('a@b.com','password12345');return {kind,writes};
        }''')
        self.assertEqual(result, {'kind': 'cancelled', 'writes': 1})

    def test_projects_and_backlog_cancel_before_mutating(self):
        result = self.evaluate('''async () => {
          const {createProjectsApiClient}=await import('/scripts/projects-api.js');
          const {createBacklogApiClient}=await import('/scripts/backlog-api.js');
          const out=[];let writes=0;
          const options={baseUrl:'https://api.test',fetchImpl:async()=>{writes++;return new Response('{}')},
            readiness:{prepare:async()=>{throw {kind:'cancelled'}},invalidate(){}}};
          const project='22222222-2222-4222-8222-222222222222';
          const story='33333333-3333-4333-8333-333333333333';
          for(const action of [()=>createProjectsApiClient(options).create('token',{name:'A'}),
            ()=>createBacklogApiClient(options).create('token',project,{title:'A'}),
            ()=>createBacklogApiClient(options).update('token',project,story,{status:'done'})]) {
            try{await action()}catch(e){out.push(e.kind)}
          }
          return {out,writes};
        }''')
        self.assertEqual(result, {'out': ['cancelled'] * 3, 'writes': 0})

    def test_cloud_login_waits_for_readiness_before_sending_credentials(self):
        self.page.route('**/config.js', lambda route: route.fulfill(
            content_type='text/javascript', body='''
              export const API_BASE_URL="https://auth.example.test";
              export const PROJECTS_API_BASE_URL="https://projects.example.test";
              export const BACKLOG_API_BASE_URL="https://backlog.example.test";
            '''))
        pending = []
        writes = []
        self.page.route('**/health/ready', lambda route: pending.append(route))
        self.page.route('**/auth/token', lambda route: (
            writes.append(route.request.method), route.fulfill(json=self.token_response)))
        self.page.route('**/auth/me', lambda route: route.fulfill(json=self.identity))
        self.page.goto(self.base_url)
        self.login()
        self.page.get_by_text('Preparando acesso…', exact=True).wait_for()
        self.assertEqual(writes, [])
        self.assertEqual(len(pending), 1)
        pending[0].fulfill(json={'status': 'ready'})
        self.page.get_by_role('button', name='Meus projetos', exact=True).wait_for()
        self.assertEqual(writes, ['POST'])
