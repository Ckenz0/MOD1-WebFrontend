from browser_support import BrowserCase


class SessionPersistenceTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_reload_does_not_restart_access_lifetime(self):
        result = self.evaluate('''async () => {
          const {createSession}=await import('/scripts/session.js');
          let now=1000,saved=null;
          const store={load:()=>saved,save:value=>saved=value,clear:()=>saved=null};
          const first=createSession({now:()=>now,store});
          first.start({access_token:'synthetic-token',token_type:'bearer',expires_in:30});
          now=30000;const restored=createSession({now:()=>now,store});
          const before=restored.getToken();now=31000;
          return {before,expired:restored.getToken(),cleared:saved===null};
        }''')
        self.assertEqual(result, {'before': 'synthetic-token', 'expired': None, 'cleared': True})

    def test_idle_and_absolute_deadlines_survive_reload(self):
        result = self.evaluate('''async () => {
          const {createSession}=await import('/scripts/session.js');
          const out=[];
          for(const limits of [{idle:11000,absolute:21000},{idle:21000,absolute:11000}]) {
            let now=1000,saved=null;
            const store={load:()=>saved,save:value=>saved=value,clear:()=>saved=null};
            createSession({now:()=>now,store}).start({access_token:'synthetic-token',
              token_type:'bearer',expires_in:1800,refresh_token:'refresh',
              idle_expires_at:new Date(limits.idle).toISOString(),
              absolute_expires_at:new Date(limits.absolute).toISOString()});
            now=10000;const restored=createSession({now:()=>now,store});
            const before=restored.isSessionAlive();now=11000;
            out.push({before,after:restored.isSessionAlive(),cleared:saved===null});
          }return out;
        }''')
        self.assertEqual(result, [{'before': True, 'after': False, 'cleared': True}] * 2)

    def test_activity_deadline_is_persisted_without_extending_absolute_limit(self):
        result = self.evaluate('''async () => {
          const {createSession}=await import('/scripts/session.js');
          let now=1000,saved=null;
          const store={load:()=>saved,save:value=>saved=value,clear:()=>saved=null};
          const first=createSession({now:()=>now,store});
          first.start({access_token:'synthetic-token',token_type:'bearer',expires_in:1800,
            idle_expires_at:new Date(11000).toISOString(),absolute_expires_at:new Date(21000).toISOString()});
          first.updateActivity({idle_expires_at:new Date(31000).toISOString(),absolute_expires_at:new Date(41000).toISOString()});
          now=12000;const restored=createSession({now:()=>now,store});
          const before=restored.isActive();now=21000;
          return {before,after:restored.isActive(),cleared:saved===null};
        }''')
        self.assertEqual(result, {'before': True, 'after': False, 'cleared': True})

    def test_invalid_saved_shape_cannot_restore_or_break_session(self):
        result = self.evaluate('''async () => {
          const {createSession}=await import('/scripts/session.js');
          const out=[];
          for(const invalid of [{},[],{version:99},
            {version:1,token:'injected',accessExpiresAt:'tomorrow',idleExpiresAt:null,absoluteExpiresAt:null}]) {
            let saved=invalid;
            const store={load:()=>saved,save:value=>saved=value,clear:()=>saved=null};
            const session=createSession({store});
            out.push({active:session.isSessionAlive(),cleared:saved===null});
          }return out;
        }''')
        self.assertEqual(result, [{'active': False, 'cleared': True}] * 4)
