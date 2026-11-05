import shutil
import tempfile
import tomllib
import unittest
from datetime import date
from pathlib import Path

from harness.check import lint
from harness.init import install, version


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def test_fresh_project_gets_full_setup_that_passes_lint(self):
        created, _ = install(self.root, '새 프로젝트', today=date(2026, 1, 2))
        for rel in ('harness/check.py', 'AGENTS.md', 'CLAUDE.md', 'HOME.md', 'harness.toml',
                    'docs/progress.md', '.obsidian/templates.json', 'work_orders/.gitkeep'):
            self.assertTrue((self.root / rel).exists(), rel)
        self.assertIn('harness/', created)
        config = tomllib.loads((self.root / 'harness.toml').read_text(encoding='utf-8'))
        self.assertEqual(config['project'], {'name': '새 프로젝트', 'harness_version': version()})
        self.assertIn('2026-01-02', (self.root / 'docs/progress.md').read_text(encoding='utf-8'))
        self.assertEqual(lint(self.root, config)[0], [])

    def test_rerun_never_overwrites(self):
        (self.root / 'AGENTS.md').write_text('내 규칙', encoding='utf-8')
        (self.root / '.gitignore').write_text('dist/', encoding='utf-8')
        install(self.root, 'a')
        _, skipped = install(self.root, 'b')
        self.assertEqual((self.root / 'AGENTS.md').read_text(encoding='utf-8'), '내 규칙')
        self.assertIn('AGENTS.md', skipped)
        gitignore = (self.root / '.gitignore').read_text(encoding='utf-8')
        self.assertTrue(gitignore.startswith('dist/\n'))
        self.assertEqual(gitignore.count('# harness'), 1)

    def test_obsidian_templates_keep_their_placeholders(self):
        install(self.root, 'x')
        text = (self.root / 'harness/templates/failure.md').read_text(encoding='utf-8')
        self.assertIn('{{title}}', text)


if __name__ == '__main__':
    unittest.main()
