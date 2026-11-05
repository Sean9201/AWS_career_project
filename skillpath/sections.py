"""Split posting sections into source sentences and decide the requirement label from the source text."""
import re

# section -> default label. `unknown` text has no heading we recognise, so only line cues can label it.
SECTIONS = {'qualifications': 'required', 'preferred': 'preferred',
            'responsibilities': 'responsibility', 'unknown': 'unknown'}
SECTION_LABELS = {'qualifications': '자격요건', 'preferred': '우대사항',
                  'responsibilities': '주요업무', 'unknown': '구분 없음'}
PREFERRED_CUES = ('우대', '선호', '있으면 좋', '가산점', 'plus', 'preferred', 'nice to have')
REQUIRED_CUES = ('필수', 'must', 'required')
_LINE = re.compile(r'[^\n]+')
_BULLET = re.compile(r'^[\s\-•·*▪○◦]+')


def sentences(text):
    """Yield (start, end, sentence) with offsets into the original section text."""
    for line in _LINE.finditer(text or ''):
        lead = _BULLET.match(line.group(0))
        start = line.start() + (lead.end() if lead else 0)
        sentence = text[start:line.end()].rstrip()
        if sentence:
            yield start, start + len(sentence), sentence


def requirement(section, sentence):
    """The sentence's own words win over its section: '우대합니다' under 자격요건 is preferred."""
    text = sentence.casefold()
    if section != 'preferred' and any(cue in text for cue in PREFERRED_CUES):
        return 'preferred'
    if section == 'unknown' and any(cue in text for cue in REQUIRED_CUES):
        return 'required'
    return SECTIONS[section]
