from browser_support import BrowserCase


class WorkspaceApplicationTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_backlog_load_combines_current_project_permissions_and_stories(self):
        result = self.evaluate('''async () => {
          const {createWorkspaceApplication} = await import('/scripts/workspace-application.js');
          const project={id:'project-a',permissions:['project:read','backlog:read','backlog:update_status']};
          const page={items:[{id:'story-a'}],total:1,limit:20,offset:0};
          const app=createWorkspaceApplication({projects:{get:async()=>project},backlog:{list:async()=>page}});
          return app.loadBacklog('token','project-a','user-a');
        }''')
        self.assertEqual(result, {
            'project': {'id': 'project-a', 'permissions': ['project:read', 'backlog:read', 'backlog:update_status']},
            'page': {'items': [{'id': 'story-a'}], 'total': 1, 'limit': 20, 'offset': 0},
            'permissions': ['project:read', 'backlog:read', 'backlog:update_status'],
        })

    def test_member_load_combines_access_catalog_and_members(self):
        result = self.evaluate('''async () => {
          const {createWorkspaceApplication} = await import('/scripts/workspace-application.js');
          const projects={get:async()=>({id:'project-a',permissions:['project:read']}),
            roles:async()=>({items:[{key:'developer'}]}),members:async()=>({items:[],total:0,limit:20,offset:0})};
          return createWorkspaceApplication({projects}).loadMembers('token','project-a','user-a');
        }''')
        self.assertEqual(result, {'project': {'id': 'project-a', 'permissions': ['project:read']},
            'roles': [{'key': 'developer'}], 'members': {'items': [], 'total': 0, 'limit': 20, 'offset': 0}})

    def test_failed_project_lookup_does_not_return_stories_as_an_authorized_result(self):
        result = self.evaluate('''async () => {
          const {createWorkspaceApplication} = await import('/scripts/workspace-application.js');
          const app=createWorkspaceApplication({projects:{get:async()=>{throw Object.assign(new Error(),{kind:'not-found'})}},
            backlog:{list:async()=>({items:[{id:'story-a'}]})}});
          try {await app.loadBacklog('token','project-a','user-a');return 'accepted'}
          catch(error){return error.kind}
        }''')
        self.assertEqual(result, 'not-found')

    def test_story_change_keeps_developer_patch_limited_to_status(self):
        result = self.evaluate('''async () => {
          const {storyChange} = await import('/scripts/story-domain.js');
          const saved={title:'Original',description:'Old',acceptance_criteria:'Criteria'};
          const draft={title:'\\u0085Revised\\u001f',description:'New',acceptance_criteria:'Criteria',priority:'high',status:'done'};
          return {developer:storyChange(saved,draft,['backlog:update_status']),
            manager:storyChange(saved,draft,['backlog:update','backlog:update_status'])};
        }''')
        self.assertEqual(result, {'developer': {'status': 'done'},
            'manager': {'status': 'done', 'priority': 'high', 'title': 'Revised', 'description': 'New'}})
