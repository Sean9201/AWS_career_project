"""Turn stored claims into what the screen shows: one entry per posting, and a label that says
*how* a sentence was judged so a reader can check it against the quote."""

STRENGTH = {'required': 3, 'preferred': 2, 'responsibility': 1, 'unknown': 0}
LABELS = {'required': '필수', 'preferred': '우대', 'responsibility': '업무', 'unknown': '언급만'}
SECTION_TEXT = {'qualifications': '자격요건', 'preferred': '우대사항', 'responsibilities': '주요업무'}


def evidence_label(section, requirement):
    if section == 'unknown':
        if requirement == 'required':
            return "필수 · 섹션 제목은 없지만 문장에 '필수' 표기"
        if requirement == 'preferred':
            return "우대 · 섹션 제목은 없지만 문장에 '우대' 표기"
        return '언급만 · 제목·소개 등에 등장, 필수/우대 판단 안 함'
    if section == 'qualifications' and requirement == 'preferred':
        return "우대 · 자격요건 안의 '우대' 문장"
    return f'{LABELS[requirement]} · {SECTION_TEXT[section]} 섹션'


def group_evidence(evidence):
    """One entry per posting. The posting's verdict is its strongest sentence, matching analyze.demand."""
    groups = {}
    for item in evidence:
        groups.setdefault(item['posting_id'], []).append(item)
    entries = []
    for posting_id, items in groups.items():
        items.sort(key=lambda e: -STRENGTH[e['requirement']])
        entries.append({'posting_id': posting_id, 'requirement': items[0]['requirement'], 'sentences': items})
    entries.sort(key=lambda g: -STRENGTH[g['requirement']])
    return entries
