"""Merge the same posting published on several job sites.

Two postings are one job when the company is the same after stripping legal-form noise
(㈜, (주), 주식회사 ...) and their requirement sentences mostly overlap. Portal formatting
differs (one site glues a benefits section onto the last bullet, another drops a heading),
so overlap is measured on sentence sets, not exact text.
"""
import re

from .sections import sentences

COMPANY_NOISE = re.compile(r'㈜|\(주\)|\(유\)|주식회사|유한회사|유한책임회사|co\.?,?\s*ltd\.?|inc\.?|corp\.?|[\s\W_]+',
                           re.IGNORECASE)
REQUIREMENT_SECTIONS = ('qualifications', 'preferred')
MIN_SENTENCES = 3          # below this a requirement set is too small to be telling
OVERLAP_THRESHOLD = 0.6    # Jaccard over normalised sentences
BODY_RANK = {'has_sections': 2, 'no_sections': 1, 'no_body': 0}


def company_key(name):
    return COMPANY_NOISE.sub('', name or '').lower()


def _normalise(sentence):
    return re.sub(r'[\W_]+', '', sentence).lower()


def requirement_sentences(posting):
    """Normalised sentences from 자격요건/우대사항; any section when neither exists."""
    sections = posting.get('sections') or {}
    keys = [k for k in REQUIREMENT_SECTIONS if sections.get(k)] or list(sections)
    found = {_normalise(s) for k in keys for _, _, s in sentences(sections.get(k))}
    return {s for s in found if s}


def same_job(a, b):
    if company_key(a.get('company')) != company_key(b.get('company')):
        return False
    sa, sb = requirement_sentences(a), requirement_sentences(b)
    if len(sa) < MIN_SENTENCES or len(sb) < MIN_SENTENCES:
        # Too little text to compare (image-only ads): fall back to the title.
        return _normalise(a.get('title') or '') == _normalise(b.get('title') or '') != ''
    return len(sa & sb) / len(sa | sb) >= OVERLAP_THRESHOLD


def _quality(posting):
    return (BODY_RANK.get(posting.get('body_status'), 0), len(posting.get('sections') or {}),
            # Earlier publication wins ties: it is the original, the rest are reposts.
            -(_sortable_date(posting.get('date_created'))))


def _sortable_date(value):
    return int(re.sub(r'\D', '', value or '')[:14] or 0)


def merge_duplicates(postings):
    """Return (representatives, merged_count). Every representative lists its other copies in `also_at`."""
    groups = []
    for posting in postings:
        for group in groups:
            if same_job(group[0], posting):
                group.append(posting)
                break
        else:
            groups.append([posting])
    merged, result = 0, []
    for group in groups:
        group.sort(key=_quality, reverse=True)
        best, rest = group[0], group[1:]
        best['also_at'] = [{'source': p.get('source'), 'url': p.get('url'), 'company': p.get('company'),
                            'date_created': p.get('date_created')} for p in rest]
        merged += len(rest)
        result.append(best)
    return result, merged
