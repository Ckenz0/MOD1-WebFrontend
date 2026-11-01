from browser_support import BrowserCase


class SessionSecurityTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def token(self):
        return {**self.token_response, 'refresh_token': 'opaque-local-refresh',
            'session_id': '33333333-3333-4333-8333-333333333333',
            'idle_expires_at': '2026-10-30T12:15:00Z', 'absolute_expires_at': '2026-10-30T20:00:00Z'}

    def test_idle_deadline_expires_session_before_access_token(self):
        result = self.evaluate('''async token => {
          const {createSession}=await import('/scripts/session.js');
          let now=Date.parse('2026-10-30T12:00:00Z');const session=createSession({now:()=>now});session.start(token);
          const before={active:session.isActive(),refresh:session.getRefreshToken(),id:session.getSessionId()};
          now=Date.parse('2026-10-30T12:15:00Z');
          return {before,active:session.isActive(),refresh:session.getRefreshToken(),token:session.getToken()};
        }''', self.token())
        self.assertEqual(result, {'before': {'active': True, 'refresh': 'opaque-local-refresh',
            'id': '33333333-3333-4333-8333-333333333333'}, 'active': False, 'refresh': None, 'token': None})

    def test_activity_uses_server_deadline_and_cannot_extend_absolute_limit(self):
        result = self.evaluate('''async token=>{
          const {createSession}=await import('/scripts/session.js');
          let now=Date.parse('2026-10-30T12:00:00Z');const session=createSession({now:()=>now});session.start(token);
          session.updateActivity({idle_expires_at:'2026-10-31T12:00:00Z',absolute_expires_at:'2026-10-31T20:00:00Z'});
          now=Date.parse('2026-10-30T20:00:00Z');return session.isSessionAlive();
        }''', self.token())
        self.assertFalse(result)

    def test_refresh_is_single_flight_and_installs_new_credentials(self):
        result = self.evaluate('''async fixtures=>{
          const {createSession}=await import('/scripts/session.js');
          const {createAccountApplication}=await import('/scripts/account-application.js');
          const session=createSession({now:()=>Date.parse('2026-10-30T12:00:00Z')});session.start(fixtures.token);
          let release,calls=0;const api={refresh:()=>{calls++;return new Promise(resolve=>release=resolve)}};
          const account=createAccountApplication({api,session});
          const one=account.refresh(),two=account.refresh();
          release({...fixtures.token,access_token:'rotated-access',refresh_token:'rotated-refresh'});
          await Promise.all([one,two]);return {calls,token:session.getToken(),refresh:session.getRefreshToken()};
        }''', {'token': self.token()})
        self.assertEqual(result, {'calls': 1, 'token': 'rotated-access', 'refresh': 'rotated-refresh'})

    def test_logout_during_refresh_cannot_restore_session(self):
        result = self.evaluate('''async token=>{
          const {createSession}=await import('/scripts/session.js');
          const {createAccountApplication}=await import('/scripts/account-application.js');
          const session=createSession({now:()=>Date.parse('2026-10-30T12:00:00Z')});session.start(token);
          let release;const account=createAccountApplication({session,api:{refresh:()=>new Promise(resolve=>release=resolve)}});
          const pending=account.refresh().catch(error=>error.kind);account.logout();release(token);
          return {kind:await pending,token:session.getToken(),refresh:session.getRefreshToken()};
        }''', self.token())
        self.assertEqual(result, {'kind': 'cancelled', 'token': None, 'refresh': None})

    def test_refresh_network_failure_preserves_live_session_for_retry(self):
        result = self.evaluate('''async token=>{
          const {createSession}=await import('/scripts/session.js');
          const {createAccountApplication}=await import('/scripts/account-application.js');
          const session=createSession({now:()=>Date.parse('2026-10-30T12:00:00Z')});session.start(token);
          const account=createAccountApplication({session,api:{refresh:async()=>{throw Object.assign(new Error(),{kind:'unavailable'})}}});
          try{await account.refresh()}catch(error){return {kind:error.kind,active:session.isSessionAlive(),refresh:session.getRefreshToken()}}
        }''', self.token())
        self.assertEqual(result, {'kind': 'unavailable', 'active': True, 'refresh': 'opaque-local-refresh'})

    def test_mfa_password_stage_cannot_install_access_until_factor_verified(self):
        result = self.evaluate('''async fixtures=>{
          const {createSession}=await import('/scripts/session.js');
          const {createAccountApplication}=await import('/scripts/account-application.js');
          const session=createSession();let me=0;
          const api={login:async()=>({mfa_required:true,challenge_token:'challenge',expires_in:300}),
            verifyMfa:async()=>fixtures.token,getMe:async()=>{me++;return fixtures.user}};
          const account=createAccountApplication({api,session});const challenge=await account.login('a@example.com','password');
          const before={active:session.isActive(),me};const user=await account.verifyMfa('123456');
          return {challenge:challenge.mfa_required,before,userId:user.id,me,active:session.isActive()};
        }''', {'token': self.token_response, 'user': self.identity})
        self.assertEqual(result, {'challenge': True, 'before': {'active': False, 'me': 0},
            'userId': self.identity['id'], 'me': 1, 'active': True})
