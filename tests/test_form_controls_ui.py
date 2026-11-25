from browser_support import BrowserCase


class FormControlsUiTests(BrowserCase):
    """Field contents stay whole inside their boxes in the compact signed-in layout."""

    def setUp(self):
        super().setUp()
        self.assertEqual(self.page.goto(self.base_url).status, 200)

    def test_multiselect_shows_every_option_in_the_compact_workspace(self):
        result = self.evaluate('''async () => {
          const {form} = await import('/scripts/workspace-view.js');
          document.body.classList.add('is-signed-in');
          const created = form('controls', [{name: 'roles', label: 'Papéis da equipe no projeto', type: 'multiselect',
            options: {product_owner: 'Product Owner', project_manager: 'PM/Scrum Master', developer: 'Desenvolvedor'},
            value: ['developer']}], 'Salvar', () => {});
          document.getElementById('main').prepend(created.node);
          const select = created.inputs.roles;
          return {size: select.size, client: select.clientHeight, scroll: select.scrollHeight,
            option: select.options[0].getBoundingClientRect().height};
        }''')
        self.assertEqual(result['size'], 3)
        self.assertLessEqual(result['scroll'], result['client'] + 1, 'No option may hide behind inner scrolling')
        self.assertGreaterEqual(result['client'] + 1, result['option'] * 3, 'All three options must be visible')

    def test_table_cells_wrap_words_whole_and_actions_stay_in_the_row(self):
        result = self.evaluate('''async () => {
          const {rows, action} = await import('/scripts/workspace-view.js');
          document.body.classList.add('is-signed-in');
          const list = rows([{role: 'Desenvolvedor', permissions: 'Consultar projeto, Consultar backlog'}],
            [{label: 'Papel', key: 'role'}, {label: 'Permissões', key: 'permissions'}],
            {caption: 'Papéis', actions: () => [action('Editar papel', () => {})]});
          list.style.width = '700px';
          document.getElementById('main').prepend(list);
          const cell = list.querySelector('tbody td');
          const range = document.createRange(); range.selectNodeContents(cell);
          const actions = list.querySelector('td.row-actions'), row = actions.parentElement;
          return {lines: range.getClientRects().length, display: getComputedStyle(actions).display,
            actionsBottom: actions.getBoundingClientRect().bottom, rowBottom: row.getBoundingClientRect().bottom};
        }''')
        self.assertEqual(result['lines'], 1, 'A role name must not break inside the word')
        self.assertEqual(result['display'], 'table-cell')
        self.assertAlmostEqual(result['actionsBottom'], result['rowBottom'], delta=1)
