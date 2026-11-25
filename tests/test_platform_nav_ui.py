import re

from playwright.sync_api import expect

from browser_support import BrowserCase


class PlatformNavigationUiTests(BrowserCase):
    """The shared platform bar (public/nav.js) agreed between the module groups."""

    def setUp(self):
        super().setUp()
        self.assertEqual(self.page.goto(self.base_url).status, 200)
        self.nav = self.page.get_by_role('navigation', name='Módulos da plataforma')

    def test_home_links_to_the_other_module_frontends(self):
        expect(self.nav).to_be_visible()
        current = self.nav.get_by_role('link', name='Projetos', exact=True)
        expect(current).to_have_attribute('aria-current', 'page')
        for name in ['GitHub Sync', 'Artefatos', 'Code Review', 'Curadoria', 'MackAI']:
            link = self.nav.get_by_role('link', name=name, exact=True)
            expect(link).to_have_attribute('href', re.compile(r'^https://'))
            expect(link).not_to_have_attribute('aria-current', 'page')
        self.assertEqual(self.nav.get_by_role('link').count(), 6)

    def test_module_without_address_is_shown_disabled_not_as_a_broken_link(self):
        disabled = self.nav.locator('.bm-off', has_text='Notificações')
        expect(disabled).to_be_visible()
        expect(disabled).to_have_attribute('title', 'Endereço ainda não informado')
        expect(self.nav.get_by_role('link', name='Notificações')).to_have_count(0)

    def test_skip_link_stays_the_first_keyboard_stop_above_the_bar(self):
        expect(self.page.get_by_label('E-mail', exact=True)).to_be_enabled()
        self.page.keyboard.press('Tab')
        skip = self.page.get_by_role('link', name='Ir para o conteúdo')
        expect(skip).to_be_focused()
        expect(skip).to_be_in_viewport()
        on_top = self.evaluate('''() => {
          const link = document.querySelector('.skip-link'), box = link.getBoundingClientRect();
          return document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2) === link;
        }''')
        self.assertTrue(on_top, 'The focused skip link must not sit under the sticky platform bar')

    def test_bar_mounts_even_when_the_application_module_fails(self):
        with self.browser.new_context() as context:
            page = context.new_page()
            page.route('**/scripts/app.js', lambda route: route.abort())
            page.goto(self.base_url)
            expect(page.get_by_role('navigation', name='Módulos da plataforma')).to_be_visible()

    def test_bar_scrolls_inside_itself_on_a_phone(self):
        self.page.set_viewport_size({'width': 320, 'height': 740})
        expect(self.nav).to_be_visible()
        self.assertTrue(self.evaluate('() => document.documentElement.scrollWidth <= innerWidth'))
        self.assertTrue(self.evaluate('() => { const n = document.querySelector(".barra-modulos"); return n.scrollWidth > n.clientWidth; }'))
