from browser_support import BrowserCase


class PlatformApiTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_injected_platform_transport_serializes_json_and_bearer(self):
        result = self.evaluate('''async()=>{
          const {createPlatformClient}=await import('/scripts/platform-api.js');let call;
          const api=createPlatformClient({baseUrl:'http://127.0.0.1:8001',fetchImpl:async(url,options)=>{
            call={url,method:options.method,auth:new Headers(options.headers).get('Authorization'),body:JSON.parse(options.body),credentials:options.credentials};
            return new Response(JSON.stringify({id:'team-a',name:'Equipe de dados'}),{status:201});
          }});const team=await api.request('POST','/teams','opaque-token',{name:'Equipe de dados',description:'Integração'});
          return {call,name:team.name};
        }''')
        self.assertEqual(result, {'call': {'url': 'http://127.0.0.1:8001/teams', 'method': 'POST',
            'auth': 'Bearer opaque-token', 'body': {'name': 'Equipe de dados', 'description': 'Integração'},
            'credentials': 'omit'}, 'name': 'Equipe de dados'})

    def test_dependency_failure_conflict_and_permission_errors_remain_distinct(self):
        result = self.evaluate('''async()=>{
          const {createPlatformClient}=await import('/scripts/platform-api.js');const kinds=[];
          for(const status of [401,403,404,409,422,503]){
            const api=createPlatformClient({baseUrl:'http://127.0.0.1',fetchImpl:async()=>new Response('private backend trace',{status})});
            try{await api.request('POST','/teams','token',{})}catch(error){kinds.push({kind:error.kind,leaked:error.message.includes('private')})}
          }return kinds;
        }''')
        self.assertEqual(result, [{'kind': kind, 'leaked': False} for kind in
            ['unauthorized', 'forbidden', 'not-found', 'conflict', 'validation', 'unavailable']])

    def test_transport_rejects_foreign_paths_before_sending_credentials(self):
        result = self.evaluate('''async()=>{
          const {createPlatformClient}=await import('/scripts/platform-api.js');let calls=0;
          const api=createPlatformClient({baseUrl:'http://127.0.0.1',fetchImpl:async()=>{calls++;return new Response('{}')}});
          let rejected=0;for(const path of ['https://evil.example/','//evil.example/','/teams/../admin']){
            try{await api.request('GET',path,'secret')}catch{rejected++}
          }return {calls,rejected};
        }''')
        self.assertEqual(result, {'calls': 0, 'rejected': 3})

    def test_login_accepts_challenge_but_not_challenge_with_access_token(self):
        result = self.evaluate('''async()=>{
          const {createApiClient}=await import('/scripts/api.js');
          const out=[];for(const value of [
            {mfa_required:true,challenge_token:'challenge',expires_in:300},
            {mfa_required:true,challenge_token:'challenge',expires_in:300,access_token:'premature',token_type:'bearer'}]){
            const api=createApiClient({baseUrl:'http://127.0.0.1',fetchImpl:async()=>new Response(JSON.stringify(value))});
            try{const reply=await api.login('a@example.com','literal password');out.push(reply.mfa_required)}catch(error){out.push(error.kind)}
          }return out;
        }''')
        self.assertEqual(result, [True, 'invalid-response'])
