"""Techmap Jobs API (via RapidAPI) collector with a hard monthly request cap.

Every request is billed by RapidAPI after the free quota, so the cap is checked and the
counter is written *before* the request is sent. Failed requests are not retried in a loop.

python -m skillpath.sources.techmap count --countryCode kr --dateCreatedMin 2026-10-06 --dateCreatedMax 2026-11-05
python -m skillpath.sources.techmap search --countryCode kr --title 백엔드,backend --pages 1
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ..skills import ROOT

BASE = 'https://daily-international-job-postings.p.rapidapi.com/api/v2/jobs'
HOST = 'daily-international-job-postings.p.rapidapi.com'
OUT = ROOT / 'data' / 'real' / 'techmap'
USAGE = OUT / 'usage.json'
FILTERS = ('countryCode', 'language', 'title', 'skills', 'occupation', 'industry', 'city',
           'dateCreated', 'dateCreatedMin', 'dateCreatedMax', 'isDuplicate', 'source', 'portal', 'sort')


class CapReached(RuntimeError):
    pass


def load_env(path=ROOT / '.env'):
    """Minimal KEY=VALUE reader so no extra dependency is needed. Existing env vars win."""
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip() and not key.strip().startswith('#'):
                os.environ.setdefault(key.strip(), value.strip())


class TechmapClient:
    def __init__(self, key, cap, usage_path=USAGE, opener=urllib.request.urlopen, clock=time):
        if not key:
            raise SystemExit('.env의 TECHMAP_RAPIDAPI_KEY가 비어 있습니다.')
        self.key, self.cap, self.usage_path = key, cap, Path(usage_path)
        self.opener, self.clock = opener, clock

    def _usage(self):
        data = json.loads(self.usage_path.read_text(encoding='utf-8')) if self.usage_path.exists() else {}
        return data, datetime.now(timezone.utc).strftime('%Y-%m')

    def used(self):
        data, month = self._usage()
        return data.get(month, 0)

    def _spend(self):
        data, month = self._usage()
        if data.get(month, 0) >= self.cap:
            raise CapReached(f'이번 달 요청 {data.get(month, 0)}회로 상한 {self.cap}회에 도달해 호출하지 않습니다.')
        # Basic plan allows 1 request per second. The last request time is persisted so that
        # separate command runs are spaced too, not only requests within one process.
        wait = 1.1 - (self.clock.time() - data.get('last_request_at', 0))
        if wait > 0:
            self.clock.sleep(wait)
        data[month] = data.get(month, 0) + 1
        data['last_request_at'] = self.clock.time()
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        self.usage_path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def get(self, endpoint, params):
        query = {k: v for k, v in params.items() if v not in (None, '')}
        url = f'{BASE}/{endpoint}?{urllib.parse.urlencode(query)}'
        self._spend()
        request = urllib.request.Request(url, headers={'X-RapidAPI-Key': self.key, 'X-RapidAPI-Host': HOST})
        try:
            with self.opener(request, timeout=60) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            # The message never contains the key: it is sent as a header, not in the URL.
            body = exc.read().decode('utf-8', errors='replace')[:300]
            raise RuntimeError(f'Techmap {endpoint} HTTP {exc.code}: {body}') from None


def save(kind, params, payload):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = OUT / 'raw' / f'{stamp}_{kind}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'collected_at': stamp, 'endpoint': kind, 'params': params,
                                'response': payload}, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description='Techmap 수집 (월 요청 상한 적용)')
    parser.add_argument('endpoint', choices=['count', 'search'])
    parser.add_argument('--pages', type=int, default=1)
    parser.add_argument('--start-page', type=int, default=1, help='이미 받은 페이지를 다시 요청하지 않도록 시작 페이지 지정')
    for name in FILTERS:
        parser.add_argument(f'--{name}')
    args = parser.parse_args(argv)
    load_env()
    client = TechmapClient(os.getenv('TECHMAP_RAPIDAPI_KEY', ''), int(os.getenv('TECHMAP_MONTHLY_REQUEST_CAP', '80')))
    params = {name: getattr(args, name) for name in FILTERS}
    pages = range(args.start_page, args.start_page + args.pages) if args.endpoint == 'search' else [None]
    for page in pages:
        payload = client.get(args.endpoint, {**params, 'page': page})
        path = save(args.endpoint if page is None else f'search_p{page}', params, payload)
        print(f"{args.endpoint}{'' if page is None else f' p{page}'}: totalCount={payload.get('totalCount')} "
              f"결과 {len(payload.get('result') or [])}건 → {path.relative_to(ROOT)}")
    print(f'이번 달 사용 {client.used()}/{client.cap}회 (무료 100회, 초과 1회당 $0.06)')


if __name__ == '__main__':
    main()
