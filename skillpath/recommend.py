"""Gap and course recommendation. Every sentence of the reason is assembled by code from stored evidence."""
from .sections import sentences

# Prerequisites are guidance only: a course that *requires* Java does not *teach* Java.
# Most specific field first: a curriculum line is stronger evidence than a course title.
MATCH_FIELDS = ('curriculum', 'description', 'title')
FIELD_LABELS = {'title': '과정명', 'description': '소개', 'curriculum': '커리큘럼'}


def _course_lines(course):
    for field in MATCH_FIELDS:
        value = course.get(field) or ''
        for text in (value if isinstance(value, list) else [s for _, _, s in sentences(value)]):
            yield field, text


def course_coverage(course, skills):
    """{skill: (field, quote)} for skills the course text itself mentions."""
    covered = {}
    for field, text in _course_lines(course):
        for m in skills.find(text):
            covered.setdefault(m.skill, (field, text))
    return covered


def gaps(role, user_skills, demand_rows, skills):
    have, unknown = set(), []
    for name in user_skills:
        canon = skills.canonical(name)
        if canon:
            have.add(canon)
        else:
            unknown.append(name)
    rows = [r for r in demand_rows if r['role'] == role and r['required_n'] + r['preferred_n'] > 0]
    return [r for r in rows if r['skill'] not in have], sorted(have), unknown


def reason_text(row, course, quote):
    need = (f"{row['role']} 공고 {row['postings']}건 중 {row['skill']} 필수 {row['required_n']}건, "
            f"우대 {row['preferred_n']}건.")
    if course is None:
        return need + f" {row['skill']} 내용을 다룬다고 확인된 과정이 아직 없습니다."
    field, text = quote
    return need + f" '{course['title']}' {FIELD_LABELS[field]}에서 확인: \"{text}\""


def recommend(role, user_skills, demand_rows, courses, skills):
    """One item per missing skill, in demand order. Nothing is dropped; a skill without a course says so."""
    missing, have, unknown = gaps(role, user_skills, demand_rows, skills)
    coverage = {c['id']: course_coverage(c, skills) for c in courses}
    items = []
    for row in missing:
        matches = [c for c in courses if row['skill'] in coverage[c['id']]]
        picks = []
        for course in matches:
            prereq = sorted({m.skill for m in skills.find(course.get('prerequisites') or '')})
            picks.append({'course': course, 'quote': coverage[course['id']][row['skill']],
                          'reason': reason_text(row, course, coverage[course['id']][row['skill']]),
                          'prerequisites': course.get('prerequisites') or '미제공',
                          'level': course.get('level') or '미제공',
                          'missing_prerequisites': [s for s in prereq if s not in have]})
        items.append({'gap': row, 'courses': picks,
                      'reason': picks[0]['reason'] if picks else reason_text(row, None, None)})
    return {'role': role, 'have': have, 'unrecognized_inputs': unknown, 'items': items}
