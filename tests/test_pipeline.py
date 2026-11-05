import json
import tempfile
import unittest
from pathlib import Path

from eval.evaluate import score
from skillpath import extract_rules
from skillpath.analyze import demand
from skillpath.extract_bedrock import BedrockExtractor
from skillpath.models import Claim
from skillpath.pipeline import run
from skillpath.recommend import course_coverage, recommend
from skillpath.sections import requirement, sentences
from skillpath.skills import ROOT, SkillDictionary
from skillpath.verify import verify

SKILLS = SkillDictionary.load()


def posting(qualifications='', preferred='', pid='p1', role='백엔드'):
    return {'id': pid, 'role': role, 'sections': {'qualifications': qualifications, 'preferred': preferred}}


class SkillMatchingTest(unittest.TestCase):
    def names(self, text):
        return [m.skill for m in SKILLS.find(text)]

    def test_java_is_not_javascript(self):
        self.assertEqual(self.names('JavaScript 비동기 처리'), ['JavaScript'])
        self.assertEqual(self.names('Java와 JavaScript'), ['Java', 'JavaScript'])

    def test_korean_alias_and_particles(self):
        self.assertEqual(self.names('아마존 웹 서비스(AWS) 운영'), ['AWS', 'AWS'])
        self.assertEqual(self.names('Python을 활용한 파이썬 개발'), ['Python', 'Python'])

    def test_longest_alias_wins(self):
        self.assertEqual(self.names('Spring Boot와 MySQL, PostgreSQL'), ['Spring', 'MySQL', 'PostgreSQL'])
        self.assertEqual(self.names('GitHub 사용'), [])

    def test_canonical_from_free_text(self):
        self.assertEqual(SKILLS.canonical('k8s'), 'Kubernetes')
        self.assertEqual(SKILLS.canonical('AWS 운영'), 'AWS')
        self.assertIsNone(SKILLS.canonical('Airbyte'))
        self.assertIsNone(SKILLS.canonical('Java와 Python'))


class SectionTest(unittest.TestCase):
    def test_offsets_point_into_source(self):
        text = '- Python 경험\n• Docker 우대'
        for start, end, sentence in sentences(text):
            self.assertEqual(text[start:end], sentence)
        self.assertEqual([s for _, _, s in sentences(text)], ['Python 경험', 'Docker 우대'])

    def test_preferred_cue_inside_qualifications(self):
        self.assertEqual(requirement('qualifications', '쿠버네티스 경험이 있으면 우대합니다'), 'preferred')
        self.assertEqual(requirement('qualifications', 'Python 경험'), 'required')


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.post = posting('- Python 개발 경험\n- AWS 운영 경험', '- Docker 경험')

    def claim(self, skill, evidence, section='qualifications', req='required'):
        return Claim('p1', section, skill, evidence, req, 'test')

    def test_confirmed_with_span(self):
        v = verify(self.claim('파이썬', 'Python 개발 경험'), self.post, SKILLS)
        self.assertEqual((v.status, v.canonical), ('confirmed', 'Python'))
        self.assertEqual(self.post['sections']['qualifications'][slice(*v.span)], 'Python 개발 경험')

    def test_invented_evidence_is_rejected(self):
        v = verify(self.claim('Kubernetes', 'Kubernetes 운영 경험'), self.post, SKILLS)
        self.assertEqual((v.status, v.reasons), ('rejected', ['evidence_not_in_source']))

    def test_skill_missing_from_its_evidence_is_uncertain(self):
        v = verify(self.claim('Docker', 'AWS 운영 경험'), self.post, SKILLS)
        self.assertEqual((v.status, v.reasons), ('uncertain', ['skill_not_in_evidence']))

    def test_unknown_skill_and_label_conflict_are_uncertain(self):
        v = verify(self.claim('Airbyte', 'Docker 경험', 'preferred', 'required'), self.post, SKILLS)
        self.assertEqual(v.status, 'uncertain')
        self.assertEqual(v.reasons, ['skill_not_in_dictionary', 'requirement_conflict'])

    def test_whitespace_difference_still_traces(self):
        v = verify(self.claim('AWS', 'AWS  운영 경험'), self.post, SKILLS)
        self.assertEqual((v.status, v.span), ('confirmed', None))


