"""Guard the architectural direction of the browser's native ES modules."""

import re
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / 'public' / 'scripts'
IMPORT = re.compile(r'''(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)["'](\.[^"']+)["']''')
DOMAIN = {
    'session.js', 'permissions.js', 'auth-domain.js', 'project-domain.js',
    'story-domain.js', 'validation-rules.js', 'collaboration-domain.js', 'api-errors.js', 'planning-domain.js',
}
APPLICATION = {'account-application.js', 'workspace-application.js', 'session-application.js'}
INFRASTRUCTURE = {'api.js', 'projects-api.js', 'backlog-api.js', 'service-readiness.js', 'platform-api.js'}
PRESENTATION = {
    'validation.js', 'projects.js', 'backlog.js', 'collaboration.js', 'professional-profile.js',
    'workspace-controller.js', 'workspace-view.js', 'public-auth-controller.js',
}


def browser_global_violations(source, forbidden):
    # Native module convention: ignore comments and quoted data, inspect identifiers.
    # Keep template expressions visible so `${document.title}` cannot evade the guard.
    non_code = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*' ''', re.VERBOSE)
    code = non_code.sub(' ', source)
    return sorted(set(re.findall(r'\b[A-Za-z_$][\w$]*\b', code)) & forbidden)


class LayerDependencyTests(unittest.TestCase):
    def test_boundary_check_detects_hidden_dom_and_direct_network_dependencies(self):
        source = '''// document and fetch in comments are harmless
          const message = "window.document";
          function run() { return document.title + window.location + fetch('/api'); }
        '''
        self.assertEqual(browser_global_violations(source, {'document', 'window', 'fetch'}),
                         ['document', 'fetch', 'window'])

    def test_domain_and_application_have_no_browser_or_transport_globals(self):
        forbidden = {'document', 'window', 'fetch', 'XMLHttpRequest', 'localStorage', 'sessionStorage'}
        for filename in DOMAIN | APPLICATION:
            path = SCRIPTS / filename
            if path.exists():
                self.assertEqual(browser_global_violations(path.read_text(encoding='utf-8'), forbidden), [], filename)

    def test_http_adapters_do_not_access_browser_views_or_storage(self):
        forbidden = {'document', 'window', 'localStorage', 'sessionStorage'}
        for filename in INFRASTRUCTURE:
            self.assertEqual(browser_global_violations((SCRIPTS / filename).read_text(encoding='utf-8'), forbidden), [], filename)

    def test_domain_cannot_reach_transport_or_presentation(self):
        violations = []
        for filename in DOMAIN:
            path = SCRIPTS / filename
            if not path.exists():
                continue
            dependencies = {Path(name).name for name in IMPORT.findall(path.read_text(encoding='utf-8'))}
            for dependency in dependencies - DOMAIN:
                violations.append(f'{filename} -> {dependency}')
        self.assertEqual(violations, [], 'Domain imports must remain inside the domain')

    def test_application_only_uses_injected_adapters_and_domain(self):
        for filename in APPLICATION:
            path = SCRIPTS / filename
            if not path.exists():
                continue
            dependencies = {Path(name).name for name in IMPORT.findall(path.read_text(encoding='utf-8'))}
            self.assertLessEqual(dependencies, DOMAIN | APPLICATION)

    def test_infrastructure_cannot_import_screens(self):
        for filename in INFRASTRUCTURE:
            path = SCRIPTS / filename
            dependencies = {Path(name).name for name in IMPORT.findall(path.read_text(encoding='utf-8'))}
            self.assertFalse(dependencies & (PRESENTATION | {'app.js'}), filename)

    def test_screens_do_not_import_http_clients(self):
        # app.js is the composition root: it alone may assemble concrete adapters.
        violations = []
        for filename in PRESENTATION:
            dependencies = {Path(name).name for name in IMPORT.findall(
                (SCRIPTS / filename).read_text(encoding='utf-8'))}
            for dependency in dependencies & INFRASTRUCTURE:
                violations.append(f'{filename} -> {dependency}')
        self.assertEqual(violations, [], 'Screens use injected clients and shared error types')
