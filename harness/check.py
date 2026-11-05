"""Harness check: run the project's verification commands and lint the records that feed the improvement loop.

Project-agnostic. Everything project-specific comes from harness.toml at the project root.
Notes use YAML-style frontmatter so Obsidian shows them as properties and this script reads the same fields.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import tomllib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FAILURE_STATUSES = {'open', 'fixed'}
RULE_STATUSES = {'candidate', 'trial', 'promoted', 'retired'}
ENFORCEMENTS = {'structure', 'check', 'test', 'text'}
SECRET = re.compile(r'AKIA[0-9A-Z]{16}|sk-ant-[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'
                    r'|(?i:\b(password|passwd|secret_key|api_key)\s*[:=]\s*[^\s<>`]{8,})')
_LINK = re.compile(r'^\[\[([^\]|]+)(?:\|[^\]]*)?\]\]$')


# ---- frontmatter -----------------------------------------------------------------

def _clean(value):
    value = value.strip().strip('"').strip("'").strip()
    link = _LINK.match(value)
    return link.group(1) if link else value


def _inline(value):
    value = value.strip()
    if not value:
        return None
    if value.startswith('[') and value.endswith(']') and not value.startswith('[['):
        return [_clean(v) for v in value[1:-1].split(',') if v.strip()]
    return _clean(value)


def frontmatter(text):
    """Flat keys, inline lists and block lists — the subset Obsidian properties write."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}
    data, key = {}, None
    for line in lines[1:]:
        if line.strip() == '---':
            return data
        stripped = line.strip()
        if stripped.startswith('- ') and key:
            data[key] = (data[key] if isinstance(data[key], list) else []) + [_clean(stripped[2:])]
        elif ':' in line and not line[:1].isspace():
            key, _, value = line.partition(':')
            key = key.strip()
            data[key] = _inline(value)
    return {}   # unterminated frontmatter is treated as none


def as_list(value):
    return value if isinstance(value, list) else ([value] if value else [])


def notes(directory):
    """{id: (path, frontmatter, body)} for every markdown note in a directory."""
    found = {}
    directory = Path(directory)
    if not directory.is_dir():
        return found
    for path in sorted(directory.glob('*.md')):
        text = path.read_text(encoding='utf-8')
        meta = frontmatter(text)
        found[meta.get('id') or path.stem] = (path, meta, text)
    return found


# ---- lint ------------------------------------------------------------------------

def failure_types(path):
    return set(re.findall(r'^\|\s*`([a-z-]+)`\s*\|', Path(path).read_text(encoding='utf-8'), re.M))


SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'outputs'}


def test_names(directory):
    names = set()
    for path in Path(directory).rglob('*.py'):
        if SKIP_DIRS & set(path.parts):
            continue
        names.update(re.findall(r'^\s*def (test_\w+)\(', path.read_text(encoding='utf-8'), re.M))
    return names


def lint(root, cfg):
    """Return (problems, info). Problems fail the check; info is reported only."""
    p, limits = cfg['paths'], cfg.get('limits', {})
    problems, info = [], []
    types = failure_types(root / p['failure_types'])
    tests = test_names(root / p['tests'])
    failures = notes(root / p['failures'])
    project_rules = notes(root / p['rules'])
    core_rules = notes(root / p['core_rules'])
    work_orders = notes(root / p['work_orders'])

    for fid, (path, m, _) in failures.items():
        where = path.relative_to(root).as_posix()
        if m.get('failure_type') not in types:
            problems.append(f'{where}: failure_type "{m.get("failure_type")}"이(가) 원인 유형 목록에 없음')
        if m.get('status') not in FAILURE_STATUSES:
            problems.append(f'{where}: status는 {sorted(FAILURE_STATUSES)} 중 하나')
        if m.get('status') == 'fixed':
            test = m.get('regression_test')
            if not test:
                problems.append(f'{where}: fixed인데 regression_test가 없음')
            elif test not in tests:
                problems.append(f'{where}: 회귀 테스트 {test}를 {p["tests"]}에서 찾지 못함')
        for rule in as_list(m.get('rule')):
            if rule not in project_rules and rule not in core_rules:
                problems.append(f'{where}: 연결된 규칙 {rule}이(가) 없음')

    promoted = 0
    for rules, is_core in ((project_rules, False), (core_rules, True)):
        for rid, (path, m, _) in rules.items():
            where = path.relative_to(root).as_posix()
            status, sources = m.get('status'), as_list(m.get('sources'))
            if status not in RULE_STATUSES:
                problems.append(f'{where}: status는 {sorted(RULE_STATUSES)} 중 하나')
            if m.get('enforcement') not in ENFORCEMENTS:
                problems.append(f'{where}: enforcement는 {sorted(ENFORCEMENTS)} 중 하나')
            if not sources:
                problems.append(f'{where}: 출처 실패(sources)가 없음')
            if not is_core:   # core rules cite failures from other projects
                problems += [f'{where}: 출처 {s}이(가) 없음' for s in sources if s not in failures]
            if status == 'promoted':
                promoted += 1
                if not is_core:
                    problems.append(f'{where}: promoted 규칙은 {p["core_rules"]}에 있어야 함')
                if not m.get('approved_by'):
                    problems.append(f'{where}: promoted인데 approved_by가 없음')
                if len(sources) < 2 and len(as_list(m.get('projects'))) < 2:
                    problems.append(f'{where}: 승격에는 출처 실패 2건 또는 프로젝트 2곳이 필요')
    if promoted > limits.get('core_rules', 20):
        problems.append(f'공통 규칙 {promoted}개가 상한 {limits.get("core_rules", 20)}개를 넘음')

    active = [wid for wid, (_, m, _) in work_orders.items() if m.get('status') == 'active']
    for wid in active:
        path, m, text = work_orders[wid]
        where = path.relative_to(root).as_posix()
        if not as_list(m.get('verify')):
            problems.append(f'{where}: 진행 중 작업지시서에 verify 명령이 없음')
        if '## 완료 조건' not in text:
            problems.append(f'{where}: 진행 중 작업지시서에 "## 완료 조건" 절이 없음')

    progress = root / p['progress']
    if progress.exists():
        text = progress.read_text(encoding='utf-8')
        lines = len(text.splitlines())
        if lines > limits.get('progress_lines', 40):
            problems.append(f'{p["progress"]}: {lines}줄 (상한 {limits.get("progress_lines", 40)}). 이력은 결정·실패 노트로 옮길 것')
        current = frontmatter(text).get('active_work_order')
        if current and current not in active:
            problems.append(f'{p["progress"]}: active_work_order {current}이(가) 진행 중 작업지시서가 아님')
    else:
        problems.append(f'{p["progress"]} 없음')

    for path in _scan_files(root, p.get('secret_scan', [])):
        for n, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
            if SECRET.search(line):
                problems.append(f'{path.relative_to(root).as_posix()}:{n}: 비밀값으로 보이는 문자열')

    counts = Counter(m.get('failure_type') for _, m, _ in failures.values())
    info += [f'원인 유형 {t}: {n}건 — 반복 발생, 규칙 강화·승격 검토' for t, n in counts.items() if n >= 2]
    info.append(f"실패 {len(failures)}건 (open {sum(m.get('status') == 'open' for _, m, _ in failures.values())}) · "
                f"규칙 {dict(Counter(m.get('status') for _, m, _ in [*project_rules.values(), *core_rules.values()]))} · "
                f"진행 중 작업지시서 {active or '없음'}")
    return problems, info, (active[0] if len(active) == 1 else ';'.join(active))


