from browser_support import BrowserCase


class AccountApplicationTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_account_and_workspace_use_cases_run_in_a_worker_without_dom_or_fetch(self):
        result = self.evaluate('''async fixtures => {
          const source = `
            self.fetch=()=>{throw new Error('Application/domain must use injected adapters')};
            self.onmessage=async event=>{
              try {
                const root=event.data.origin+'/scripts/';
                const [{createAccountApplication},{createWorkspaceApplication},{createSession},auth,project,story,collaboration,validation,permissions,errors]=await Promise.all([
                  'account-application.js','workspace-application.js','session.js','auth-domain.js','project-domain.js',
                  'story-domain.js','collaboration-domain.js','validation-rules.js','permissions.js','api-errors.js'
                ].map(name=>import(root+name)));
                const session=createSession();
                const account=createAccountApplication({session,api:{login:async()=>event.data.token,getMe:async()=>event.data.user}});
                const user=await account.login('conta@example.com','literal password');
                const loggedToken=session.getToken();
                const workspace=createWorkspaceApplication({projects:{get:async()=>({id:'p',permissions:['backlog:read']}),
                  roles:async()=>({items:[{key:'developer'}]}),members:async()=>({items:[]})},backlog:{list:async()=>({items:[]})}});
                const loaded=await workspace.loadBacklog(loggedToken,'p',user.id);
                const members=await workspace.loadMembers(loggedToken,'p',user.id);
                let release;
                const late=createAccountApplication({session,api:{login:()=>new Promise(resolve=>release=resolve)}});
                const pending=late.login('conta@example.com','password').catch(error=>error.kind);
                late.logout();release(event.data.token);
                const cancelled=await pending;
                const draft=auth.buildProfileDraft({summary:'',seniority:'mid',hours:'20',skills:[]});
                self.postMessage({id:user.id,loggedToken,loaded:loaded.permissions,role:members.roles[0].key,cancelled,
                  active:session.isActive(),noDocument:typeof document==='undefined',valid:project.isId(user.id),
                  status:story.storyChange({}, {status:'done'},['backlog:update_status']).status,
                  availability:draft.value.weekly_availability_hours,emptyExpiry:collaboration.membershipExpiry('',0),
                  validName:validation.nameValueError('Nome'),permissions:permissions.isPermissions(loaded.permissions),
                  errorKind:new errors.ApiError('cancelled').kind});
              } catch(error) {self.postMessage({error:error.message})}
            }`;
          const url=URL.createObjectURL(new Blob([source],{type:'text/javascript'}));
          const worker=new Worker(url,{type:'module'});
          let timer;
          try {return await new Promise((resolve,reject)=>{
            timer=setTimeout(()=>reject(new Error('Worker use cases timed out')),5000);
            worker.onmessage=event=>resolve(event.data);worker.onerror=()=>reject(new Error('Worker failed'));
            worker.postMessage({...fixtures,origin:location.origin});
          })} finally {clearTimeout(timer);worker.terminate();URL.revokeObjectURL(url)}
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result, {'id': self.identity['id'], 'loggedToken': 'synthetic-token',
            'loaded': ['backlog:read'], 'role': 'developer', 'cancelled': 'cancelled', 'active': False,
            'noDocument': True, 'valid': True, 'status': 'done', 'availability': 20, 'emptyExpiry': None,
            'validName': '', 'permissions': True, 'errorKind': 'cancelled'})

    def test_login_coordinates_token_identity_and_session(self):
        result = self.evaluate('''async fixtures => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createApiClient} = await import('/scripts/api.js');
          const {createSession} = await import('/scripts/session.js');
          const session = createSession();
          let literal;
          const api = createApiClient({baseUrl:'http://127.0.0.1', fetchImpl:async (url, options) => {
            if (url.endsWith('/auth/token')) {
              literal = new URLSearchParams(options.body).get('password');
              return new Response(JSON.stringify(fixtures.token));
            }
            if (new Headers(options.headers).get('Authorization') !== 'Bearer synthetic-token') {
              return new Response(null, {status:401});
            }
            return new Response(JSON.stringify(fixtures.user));
          }});
          const account = createAccountApplication({api, session});
          const user = await account.login('conta@example.com', '  literal password  ');
          return {user, literal, token:session.getToken(), pending:account.isAuthenticating()};
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result['user'], self.identity)
        self.assertEqual(result['literal'], '  literal password  ')
        self.assertEqual(result['token'], 'synthetic-token')
        self.assertFalse(result['pending'])

    def test_logout_while_token_is_pending_cannot_restore_session(self):
        result = self.evaluate('''async token => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createSession} = await import('/scripts/session.js');
          const session = createSession(); let release; let identityRequests = 0;
          const api = {login:()=>new Promise(resolve=>release=resolve), getMe:async()=>{identityRequests++;return {}}};
          const account = createAccountApplication({api, session});
          const pending = account.login('a@example.com','password').catch(error=>error.kind);
          account.logout(); release(token);
          return {kind:await pending, active:session.isActive(), identityRequests};
        }''', self.token_response)
        self.assertEqual(result, {'kind': 'cancelled', 'active': False, 'identityRequests': 0})

    def test_logout_while_identity_is_pending_cannot_complete_login(self):
        result = self.evaluate('''async fixtures => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createSession} = await import('/scripts/session.js');
          const session = createSession(); let release; let entered;
          const identityEntered = new Promise(resolve=>entered=resolve);
          const api = {login:async()=>fixtures.token, getMe:()=>{entered();return new Promise(resolve=>release=resolve)}};
          const account = createAccountApplication({api, session});
          const pending = account.login('a@example.com','password').catch(error=>error.kind);
          await identityEntered;
          const authenticating = account.isAuthenticating();
          account.logout(); release(fixtures.user);
          return {kind:await pending, token:session.getToken(), authenticating, pending:account.isAuthenticating()};
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result, {'kind': 'cancelled', 'token': None, 'authenticating': True, 'pending': False})

    def test_expired_token_during_identity_lookup_is_not_accepted(self):
        result = self.evaluate('''async fixtures => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createSession} = await import('/scripts/session.js');
          let now = 0; const session = createSession({now:()=>now});
          const account = createAccountApplication({session, api:{login:async()=>({...fixtures.token,expires_in:1}),
            getMe:async()=>{now=1001; return fixtures.user}}});
          try {await account.login('a@example.com','password');return {accepted:true}}
          catch(error){return {kind:error.kind,active:session.isActive()}}
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result, {'kind': 'unauthorized', 'active': False})

    def test_cancelled_login_does_not_leave_a_session(self):
        result = self.evaluate('''async fixtures => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createSession} = await import('/scripts/session.js');
          const session = createSession(), controller = new AbortController();
          const account = createAccountApplication({session,api:{login:async()=>fixtures.token,
            getMe:async()=>{controller.abort();return fixtures.user}}});
          try {await account.login('a@example.com','password',{signal:controller.signal})}
          catch(error){return {kind:error.kind,active:session.isActive()}}
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result, {'kind': 'cancelled', 'active': False})

    def test_failed_identity_lookup_discards_token(self):
        result = self.evaluate('''async token => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createSession} = await import('/scripts/session.js');
          const session = createSession();
          const account = createAccountApplication({session,api:{login:async()=>token,
            getMe:async()=>{throw Object.assign(new Error('Unavailable'),{kind:'unavailable'})}}});
          try {await account.login('a@example.com','password')}
          catch(error){return {kind:error.kind,active:session.isActive()}}
        }''', self.token_response)
        self.assertEqual(result, {'kind': 'unavailable', 'active': False})

    def test_old_failed_login_cannot_clear_new_session(self):
        result = self.evaluate('''async fixtures => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createSession} = await import('/scripts/session.js');
          const session = createSession(); let rejectOld;
          const api = {login:email=>email==='old@example.com'?new Promise((resolve,reject)=>rejectOld=reject):Promise.resolve(fixtures.token),
            getMe:async()=>fixtures.user};
          const account = createAccountApplication({api,session});
          const old = account.login('old@example.com','old password').catch(error=>error.kind);
          const user = await account.login('new@example.com','new password');
          rejectOld(Object.assign(new Error('late failure'),{kind:'network'}));
          await old;
          return {id:user.id,token:session.getToken()};
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result, {'id': self.identity['id'], 'token': 'synthetic-token'})

    def test_password_change_clears_session_only_after_success(self):
        result = self.evaluate('''async token => {
          const {createAccountApplication} = await import('/scripts/account-application.js');
          const {createSession} = await import('/scripts/session.js');
          const session = createSession(); session.start(token); let reject = true;
          const api = {changePassword:async()=>{if(reject)throw Object.assign(new Error(),{kind:'password-rejected'})}};
          const account = createAccountApplication({api,session});
          let kind;
          try {await account.changePassword('old','new')}catch(error){kind=error.kind}
          const activeAfterFailure = session.isActive(); reject = false;
          await account.changePassword('old','new');
          return {kind,activeAfterFailure,activeAfterSuccess:session.isActive()};
        }''', self.token_response)
        self.assertEqual(result, {'kind': 'password-rejected', 'activeAfterFailure': True, 'activeAfterSuccess': False})

    def test_domain_runs_without_dom_or_network_in_a_worker(self):
        result = self.evaluate('''async origin => {
          const source = `
            import {isTokenResponse} from '${origin}/scripts/auth-domain.js';
            import {emailValueError,newPasswordValueError} from '${origin}/scripts/validation-rules.js';
            import {trimStoryTitle} from '${origin}/scripts/story-domain.js';
            import {createSession} from '${origin}/scripts/session.js';
            self.onmessage=()=>{
              const session=createSession();session.start({access_token:'worker-token',token_type:'bearer',expires_in:10});
              self.postMessage({noDocument:typeof document==='undefined',valid:isTokenResponse({access_token:'x',token_type:'bearer',expires_in:1}),
                badEmail:!!emailValueError('bad'),password:newPasswordValueError(' 1234567890 '),title:trimStoryTitle('\\u0085História\\u001f'),token:session.getToken()});
            }`;
          const url = URL.createObjectURL(new Blob([source],{type:'text/javascript'}));
          const worker = new Worker(url,{type:'module'});
          try {return await new Promise((resolve,reject)=>{
            worker.onmessage=event=>resolve(event.data); worker.onerror=()=>reject(new Error('Domain modules could not run without DOM'));
            worker.postMessage(null);
          })} finally {worker.terminate(); URL.revokeObjectURL(url)}
        }''', self.base_url)
        self.assertEqual(result, {'noDocument': True, 'valid': True, 'badEmail': True, 'password': '', 'title': 'História', 'token': 'worker-token'})
