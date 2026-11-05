import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path

from harness.check import frontmatter, lint
from skillpath.skills import ROOT

CONFIG = tomllib.loads((ROOT / 'harness.toml').read_text(encoding='utf-8'))


class FrontmatterTest(unittest.TestCase):
    def test_obsidian_style_properties(self):
        meta = frontmatter('---\nid: R-1\nsources:\n  - "[[F-001]]"\n  - "[[F-002|두번째]]"\n'
                           'tags: [a, b]\napproved_by:\n---\n# 본문\nid: 무시')
        self.assertEqual(meta, {'id': 'R-1', 'sources': ['F-001', 'F-002'], 'tags': ['a', 'b'], 'approved_by': None})

    def test_missing_or_unterminated_frontmatter(self):
        self.assertEqual(frontmatter('# 제목'), {})
        self.assertEqual(frontmatter('---\nid: x\n# 닫히지 않음'), {})


class LintTest(unittest.TestCase):
    """Builds a minimal project in a temp dir and checks that broken records are reported."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / 'harness').mkdir()
        shutil.copy(ROOT / 'harness/failure_types.md', self.tmp / 'harness/failure_types.md')
        (self.tmp / 'tests').mkdir()
        (self.tmp / 'tests/test_x.py').write_text('def test_kept():\n    pass\n', encoding='utf-8')
        self.write('docs/progress.md', '---\nactive_work_order: WO-1\n---\n# 상태\n')
        self.write('work_orders/WO-1.md', '---\nid: WO-1\nstatus: active\nverify:\n  - python -m x\n---\n## 완료 조건\n- a\n')

    def write(self, rel, text):
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def failure(self, fid='F-1', test='test_kept', status='fixed', kind='silent-drop'):
        self.write(f'docs/failures/{fid}.md', f'---\nid: {fid}\nfailure_type: {kind}\nstatus: {status}\n'
                                              f'regression_test: {test}\n---\n')

    def rule(self, status='candidate', sources=('F-1',), where='docs/rules', approved=''):
        listed = ''.join(f'  - "[[{s}]]"\n' for s in sources)
        self.write(f'{where}/R-1.md', f'---\nid: R-1\nstatus: {status}\nenforcement: check\n'
                                      f'sources:\n{listed}approved_by: {approved}\n---\n')

    def problems(self):
        return lint(self.tmp, CONFIG)[0]

    def test_clean_project_passes(self):
        self.failure()
        self.rule()
        self.assertEqual(self.problems(), [])

    def test_fixed_failure_needs_existing_regression_test(self):
        self.failure(test='test_missing')
        self.assertTrue(any('test_missing' in p for p in self.problems()))

    def test_unknown_failure_type(self):
        self.failure(kind='bad-luck')
        self.assertTrue(any('bad-luck' in p for p in self.problems()))

    def test_active_work_order_needs_verify(self):
        self.write('work_orders/WO-1.md', '---\nid: WO-1\nstatus: active\nverify:\n---\n# 조건 없음\n')
        found = self.problems()
        self.assertTrue(any('verify' in p for p in found))
        self.assertTrue(any('완료 조건' in p for p in found))

    def test_promotion_requires_core_location_two_sources_and_approval(self):
        self.failure()
        self.rule(status='promoted')
        found = self.problems()
        self.assertTrue(any('harness/rules' in p for p in found))
        self.assertTrue(any('approved_by' in p for p in found))
        self.assertTrue(any('2건' in p for p in found))

    def test_promoted_core_rule_with_evidence_passes(self):
        self.failure()
        self.rule(status='promoted', sources=('a:F-1', 'b:F-9'), where='harness/rules', approved='승현')
        self.assertEqual(self.problems(), [])

    def test_rule_source_must_exist(self):
        self.rule(sources=('F-404',))
        self.assertTrue(any('F-404' in p for p in self.problems()))

    def test_secret_like_text_is_reported(self):
        self.write('docs/note.md', 'api_key = abcdefgh12345\n')
        self.assertTrue(any('비밀값' in p for p in self.problems()))

    def test_repeated_failure_type_is_flagged_for_review(self):
        self.failure('F-1')
        self.failure('F-2')
        info = lint(self.tmp, CONFIG)[1]
        self.assertTrue(any('silent-drop: 2건' in line for line in info))


class ProjectRecordsTest(unittest.TestCase):
    def test_this_project_records_are_consistent(self):
        self.assertEqual(lint(ROOT, CONFIG)[0], [])


if __name__ == '__main__':
    unittest.main()
