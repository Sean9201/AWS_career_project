import unittest

from skillpath.dedupe import company_key, merge_duplicates, same_job

QUALS = '• 경력 3년 이상\n• Golang 실무 3년 이상\n• AWS 기반 서비스 실전 경험\n• Docker, EKS, Kubernetes 경험\n• RDBMS(MySQL/PostgreSQL) 이해'
PREF = '• On-premise K8s 운영 경험\n• Redis, OpenSearch 활용 경험\n• Prometheus, Grafana 이해'


def posting(company, source, title='백엔드 개발자 경력직 채용', quals=QUALS, pref=PREF, body='has_sections',
            extra=None, date='2026-11-04T00:00:00.000Z'):
    sections = {'qualifications': quals, 'preferred': pref} if quals else {'unknown': title}
    if extra:
        sections.update(extra)
    return {'id': f'{source}-{company}', 'company': company, 'source': source, 'title': title,
            'url': f'https://{source}/x/{company}', 'body_status': body, 'date_created': date, 'sections': sections}


class SameJobTest(unittest.TestCase):
    def test_company_key_ignores_legal_form_and_spacing(self):
        self.assertEqual(company_key('(주)럭스로보'), company_key('주식회사 럭스로보'))
        self.assertEqual(company_key('㈜ 마린 소프트'), company_key('마린소프트'))
        self.assertNotEqual(company_key('럭스로보'), company_key('럭스로봇'))

    def test_same_job_on_two_sites_with_portal_formatting_noise(self):
        # Jobkorea glued a benefits section onto the last preferred bullet and lost 주요업무.
        a = posting('(주)럭스로보', 'saramin_kr', extra={'responsibilities': '• API 설계\n• 분산 시스템 설계'})
        b = posting('주식회사 럭스로보', 'jobkorea_kr', pref=PREF + ' 복지제도 전형절차\n• 서류전형 > 면접\n• 면접일정은 추후 통보')
        self.assertTrue(same_job(a, b))

    def test_same_company_different_jobs_stay_apart(self):
        a = posting('제이투이', 'jobkorea_kr', title='[JAVA SM] 웹서비스 백엔드 운영',
                    quals='• Java 3년\n• Spring 운영 경험\n• Linux 경험\n• MySQL 경험')
        b = posting('제이투이', 'jobkorea_kr', title='[JAVA/VUE SI] 은행 프론트/백엔드',
                    quals='• Vue 경험\n• 카드 개발 경험자\n• 금융 도메인 이해\n• Java 필수')
        self.assertFalse(same_job(a, b))

    def test_same_text_from_different_companies_stays_apart(self):
        self.assertFalse(same_job(posting('A사', 'saramin_kr'), posting('B사', 'jobkorea_kr')))

    def test_image_only_postings_fall_back_to_title(self):
        a = posting('업투유', 'jobkorea_kr', title='업투유 백엔드 개발자 채용', quals=None, body='no_body')
        b = posting('㈜업투유', 'saramin_kr', title='업투유 백엔드 개발자 채용', quals=None, body='no_body')
        c = posting('업투유', 'saramin_kr', title='업투유 프론트 개발자 채용', quals=None, body='no_body')
        self.assertTrue(same_job(a, b))
        self.assertFalse(same_job(a, c))


class MergeTest(unittest.TestCase):
    def test_keeps_the_copy_with_more_sections_and_lists_the_rest(self):
        full = posting('(주)럭스로보', 'saramin_kr', extra={'responsibilities': '• API 설계'})
        partial = posting('주식회사 럭스로보', 'jobkorea_kr', date='2026-11-02T00:00:00.000Z')
        other = posting('다른회사', 'jobkorea_kr')
        kept, merged = merge_duplicates([partial, full, other])
        self.assertEqual(merged, 1)
        self.assertEqual([p['source'] for p in kept], ['saramin_kr', 'jobkorea_kr'])
        self.assertEqual(kept[0]['also_at'], [{'source': 'jobkorea_kr', 'url': partial['url'],
                                               'company': '주식회사 럭스로보', 'date_created': partial['date_created']}])
        self.assertEqual(kept[1]['also_at'], [])

    def test_equal_quality_prefers_earlier_publication(self):
        first = posting('A사', 'jobkorea_kr', date='2026-11-01T00:00:00.000Z')
        repost = posting('A사', 'saramin_kr', date='2026-11-04T00:00:00.000Z')
        kept, _ = merge_duplicates([repost, first])
        self.assertEqual(kept[0]['source'], 'jobkorea_kr')


if __name__ == '__main__':
    unittest.main()
