from browser_support import BrowserCase


class ApiSessionTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_literal_password_and_bearer_header(self):
        result = self.evaluate('''async (fixtures) => {
          const {createApiClient} = await import('/scripts/api.js');
          const calls = [];
          const api = createApiClient({baseUrl:'http://127.0.0.1:8000/',
            fetchImpl:async (url, options) => {
              calls.push({url, method:options.method, headers:Object.fromEntries(new Headers(options.headers)),
                          body:options.body?.toString()});
              return new Response(JSON.stringify(calls.length===1?fixtures.token:fixtures.user));
            }});
          await api.login('conta@example.com','  password12345  ');
          const me = await api.getMe('synthetic-token');
          return {calls, email:me.email};
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result['email'], 'conta@example.com')
        call = result['calls'][0]
        self.assertEqual(call['url'], 'http://127.0.0.1:8000/auth/token')
        self.assertEqual(call['method'], 'POST')
        self.assertEqual(call['body'], 'username=conta%40example.com&password=++password12345++')
        self.assertIn('application/x-www-form-urlencoded', call['headers']['content-type'])
        self.assertEqual(result['calls'][1]['headers']['authorization'], 'Bearer synthetic-token')

    def test_invalid_token_responses_fail_closed(self):
        cases = [None, {}, {**self.token_response, 'expires_in': 0},
                 {**self.token_response, 'expires_in': '1800'},
                 {**self.token_response, 'expires_in': True},
                 {**self.token_response, 'token_type': 'other'},
                 {**self.token_response, 'access_token': ''}]
        result = self.evaluate('''async cases => {
          const {createApiClient} = await import('/scripts/api.js');
          const results = [];
          for(const data of cases) {
            const api = createApiClient({baseUrl:'http://127.0.0.1',
              fetchImpl:async()=>new Response(JSON.stringify(data))});
            try {await api.login('a@example.com','literal-password'); results.push('accepted')}
            catch(error){results.push(error.kind)}
          }
          return results;
        }''', cases)
        self.assertEqual(result, ['invalid-response'] * len(cases))

    def test_invalid_identity_and_malformed_json_fail_closed(self):
        result = self.evaluate('''async fixtures => {
          const {createApiClient} = await import('/scripts/api.js');
          const values = ['not-json', JSON.stringify({}), JSON.stringify({...fixtures, id:'bad'}),
            JSON.stringify({...fixtures, is_active:false}), JSON.stringify({...fixtures,created_at:'bad'})];
          const out=[];
          for(const body of values) {
            const api=createApiClient({baseUrl:'http://127.0.0.1',fetchImpl:async()=>new Response(body)});
            try{await api.getMe('synthetic-token');out.push('accepted')}catch(e){out.push(e.kind)}
          }
          return out;
        }''', self.identity)
        self.assertEqual(result, ['invalid-response'] * 5)

    def test_error_classification_hides_remote_contents(self):
        result = self.evaluate('''async () => {
          const {createApiClient} = await import('/scripts/api.js');
          const out=[];
          for(const status of [401,422,503,500]) {
            const api=createApiClient({baseUrl:'http://127.0.0.1',
              fetchImpl:async()=>new Response('private-exception synthetic-token',{status})});
            for(const action of [()=>api.login('a@example.com','literal-password'),()=>api.getMe('synthetic-token')]) {
              try{await action()}catch(e){out.push({kind:e.kind,message:e.message})}
            }
          }
          return out;
        }''')
        self.assertEqual([r['kind'] for r in result], ['credentials', 'unauthorized',
            'validation', 'validation', 'unavailable', 'unavailable', 'unavailable', 'unavailable'])
        for entry in result:
            self.assertNotIn('private-exception', entry['message'])
            self.assertNotIn('synthetic-token', entry['message'])

    def test_timeout_network_and_explicit_cancellation(self):
        result = self.evaluate('''async () => {
          const {createApiClient} = await import('/scripts/api.js');
          const pending=(_, {signal})=>new Promise((resolve,reject)=>{
            if(signal.aborted) reject(new DOMException('Aborted','AbortError'));
            else signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true});
          });
          const kinds=[];
          const controller=new AbortController(); controller.abort();
          const scenarios=[{fetchImpl:pending,timeoutMs:20},
            {fetchImpl:async()=>{throw new TypeError('private-exception')}},
            {fetchImpl:pending,signal:controller.signal}];
          for(const {signal,...options} of scenarios){
            const api=createApiClient({baseUrl:'http://127.0.0.1',...options});
            try{await api.login('a@example.com','literal-password',{signal})}catch(e){kinds.push(e.kind)}
          }
          return kinds;
        }''')
        self.assertEqual(result, ['timeout', 'network', 'cancelled'])

    def test_session_expires_and_never_persists(self):
        result = self.evaluate('''async () => {
          const {createSession}=await import('/scripts/session.js');
          let now=1000;
          const session=createSession({now:()=>now});
          session.start({access_token:'synthetic-token',token_type:'bearer',expires_in:30});
          const before=session.getToken(); now=31000;
          const expired=session.getToken(); session.clear();
          return {before,expired,active:session.isActive(),stored:localStorage.length+sessionStorage.length};
        }''')
        self.assertEqual(result, {'before': 'synthetic-token', 'expired': None,
                                 'active': False, 'stored': 0})
