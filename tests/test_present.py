import unittest

from skillpath.present import evidence_label, group_evidence


def ev(pid, section, requirement, quote):
    return {'posting_id': pid, 'section': section, 'requirement': requirement, 'quote': quote}


class GroupEvidenceTest(unittest.TestCase):
    def test_one_entry_per_posting_with_strongest_verdict_first(self):
        evidence = [ev('p2', 'unknown', 'unknown', '백엔드(JSP/JAVA기반) 경력 개발자 모집'),
                    ev('p1', 'unknown', 'unknown', 'JAVA, Python'),
                    ev('p1', 'unknown', 'required', '필수 : 자바, 파이썬 소스 코드 이해 가능'),
                    ev('p2', 'qualifications', 'required', 'Java 기반 백엔드 개발 실무 경력')]
        grouped = group_evidence(evidence)
        self.assertEqual([g['posting_id'] for g in grouped], ['p2', 'p1'])
        self.assertEqual([g['requirement'] for g in grouped], ['required', 'required'])
        # Inside a posting the sentence that decided the verdict comes first.
        self.assertEqual([s['requirement'] for s in grouped[1]['sentences']], ['required', 'unknown'])
        self.assertEqual(len(grouped[1]['sentences']), 2)


class EvidenceLabelTest(unittest.TestCase):
    def test_labels_say_how_the_sentence_was_judged(self):
        self.assertEqual(evidence_label('qualifications', 'required'), '필수 · 자격요건 섹션')
        self.assertEqual(evidence_label('preferred', 'preferred'), '우대 · 우대사항 섹션')
        self.assertIn("문장에 '필수' 표기", evidence_label('unknown', 'required'))
        self.assertIn("자격요건 안의 '우대'", evidence_label('qualifications', 'preferred'))
        self.assertTrue(evidence_label('unknown', 'unknown').startswith('언급만'))
        self.assertNotIn('구분 없음', evidence_label('unknown', 'unknown'))


if __name__ == '__main__':
    unittest.main()
