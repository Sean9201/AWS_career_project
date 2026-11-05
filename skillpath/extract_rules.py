"""Dictionary baseline extractor: no model call, fully reproducible, and the comparison point for Bedrock."""
from .models import Claim
from .sections import SECTIONS, requirement, sentences


def extract(posting, skills):
    claims, seen = [], set()
    for section in SECTIONS:
        for _, _, sentence in sentences(posting['sections'].get(section)):
            for m in skills.find(sentence):
                key = (section, sentence, m.skill)
                if key in seen:
                    continue
                seen.add(key)
                claims.append(Claim(posting['id'], section, m.text, sentence,
                                    requirement(section, sentence), 'rules'))
    return claims