def _scan_files(root, entries):
    for entry in entries:
        path = root / entry
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from (f for f in path.rglob('*') if f.suffix in {'.md', '.json', '.toml', '.py'})


# ---- run -------------------------------------------------------------------------

def _metric(data, dotted):
    for part in dotted.split('.'):
        data = data[part]
    return data


def run_commands(root, runs):
    results, problems, metrics = [], [], {}
    for item in runs:
        command = item['command']
        if command.startswith('python '):
            command = f'"{sys.executable}" {command[len("python "):]}'
        started = time.monotonic()
        done = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True,
                              encoding='utf-8', errors='replace', env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        ok = done.returncode == 0
        if not ok:
            tail = (done.stderr or done.stdout).strip().splitlines()[-5:]
            problems.append(f'[{item["name"]}] 종료 코드 {done.returncode}\n    ' + '\n    '.join(tail))
        if ok and item.get('json'):
            try:
                data = json.loads(done.stdout)
                for dotted, minimum in item.get('thresholds', {}).items():
                    value = _metric(data, dotted)
                    metrics[f'{item["name"]}.{dotted}'] = value
                    if value < minimum:
                        ok = False
                        problems.append(f'[{item["name"]}] {dotted} = {value} < 기준 {minimum}')
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                ok = False
                problems.append(f'[{item["name"]}] 결과 JSON에서 기준값을 읽지 못함: {exc}')
        results.append((item['name'], ok, round(time.monotonic() - started, 1)))
    return results, problems, metrics


def record(root, cfg, work_order, ok, problems, results, metrics):
    path = root / cfg['paths']['metrics']
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(['run_at', 'harness_version', 'work_order', 'ok', 'problems', 'commands', 'metrics'])
        writer.writerow([datetime.now(timezone.utc).isoformat(timespec='seconds'),
                         cfg['project'].get('harness_version', ''), work_order, ok, len(problems),
                         ';'.join(f'{n}:{"ok" if r else "fail"}:{s}s' for n, r, s in results),
                         json.dumps(metrics, ensure_ascii=False)])


def find_root(start):
    for path in [start, *start.parents]:
        if (path / 'harness.toml').exists():
            return path
    raise SystemExit('harness.toml을 찾지 못했습니다.')


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='하네스 검사')
    parser.add_argument('--no-run', action='store_true', help='테스트·평가 명령을 실행하지 않고 기록만 검사')
    args = parser.parse_args(argv)
    root = find_root(Path.cwd().resolve())
    cfg = tomllib.loads((root / 'harness.toml').read_text(encoding='utf-8'))

    problems, info, work_order = lint(root, cfg)
    results, metrics = [], {}
    if not args.no_run:
        results, run_problems, metrics = run_commands(root, cfg.get('run', []))
        problems += run_problems
    ok = not problems
    if not args.no_run:
        record(root, cfg, work_order, ok, problems, results, metrics)

    for name, passed, seconds in results:
        print(f'{"통과" if passed else "실패"}  {name} ({seconds}s)')
    for k, v in metrics.items():
        print(f'지표  {k} = {v}')
    for line in info:
        print(f'정보  {line}')
    for line in problems:
        print(f'문제  {line}')
    print('결과: 통과' if ok else f'결과: 실패 ({len(problems)}건)')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
