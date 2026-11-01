from browser_support import BrowserCase


class PlanningDomainTests(BrowserCase):
    def setUp(self):
        super().setUp()
        self.page.goto(self.base_url + '/__test__/')

    def test_project_budget_remains_decimal_and_dates_are_ordered(self):
        result = self.evaluate('''async()=>{
          const {projectDetails}=await import('/scripts/planning-domain.js');
          const value=projectDetails({scope:'Escopo',budget_amount:'1234,50',budget_currency:'BRL',tags:' API, dados, API ',
            planned_start:'2026-11-01',planned_end:'2026-12-01',technology_stack:'Python,PostgreSQL',technical_requirements:'API REST',soft_skills:'Comunicação',constraints:'Prazo'});
          let reversed=false;try{projectDetails({planned_start:'2026-12-01',planned_end:'2026-11-01'})}catch{reversed=true}
          return {amount:value.budget_amount,tags:value.tags,reversed,stack:value.technology_stack};
        }''')
        self.assertEqual(result, {'amount': '1234.50', 'tags': ['API', 'dados'], 'reversed': True,
            'stack': ['Python', 'PostgreSQL']})

    def test_guided_story_requires_complete_persona_action_benefit_and_keeps_moscow_separate(self):
        result = self.evaluate('''async()=>{
          const {itemDraft}=await import('/scripts/planning-domain.js');
          const value=itemDraft({kind:'story',title:'Acompanhar entrega',persona:'cliente',action:'consultar o status',benefit:'planejar recebimento',
            moscow_priority:'must',priority:'medium',estimate_value:'3.5',estimate_unit:'points',is_blocked:false});
          let invalid=false;try{itemDraft({title:'Incompleta',persona:'cliente',action:'',benefit:''})}catch{invalid=true}
          return {moscow:value.moscow_priority,legacy:value.priority,estimate:value.estimate_value,invalid};
        }''')
        self.assertEqual(result, {'moscow': 'must', 'legacy': 'medium', 'estimate': '3.5', 'invalid': True})

    def test_block_requires_reason_and_cross_project_ids_are_never_invented(self):
        result = self.evaluate('''async()=>{
          const {itemDraft}=await import('/scripts/planning-domain.js');let blocked=false,id=false;
          try{itemDraft({title:'Bloqueio',is_blocked:true,blocked_reason:''})}catch{blocked=true}
          try{itemDraft({title:'Responsável',assignee_id:'name@example.com'})}catch{id=true}
          return {blocked,id};
        }''')
        self.assertEqual(result, {'blocked': True, 'id': True})
