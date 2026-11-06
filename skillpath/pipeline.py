"""Run collection -> extraction -> verification -> demand, and write every intermediate result to disk.

python -m skillpath.pipeline                      # dictionary baseline, no AWS call
USE_BEDROCK=true python -m skillpath.pipeline --extractor bedrock
"""
import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import extract_rules
from .analyze import demand
from .skills import ROOT, SkillDictionary
from .verify import verify_all


def load(path, key):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    return data[key], bool(data.get('synthetic'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def make_extractor(name):
    if name == 'rules':
        return extract_rules, {}
    if os.getenv('USE_BEDROCK', 'false').lower() != 'true':
        raise SystemExit('Bedrock 호출은 USE_BEDROCK=true일 때만 실행합니다.')
    from .extract_bedrock import BedrockExtractor
    extractor = BedrockExtractor(os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-opus-5-5'),
                                 os.getenv('AWS_REGION', 'ap-northeast-2'),
                                 ROOT / 'data' / 'cache' / 'bedrock')
    return extractor, {'model': extractor.model}


def run(jobs_path, courses_path, out_dir, extractor_name='rules'):
    skills = SkillDictionary.load()
    postings, jobs_synthetic = load(jobs_path, 'postings')
    courses, courses_synthetic = load(courses_path, 'courses')
    extractor, meta = make_extractor(extractor_name)
    claims = [c for p in postings for c in extractor.extract(p, skills)]
    verified = verify_all(postings, claims, skills)
    rows = demand(postings, verified)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write(out / 'postings.json', postings)
    write(out / 'courses.json', courses)
    write(out / 'claims.json', [v.to_dict() for v in verified])
    write(out / 'demand.json', rows)
    write(out / 'review_queue.json', [v.to_dict() for v in verified if v.status != 'confirmed'])
    run_info = {
        'run_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'extractor': extractor_name, **meta, 'usage': getattr(extractor, 'usage', None),
        'jobs': str(jobs_path), 'courses': str(courses_path),
        'jobs_sha256': hashlib.sha256(Path(jobs_path).read_bytes()).hexdigest()[:16],
        'synthetic': jobs_synthetic or courses_synthetic,
        'jobs_synthetic': jobs_synthetic, 'courses_synthetic': courses_synthetic,
        'body_status': dict(Counter(p.get('body_status', 'has_sections') for p in postings)),
        'sources': dict(Counter(p.get('source', 'fixture') for p in postings)),
        'cross_source_merged': sum(len(p.get('also_at') or []) for p in postings),
        'postings': len(postings), 'courses_n': len(courses), 'claims': len(verified),
        'status': dict(Counter(v.status for v in verified)),
    }
    run_info['dictionary_gaps'] = dictionary_gaps(postings, skills)
    write(out / 'run.json', run_info)
    return run_info


def dictionary_gaps(postings, skills, limit=30):
    """Skills the data provider tagged that our dictionary cannot map: candidates for a human to add.
    Provider tags are not evidence; they only point at where the dictionary is blind."""
    counts = Counter(tag for p in postings for tag in set(p.get('provider_skills') or [])
                     if skills.canonical(tag) is None)
    return [{'skill': tag, 'postings': n} for tag, n in counts.most_common(limit)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jobs', default=ROOT / 'data' / 'fixtures' / 'jobs.json')
    parser.add_argument('--courses', default=ROOT / 'data' / 'fixtures' / 'courses.json')
    parser.add_argument('--out', default=ROOT / 'outputs' / 'latest')
    parser.add_argument('--extractor', choices=['rules', 'bedrock'], default='rules')
    args = parser.parse_args()
    print(json.dumps(run(args.jobs, args.courses, args.out, args.extractor), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