class DemandAndRecommendTest(unittest.TestCase):
    def setUp(self):
        self.postings = [posting('- Python 경험\n- AWS 경험', '- Docker 경험', 'p1'),
                         posting('- Python 경험', '- AWS 경험 우대', 'p2')]
        claims = [c for p in self.postings for c in extract_rules.extract(p, SKILLS)]
        self.rows = demand(self.postings, [verify(c, self.postings[int(c.posting_id[1]) - 1], SKILLS) for c in claims])

    def row(self, skill):
        return next(r for r in self.rows if r['skill'] == skill)

    def test_counts_postings_not_mentions(self):
        self.assertEqual((self.row('Python')['required_n'], self.row('Python')['required_share']), (2, 1.0))
        self.assertEqual((self.row('AWS')['required_n'], self.row('AWS')['preferred_n']), (1, 1))

    def test_prerequisites_do_not_count_as_coverage(self):
        course = {'id': 'c', 'title': 'Spring 입문', 'description': '', 'curriculum': [], 'prerequisites': 'Java 기초'}
        self.assertEqual(set(course_coverage(course, SKILLS)), {'Spring'})

    def test_recommendation_reason_cites_demand_and_course_text(self):
        courses = [{'id': 'c1', 'title': '클라우드 입문', 'description': 'AWS로 서비스를 배포합니다.',
                    'curriculum': [], 'prerequisites': 'Python 기초', 'level': '입문', 'provider': 'x'}]
        result = recommend('백엔드', ['파이썬', '모르는기술'], self.rows, courses, SKILLS)
        self.assertEqual(result['unrecognized_inputs'], ['모르는기술'])
        aws = next(i for i in result['items'] if i['gap']['skill'] == 'AWS')
        self.assertIn('2건 중 AWS 필수 1건, 우대 1건', aws['reason'])
        self.assertIn('소개에서 확인: "AWS로 서비스를 배포합니다."', aws['reason'])
        self.assertEqual(aws['courses'][0]['missing_prerequisites'], [])
        docker = next(i for i in result['items'] if i['gap']['skill'] == 'Docker')
        self.assertEqual(docker['courses'], [])
        self.assertIn('확인된 과정이 아직 없습니다', docker['reason'])

    def test_every_missing_skill_is_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(ROOT / 'data/fixtures/jobs.json', ROOT / 'data/fixtures/courses.json', tmp)
            rows = json.loads((Path(tmp) / 'demand.json').read_text(encoding='utf-8'))
        demanded = {r['skill'] for r in rows if r['role'] == '백엔드 개발자'}
        result = recommend('백엔드 개발자', ['Java'], rows, [], SKILLS)
        self.assertEqual({i['gap']['skill'] for i in result['items']}, demanded - {'Java'})
        self.assertIn('Go', {i['gap']['skill'] for i in result['items']})

    def test_curriculum_is_preferred_over_title_as_evidence(self):
        course = {'id': 'c', 'title': 'AWS 입문', 'description': '', 'curriculum': ['AWS 배포 실습'], 'prerequisites': ''}
        self.assertEqual(course_coverage(course, SKILLS)['AWS'], ('curriculum', 'AWS 배포 실습'))


class FakeResponse:
    def __init__(self, items, stop_reason='end_turn'):
        from skillpath.extract_bedrock import Extraction
        self.parsed_output = Extraction.model_validate({'items': items}) if items is not None else None
        self.stop_reason = stop_reason
        self.usage = type('Usage', (), {'input_tokens': 10, 'output_tokens': 5})()


class FakeClient:
    def __init__(self, response):
        self.calls, self.response = 0, response
        self.messages = self

    def parse(self, **kwargs):
        self.calls += 1
        return self.response


class BedrockExtractorTest(unittest.TestCase):
    def test_cached_and_verified_by_code(self):
        post = posting('- Python 개발 경험')
        items = [{'skill': 'Python', 'evidence': 'Python 개발 경험', 'section': 'qualifications', 'requirement': 'required'},
                 {'skill': 'Kubernetes', 'evidence': 'k8s 운영', 'section': 'qualifications', 'requirement': 'required'}]
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient(FakeResponse(items))
            extractor = BedrockExtractor('model', 'region', tmp, client=client)
            first = extractor.extract(post)
            second = extractor.extract(post)
        self.assertEqual((client.calls, extractor.usage['cache_hits']), (1, 1))
        self.assertEqual([c.skill for c in first], [c.skill for c in second])
        self.assertEqual([verify(c, post, SKILLS).status for c in first], ['confirmed', 'rejected'])

    def test_truncated_answer_is_an_error_not_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            extractor = BedrockExtractor('model', 'region', tmp, client=FakeClient(FakeResponse(None, 'max_tokens')))
            with self.assertRaises(RuntimeError):
                extractor.extract(posting('- Python'))


class FixtureRunTest(unittest.TestCase):
    def test_baseline_run_matches_fixture_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = run(ROOT / 'data/fixtures/jobs.json', ROOT / 'data/fixtures/courses.json', tmp)
            claims = json.loads((Path(tmp) / 'claims.json').read_text(encoding='utf-8'))
        gold = json.loads((ROOT / 'eval/gold.fixtures.json').read_text(encoding='utf-8'))['labels']
        self.assertTrue(info['synthetic'])
        self.assertEqual(score(gold, claims)['labeled']['f1'], 1.0)


if __name__ == '__main__':
    unittest.main()
