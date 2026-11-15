"""The smoke runner refuses cloud endpoints before loading any backend."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'smoke_gemini.py'


class GeminiSmokeTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(SCRIPT), *arguments],
                              capture_output=True, text=True, timeout=10)

    def test_help_explains_controlled_http_and_no_real_ai(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--identity-path', result.stdout)
        self.assertIn('--projects-path', result.stdout)
        self.assertIn('--backlog-path', result.stdout)
        self.assertIn('controlled HTTP', result.stdout)

    def test_rejects_remote_and_ambiguous_urls_before_loading_backends(self):
        for url in [
            'https://generativelanguage.googleapis.com/v1beta',
            'http://remote.example/v1beta', 'http://localhost/v1beta?key=synthetic-secret',
            'http://user:synthetic-secret@localhost/v1beta',
            'http://localhost/v1beta#synthetic-secret', 'http://localhost/a/../v1beta',
            'http://localhost/%76%31beta', 'http://localhost/v1beta\\x',
            'http://localhost:invalid/v1beta', 'http://localhost/v1beta\n',
        ]:
            with self.subTest(url=url):
                result = self.run_cli('--base-url', url, '--identity-path', 'missing',
                                      '--projects-path', 'missing', '--backlog-path', 'missing')
                self.assertEqual(result.returncode, 2)
                self.assertIn('HTTP loopback /v1beta', result.stderr)
                self.assertNotIn('synthetic-secret', result.stderr + result.stdout)
                self.assertNotIn('Traceback', result.stderr)

    def test_missing_checkout_fails_without_backend_import_or_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_cli('--base-url', 'http://127.0.0.1:1/v1beta',
                                  '--identity-path', folder, '--projects-path', folder,
                                  '--backlog-path', folder)
        self.assertEqual(result.returncode, 2)
        self.assertIn('backend checkout', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
