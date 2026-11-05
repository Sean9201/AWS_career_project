"""Score confirmed claims against human labels.

python -m eval.evaluate --gold eval/gold.fixtures.json --claims outputs/latest/claims.json

skill:      (posting, skill) found at all
labeled:    (posting, skill, required|preferred) found with the right label
"""
import argparse
import json
from pathlib import Path


def _prf(predicted, gold):
    tp = len(predicted & gold)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'tp': tp, 'predicted': len(predicted), 'gold': len(gold),
            'precision': round(precision, 3), 'recall': round(recall, 3), 'f1': round(f1, 3)}


def score(gold_labels, claims):
    gold = {(pid, skill, req) for pid, by in gold_labels.items() for req, names in by.items() for skill in names}
    confirmed = [c for c in claims if c['status'] == 'confirmed' and c['posting_id'] in gold_labels]
    labeled = {(c['posting_id'], c['canonical'], c['requirement']) for c in confirmed}
    # A posting that requires a skill in one sentence and prefers it in another counts as required.
    required = {(p, s) for p, s, r in labeled if r == 'required'}
    labeled = {(p, s, r) for p, s, r in labeled if r == 'required' or (p, s) not in required}
    result = {'skill': _prf({(p, s) for p, s, _ in labeled}, {(p, s) for p, s, _ in gold}),
              'labeled': _prf(labeled, gold),
              'status': {k: sum(c['status'] == k for c in claims) for k in ('confirmed', 'uncertain', 'rejected')}}
    result['missed'] = sorted(gold - labeled)
    result['extra'] = sorted(labeled - gold)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gold', default='eval/gold.fixtures.json')
    parser.add_argument('--claims', default='outputs/latest/claims.json')
    args = parser.parse_args()
    gold = json.loads(Path(args.gold).read_text(encoding='utf-8'))['labels']
    claims = json.loads(Path(args.claims).read_text(encoding='utf-8'))
    print(json.dumps(score(gold, claims), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
