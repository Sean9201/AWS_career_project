"""Install the harness into a project. Never overwrites existing files, so it is safe to rerun.

python harness/init.py --name "내 프로젝트"                       # harness/ already inside the project
python path/to/ai-harness/harness/init.py --root ../my-app --name "내 앱"   # copy harness/ into another project
"""
import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKELETON = HERE / 'skeleton'
EMPTY_DIRS = ('docs/failures', 'docs/rules', 'docs/decisions', 'work_orders')
GITIGNORE = ('.env', '__pycache__/', '.obsidian/workspace*.json', '.obsidian/plugins/')
SKIP = shutil.ignore_patterns('__pycache__', '*.pyc')


def version():
    for line in (HERE / 'CHANGELOG.md').read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            return line[3:].split()[0]
    return '0.0.0'


def install(root, name, today=None):
    """Return (created, skipped) relative paths."""
    root = Path(root).resolve()
    created, skipped = [], []
    if (root / 'harness').resolve() != HERE:
        if (root / 'harness').exists():
            skipped.append('harness/')
        else:
            shutil.copytree(HERE, root / 'harness', ignore=SKIP)
            created.append('harness/')
    values = {'__PROJECT_NAME__': name, '__TODAY__': (today or date.today()).isoformat(),
              '__HARNESS_VERSION__': version()}
    for source in sorted(p for p in SKELETON.rglob('*') if p.is_file()):
        rel = source.relative_to(SKELETON)
        target = root / rel
        if target.exists():
            skipped.append(rel.as_posix())
            continue
        text = source.read_text(encoding='utf-8')
        for key, value in values.items():
            text = text.replace(key, value)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        created.append(rel.as_posix())
    for rel in EMPTY_DIRS:
        folder = root / rel
        folder.mkdir(parents=True, exist_ok=True)
        if not any(folder.iterdir()):
            (folder / '.gitkeep').touch()
            created.append(f'{rel}/')
    gitignore = root / '.gitignore'
    text = gitignore.read_text(encoding='utf-8') if gitignore.exists() else ''
    missing = [line for line in GITIGNORE if line not in text.splitlines()]
    if missing:
        prefix = ('' if not text or text.endswith('\n') else '\n') + ('\n' if text else '')
        with gitignore.open('a', encoding='utf-8') as f:
            f.write(prefix + '# harness\n' + '\n'.join(missing) + '\n')
        created.append(f'.gitignore (+{len(missing)})')
    return created, skipped


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='하네스 설치')
    parser.add_argument('--root', default='.', help='설치할 프로젝트 폴더 (기본: 현재 폴더)')
    parser.add_argument('--name', help='프로젝트 이름 (기본: 폴더 이름)')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    created, skipped = install(root, args.name or root.name)
    for rel in created:
        print(f'생성  {rel}')
    for rel in skipped:
        print(f'유지  {rel} (이미 있음)')
    print(f'\n하네스 {version()} 설치 완료: {root}')
    print('다음: AGENTS.md 목표·규칙 작성 → harness.toml에 테스트 명령 추가 → python harness/check.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
