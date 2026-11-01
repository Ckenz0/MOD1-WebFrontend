from browser_support import BrowserCase


class RefreshCancellationTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_aborting_first_view_does_not_discard_shared_rotated_credentials(self):
        result = self.evaluate('''async token => {
          const {createSession}=await import('/scripts/session.js');
          const {createAccountApplication}=await import('/scripts/account-application.js');
          const session=createSession({now:()=>1000});
          session.start({...token,expires_in:1,refresh_token:'original-refresh',
            session_id:'33333333-3333-4333-8333-333333333333'});
          let finish,calls=0;
          const api={refresh:()=>{calls++;return new Promise(resolve=>finish=resolve)}};
          const account=createAccountApplication({api,session});
          const view=new AbortController();
          const first=account.accessToken({signal:view.signal}).catch(error=>error.kind);
          const second=account.accessToken().catch(error=>error.kind);
          // The server has consumed original-refresh, but its reply is delayed.
          view.abort();
          finish({...token,access_token:'rotated-access',expires_in:1800,
            refresh_token:'rotated-refresh',session_id:session.getSessionId()});
          return {first:await first,second:await second,calls,
            access:session.getToken(),refresh:session.getRefreshToken()};
        }''', self.token_response)
        self.assertEqual(result, {'first': 'cancelled', 'second': 'rotated-access', 'calls': 1,
            'access': 'rotated-access', 'refresh': 'rotated-refresh'})

    def test_logout_wins_while_shared_renewal_finishes_after_view_abort(self):
        result = self.evaluate('''async token => {
          const {createSession}=await import('/scripts/session.js');
          const {createAccountApplication}=await import('/scripts/account-application.js');
          const session=createSession({now:()=>1000});
          session.start({...token,expires_in:1,refresh_token:'original-refresh'});
          let finish;
          const api={refresh:()=>new Promise(resolve=>finish=resolve)};
          const account=createAccountApplication({api,session});
          const view=new AbortController();
          const pending=account.accessToken({signal:view.signal}).catch(error=>error.kind);
          view.abort();account.logout();
          finish({...token,access_token:'rotated-access',refresh_token:'rotated-refresh'});
          return {kind:await pending,access:session.getToken(),refresh:session.getRefreshToken()};
        }''', self.token_response)
        self.assertEqual(result, {'kind': 'cancelled', 'access': None, 'refresh': None})
