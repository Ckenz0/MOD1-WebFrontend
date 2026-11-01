from browser_support import BrowserCase


class DomainValueTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_profile_draft_normalizes_skills_and_preserves_literal_summary(self):
        result = self.evaluate('''async () => {
          const {buildProfileDraft} = await import('/scripts/auth-domain.js');
          return buildProfileDraft({summary:'  Resumo  ',seniority:'mid',hours:'0',
            skills:[{name:'  Cafe\\u0301  ',level:4}]});
        }''')
        self.assertEqual(result, {'value': {'summary': '  Resumo  ', 'seniority': 'mid',
            'weekly_availability_hours': 0, 'skills': [{'name': 'Café', 'level': 4}]}})

    def test_readonly_project_hides_data_mutations_but_preserves_access_administration(self):
        result = self.evaluate('''async()=>{
          const {permissionsFor}=await import('/scripts/permissions.js');
          const permissions=['project:read','project:update','project:members:manage','project:lifecycle:manage',
            'backlog:read','backlog:create','backlog:update','backlog:update_status','backlog:reorder'];
          return permissionsFor({status:'completed',archived:false,permissions},'user');
        }''')
        self.assertEqual(result, ['project:read', 'project:members:manage', 'project:lifecycle:manage', 'backlog:read'])

    def test_profile_rejects_invalid_fields_and_duplicate_normalized_skills(self):
        result = self.evaluate('''async () => {
          const {buildProfileDraft} = await import('/scripts/auth-domain.js');
          const base={summary:'',seniority:'mid',hours:'20',skills:[]};
          const fields=[{hours:''},{hours:'0.5'},{hours:'169'},{seniority:'unknown'},{summary:'x'.repeat(2001)}];
          const invalidFields=fields.map(change=>buildProfileDraft({...base,...change}).error);
          const duplicate=buildProfileDraft({...base,skills:[{name:'Café',level:2},{name:' CAFE\\u0301 ',level:3}]});
          const badLevel=buildProfileDraft({...base,skills:[{name:'Python',level:6}]});
          return {invalidFields,duplicate,badLevel};
        }''')
        self.assertEqual(result, {'invalidFields': ['fields'] * 5,
            'duplicate': {'error': 'skills', 'skillIndex': 1},
            'badLevel': {'error': 'skills', 'skillIndex': 0}})

    def test_membership_expiry_and_invitation_deadline_are_pure(self):
        result = self.evaluate('''async () => {
          const {membershipExpiry,invitationDeadline} = await import('/scripts/collaboration-domain.js');
          const out={empty:membershipExpiry('',0),future:membershipExpiry('2030-01-02T00:00:00Z',0),
            deadline:invitationDeadline('2030-01-07T00:00:00Z','2030-01-02T00:00:00Z')};
          try {membershipExpiry('2020-01-01T00:00:00Z',Date.parse('2026-10-30T00:00:00Z'))}
          catch(error){out.pastRejected=true}
          try {membershipExpiry('invalid',0)}catch(error){out.invalidRejected=true}
          return out;
        }''')
        self.assertEqual(result, {'empty': None, 'future': '2030-01-02T00:00:00.000Z',
            'deadline': 1893542400000, 'pastRejected': True, 'invalidRejected': True})
