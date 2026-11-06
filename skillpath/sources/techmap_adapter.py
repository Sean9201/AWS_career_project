"""Convert saved Techmap search responses into the pipeline's `postings` format.

python -m skillpath.sources.techmap_adapter --role "백엔드 개발자" --out data/real/jobs.json

Nothing is fetched here. Duplicates are dropped at two levels: the same URL seen twice, and the
same job published on several sites (see dedupe.py), which keeps one representative and lists
the other copies in `also_at`. A posting whose description has no recognisable text body (e.g.
an image-only ad) is kept with body_status `no_body` so it is visible in the dataset but
excluded from requirement ratios.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from ..dedupe import merge_duplicates
from ..segment import segment
from ..skills import ROOT
from .techmap import OUT

MIN_BODY = 300   # shorter descriptions without any heading were company-info stubs in the sample


def convert(item, role, collected_at):
    ld = item.get('jsonLD') or {}
    description = ld.get('description') or ''
    sections, headings = segment(description)
    has_requirement_heading = bool({'qualifications', 'preferred'} & set(headings))
    if has_requirement_heading:
        body_status = 'has_sections'
    elif len(description) >= MIN_BODY:
        body_status = 'no_sections'
    else:
        body_status = 'no_body'
    url = ld.get('url') or ''
    org = ld.get('hiringOrganization') or {}
    return {
        'id': f"techmap-{hashlib.sha1(url.encode()).hexdigest()[:12]}",
        'role': role,
        'region': item.get('city') or item.get('state') or '',
        'company': (org.get('name') if isinstance(org, dict) else None) or item.get('company') or '',
        'title': ld.get('title') or item.get('title') or '',
        'url': url,
        'source': item.get('source'),
        'portal': item.get('portal'),
        'language': item.get('language'),
        'date_created': item.get('dateCreated'),
        'collected_at': collected_at,
        'body_status': body_status,
        'evidence_level': 'sentence' if body_status != 'no_body' else 'none',
        'provider_skills': item.get('skills') or [],
        'sections': sections,
    }


def build(raw_files, role):
    postings, seen, duplicates = [], set(), 0
    for path in sorted(raw_files):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('endpoint', '').startswith('search'):
            for item in data['response'].get('result') or []:
                posting = convert(item, role, data['collected_at'])
                if posting['url'] in seen:
                    duplicates += 1
                    continue
                seen.add(posting['url'])
                postings.append(posting)
    postings, cross_source = merge_duplicates(postings)
    summary = {
        'postings': len(postings), 'duplicates_dropped': duplicates, 'cross_source_merged': cross_source,
        'body_status': dict(Counter(p['body_status'] for p in postings)),
        'sources': dict(Counter(p['source'] for p in postings)),
        'languages': dict(Counter(p['language'] for p in postings)),
    }
    return postings, summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', required=True)
    parser.add_argument('--raw', default=OUT / 'raw')
    parser.add_argument('--out', default=ROOT / 'data' / 'real' / 'jobs.json')
    args = parser.parse_args(argv)
    postings, summary = build(Path(args.raw).glob('*.json'), args.role)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'synthetic': False, 'dataset': {'provider': 'Techmap Jobs API', 'role': args.role,
                                                               **summary}, 'postings': postings},
                              ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
