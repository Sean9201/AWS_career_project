"""Code-side checks on every extractor claim. This is where flexibility meets the source text.

confirmed  evidence is in the posting, the skill is in that evidence, and the label matches the source
uncertain  evidence is real, but the skill is unknown/ambiguous or the required/preferred label disagrees
rejected   evidence is not in the posting (the claim cannot be traced to the source)
"""
import re

from .models import VerifiedClaim
from .sections import SECTIONS, requirement

_SPACE = re.compile(r'\s+')


def _locate(evidence, source):
    evidence = evidence.strip()
    if not evidence:
        return None, False
    at = source.find(evidence)
    if at >= 0:
        return (at, at + len(evidence)), True
    # Whitespace-only differences still trace to the source, but no exact span is claimed.
    return None, _SPACE.sub(' ', evidence) in _SPACE.sub(' ', source)


def verify(claim, posting, skills):
    if claim.section not in SECTIONS:
        return VerifiedClaim(claim, 'rejected', reasons=['unknown_section'])
    source = posting['sections'].get(claim.section) or ''
    span, found = _locate(claim.evidence, source)
    if not found:
        return VerifiedClaim(claim, 'rejected', reasons=['evidence_not_in_source'])

    reasons = []
    canonical = skills.canonical(claim.skill)
    if canonical is None:
        reasons.append('skill_not_in_dictionary')
    elif canonical not in {m.skill for m in skills.find(claim.evidence)}:
        reasons.append('skill_not_in_evidence')
    expected = requirement(claim.section, claim.evidence)
    if claim.requirement != expected:
        reasons.append('requirement_conflict')
    return VerifiedClaim(claim, 'uncertain' if reasons else 'confirmed', canonical, span, expected, reasons)


def verify_all(postings, claims, skills):
    by_id = {p['id']: p for p in postings}
    return [verify(c, by_id[c.posting_id], skills) if c.posting_id in by_id
            else VerifiedClaim(c, 'rejected', reasons=['unknown_posting']) for c in claims]
