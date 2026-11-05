import unittest

from skillpath.analyze import demand
from skillpath.extract_rules import extract
from skillpath.sections import requirement
from skillpath.segment import normalize, segment
from skillpath.skills import SkillDictionary
from skillpath.sources.techmap_adapter import convert
from skillpath.verify import verify

SKILLS = SkillDictionary.load()


class SegmentTest(unittest.TestCase):
    def test_saramin_style_emoji_headings(self):
        text = '소개 문장\n📋 주요업무  \n• API 개발\n📋 자격요건  \n• Java 경험\n📋 우대사항  \n• Kafka 경험\n🏠 근무조건\n• 연봉 협의'
        sections, found = segment(text)
        self.assertEqual(found, ['responsibilities', 'qualifications', 'preferred', 'drop'])
        self.assertEqual(sections, {'qualifications': '• Java 경험', 'preferred': '• Kafka 경험',
                                    'responsibilities': '• API 개발', 'unknown': '소개 문장'})

    def test_jobkorea_single_cell_with_star_and_dot_separators(self):
        text = '| 회사 소개 담당업무 ㆍ 백엔드 개발 * * * 자격요건 * ㆍ경력 1년 * * * 우대사항 및 필요기술 * ㆍBackend: PHP, MySQL |'
        sections, found = segment(text)
        self.assertIn('qualifications', found)
        self.assertIn('MySQL', sections['preferred'])

    def test_conversational_headings_do_not_fall_under_previous_section(self):
        text = ('### 합류하시면 함께 할 업무예요\n- API 설계\n### 이런 분과 함께 하고 싶어요\n'
                'Java 경험 - SQL 설계 경험 - Docker 경험\n### 이런 분이라면 더욱 좋아요\n- Kafka 경험\n'
                '### 이렇게 합류해요\n- 서류 > 면접')
        sections, found = segment(text)
        self.assertEqual(found, ['responsibilities', 'qualifications', 'preferred', 'drop'])
        self.assertEqual(sections['qualifications'].split('\n'), ['Java 경험', 'SQL 설계 경험', 'Docker 경험'])
        self.assertNotIn('Docker', sections['responsibilities'])

    def test_single_dash_range_is_not_split(self):
        self.assertEqual(normalize('경력 2 - 3년'), '경력 2 - 3년')

    def test_long_lines_are_not_headings(self):
        sections, found = segment('4. 우대사항 : Websocket, SSE, Kafka, Redis 등 실시간 처리 경험')
        self.assertEqual(found, [])
        self.assertIn('Kafka', sections['unknown'])

    def test_markdown_escapes_removed(self):
        self.assertEqual(normalize(r'\[여의도\] 2\~4년 **굵게**'), '[여의도] 2~4년 굵게')


class RequirementCueTest(unittest.TestCase):
    def test_line_cues_label_unknown_text(self):
        self.assertEqual(requirement('unknown', '필수스킬 : Java'), 'required')
        self.assertEqual(requirement('unknown', '주요기술 (우대)'), 'preferred')
        self.assertEqual(requirement('unknown', 'Java, Spring'), 'unknown')
        self.assertEqual(requirement('responsibilities', 'API 개발'), 'responsibility')


class AdapterAndDemandTest(unittest.TestCase):
    def item(self, description, url):
        return {'jsonLD': {'description': description, 'url': url, 'title': 't',
                           'hiringOrganization': {'name': 'c'}}, 'source': 'saramin_kr', 'city': '서울'}

    def test_image_only_posting_is_kept_but_excluded_from_denominator(self):
        good = convert(self.item('📋 자격요건\n• Java 경험\n📋 우대사항\n• Docker 경험', 'u1'), '백엔드', 'now')
        stub = convert(self.item('" border="0"> * 경력: 2년', 'u2'), '백엔드', 'now')
        self.assertEqual((good['body_status'], stub['body_status']), ('has_sections', 'no_body'))
        claims = [c for p in (good, stub) for c in extract(p, SKILLS)]
        rows = demand([good, stub], [verify(c, good if c.posting_id == good['id'] else stub, SKILLS) for c in claims])
        java = next(r for r in rows if r['skill'] == 'Java')
        self.assertEqual((java['postings'], java['excluded_postings'], java['required_n']), (1, 1, 1))


if __name__ == '__main__':
    unittest.main()
