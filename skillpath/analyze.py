"""Demand per role, computed by code from confirmed claims only.

Denominator: postings with a readable body. Image-only postings (body_status `no_body`) are
counted separately and never enter a ratio. Each posting counts once per skill and label, and a
posting that requires a skill is not also counted as preferring it.
"""
from collections import defaultdict

LABELS = ('required', 'preferred', 'responsibility', 'unknown')


def analyzable(posting):
    return posting.get('body_status', 'has_sections') != 'no_body'


def demand(postings, verified):
    totals, excluded = defaultdict(int), defaultdict(int)
    for p in postings:
        (totals if analyzable(p) else excluded)[p['role']] += 1
    by_id = {p['id']: p for p in postings}
    cells = defaultdict(lambda: {**{label: set() for label in LABELS}, 'uncertain': set(), 'evidence': []})
    for v in verified:
        posting = by_id[v.claim.posting_id]
        if v.status == 'rejected' or v.canonical is None or not analyzable(posting):
            continue
        cell = cells[(posting['role'], v.canonical)]
        if v.status == 'uncertain':
            cell['uncertain'].add(posting['id'])
            continue
        cell[v.claim.requirement].add(posting['id'])
        cell['evidence'].append({'posting_id': posting['id'], 'requirement': v.claim.requirement,
                                 'section': v.claim.section, 'quote': v.claim.evidence})
    rows = []
    for (role, skill), cell in cells.items():
        required = cell['required']
        preferred = cell['preferred'] - required
        responsibility = cell['responsibility'] - required - preferred
        unknown = cell['unknown'] - required - preferred - responsibility
        mentioned = required | preferred | responsibility | unknown
        total = totals[role]
        rows.append({'role': role, 'skill': skill, 'postings': total, 'excluded_postings': excluded[role],
                     'required_n': len(required), 'preferred_n': len(preferred),
                     'responsibility_n': len(responsibility), 'unknown_n': len(unknown),
                     'mention_n': len(mentioned), 'uncertain_n': len(cell['uncertain'] - mentioned),
                     'required_share': len(required) / total if total else 0.0,
                     'mention_share': len(mentioned) / total if total else 0.0,
                     'evidence': cell['evidence']})
    return sorted(rows, key=lambda r: (r['role'], -r['required_n'], -r['mention_share'], r['skill']))
