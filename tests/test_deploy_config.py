import importlib.util
import tempfile
import unittest
from pathlib import Path


class DeployConfigTests(unittest.TestCase):
    def load(self):
        path = Path(__file__).resolve().parents[1] / 'scripts' / 'render_config.py'
        spec = importlib.util.spec_from_file_location('render_config', path)
        result = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(result)
        return result

    def test_render_only_public_origins_and_preserve_output_on_invalid_input(self):
        script = self.load()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.js'
            urls = ['https://auth.example.com', 'https://projects.example.com', 'https://backlog.example.com']
            script.render_config(*urls, path)
            output = path.read_text(encoding='utf-8')
            self.assertEqual(output,
                             'export const API_BASE_URL = "https://auth.example.com";\n'
                             'export const PROJECTS_API_BASE_URL = "https://projects.example.com";\n'
                             'export const BACKLOG_API_BASE_URL = "https://backlog.example.com";\n')
            for invalid in ['http://example.com', 'https://u:p@example.com', 'https://example.com/path',
                            'https://example.com?x=1', 'https://example.com/#x',
                            'https://example.com\\@evil.test', 'https://example.com\n']:
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    script.render_config(invalid, *urls[1:], path)
                self.assertEqual(path.read_text(encoding='utf-8'), output)
