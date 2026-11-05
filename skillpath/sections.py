"""Split posting sections into source sentences and decide required/preferred from the source text."""
import re

SECTIONS = {'qualifications': 'required', 'preferred': 'preferred'}
SECTION_LABELS = {'qualifications': '자격요건', 'preferred': '우대사항'}
PREFERRED_CUES = ('우대', '선호', '있으면 좋', '가산점', 'plus', 'preferred')
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
    """A qualification sentence that itself says '우대' is preferred, not required."""
    if section == 'qualifications' and any(cue in sentence.casefold() for cue in PREFERRED_CUES):
        return 'preferred'
    return SECTIONS[section]
