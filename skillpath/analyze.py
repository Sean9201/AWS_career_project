"""Demand per role, computed by code from confirmed claims only. Uncertain claims are counted, not merged."""
from collections import defaultdict


def demand(postings, verified):
    totals = defaultdict(int)
    for p in postings:
        totals[p['role']] += 1
    roles = {p['id']: p['role'] for p in postings}
    cells = defaultdict(lambda: {'required': set(), 'preferred': set(), 'uncertain': set(), 'evidence': []})
    for v in verified:
        if v.status == 'rejected' or v.canonical is None:
            continue
        cell = cells[(roles[v.claim.posting_id], v.canonical)]
        if v.status == 'uncertain':
            cell['uncertain'].add(v.claim.posting_id)
            continue
        cell[v.claim.requirement].add(v.claim.posting_id)
        cell['evidence'].append({'posting_id': v.claim.posting_id, 'requirement': v.claim.requirement,
                                 'section': v.claim.section, 'quote': v.claim.evidence})
    rows = []
    for (role, skill), cell in cells.items():
        required = cell['required']
        preferred = cell['preferred'] - required   # a posting that requires a skill is not also "preferred"
        mentioned = required | preferred
        rows.append({'role': role, 'skill': skill, 'postings': totals[role],
                     'required_n': len(required), 'preferred_n': len(preferred),
                     'uncertain_n': len(cell['uncertain'] - mentioned),
                     'required_share': len(required) / totals[role],
                     'mention_share': len(mentioned) / totals[role],
                     'evidence': cell['evidence']})
    return sorted(rows, key=lambda r: (r['role'], -r['required_n'], -r['mention_share'], r['skill']))
