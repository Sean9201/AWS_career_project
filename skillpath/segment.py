"""Split a single job description blob into requirement sections by its own headings.

Lines before any recognised heading, and lines under headings such as 모집분야, go to `unknown`:
they are kept for mention counts, and only a line-level cue (필수/우대) can label them.
"""
import re

# Order matters: a heading like "우대 자격" is preferred, not qualifications.
HEADINGS = (
    ('preferred', r'우대\s*사항|우대\s*조건|우대\s*요건|이런\s*분이(라)?면\s*(더|더욱)|이런\s*경험이\s*있다면|'
                  r'nice\s*to\s*have|preferred|bonus\s*points'),
    ('qualifications', r'자격\s*요건|자격\s*조건|지원\s*자격|필수\s*(요건|역량|사항|조건|자격)|필요\s*역량|필요한\s*역량|'
                       r'이런\s*분(을|과|이)\s*(찾|함께|필요)|requirements|qualifications|must\s*have|who\s*you\s*are'),
    ('responsibilities', r'주요\s*업무|담당\s*업무|업무\s*내용|하는\s*일|합류하(시)?면|responsibilities|what\s*you.?ll\s*do'),
    ('drop', r'근무\s*조건|근무\s*형태|근무지|복지|혜택|채용\s*절차|전형\s*절차|이렇게\s*합류|접수|제출\s*서류|기타\s*사항|'
             r'유의\s*사항|참고해\s*주세요|기업\s*정보|회사\s*소개|benefits|perks|hiring\s*process'),
    ('unknown', r'모집\s*분야|모집\s*인원|포지션|position'),
)
_HEADING = [(name, re.compile(rf'^({pattern})', re.IGNORECASE)) for name, pattern in HEADINGS]
_UNESCAPE = re.compile(r'\\([\[\]~>_*.\-()#!+])')
_DECOR = re.compile(r'^[\W_]+', re.UNICODE)   # emoji, bullets, numbering marks before a heading word
MAX_HEADING = 30


_TABLE_RULE = re.compile(r'^\s*\|?-{3,}[-|\s]*$', re.MULTILINE)


def normalize(text):
    """Turn provider markup into one item per line. Jobkorea puts a whole posting in one table
    cell and separates items with ' * ' and 'ㆍ', so those become line breaks too."""
    text = _UNESCAPE.sub(r'\1', text or '').replace('**', '').replace('\r', '')
    text = _TABLE_RULE.sub('', text)
    text = re.sub(r'^\s*\|\s*|\s*\|\s*$', '', text, flags=re.MULTILINE)
    text = text.replace(' * ', '\n').replace('ㆍ', '\n• ')
    lines = []
    for line in text.split('\n'):
        # Lists flattened into one line ("A - B - C"); a single " - " may be a range like "2 - 3년".
        lines.extend(line.split(' - ') if line.count(' - ') >= 2 else [line])
    return '\n'.join(line.strip() for line in lines)


def heading(line):
    cleaned = _DECOR.sub('', line.strip()).rstrip(':： ').strip()
    cleaned = re.sub(r'^\d+[.)]\s*', '', cleaned)
    if not cleaned or len(cleaned) > MAX_HEADING:
        return None
    for name, pattern in _HEADING:
        if pattern.match(cleaned):
            return name
    return None


def segment(description):
    """Return ({section: text}, found_headings). Sections: qualifications, preferred, responsibilities, unknown."""
    sections = {'qualifications': [], 'preferred': [], 'responsibilities': [], 'unknown': []}
    current, found = 'unknown', []
    for line in normalize(description).split('\n'):
        name = heading(line)
        if name:
            current = name
            found.append(name)
            continue
        if current != 'drop' and line.strip():
            sections[current].append(line.rstrip())
    return {k: '\n'.join(v) for k, v in sections.items() if v}, found
