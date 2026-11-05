import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from skillpath.sources.techmap import CapReached, TechmapClient


class FakeClock:
    def __init__(self):
        self.now, self.slept = 1000.0, []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(round(seconds, 2))
        self.now += seconds


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TechmapClientTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.sent = []

    def client(self, cap=2, fail=False, clock=None):
        def opener(request, timeout):
            self.sent.append(request)
            if fail:
                raise urllib.error.HTTPError(request.full_url, 500, 'err', {}, io.BytesIO(b'{"message":"boom"}'))
            return FakeResponse(json.dumps({'totalCount': '7'}).encode())
        return TechmapClient('secret-key', cap, self.tmp / 'usage.json', opener=opener, clock=clock or FakeClock())

    def test_cap_blocks_before_sending(self):
        client = self.client(cap=2)
        client.get('count', {'countryCode': 'kr'})
        client.get('count', {'countryCode': 'kr'})
        with self.assertRaises(CapReached):
            client.get('count', {'countryCode': 'kr'})
        self.assertEqual((len(self.sent), client.used()), (2, 2))

    def test_failed_request_still_counts_and_hides_key(self):
        client = self.client(fail=True)
        with self.assertRaises(RuntimeError) as caught:
            client.get('search', {'countryCode': 'kr'})
        self.assertEqual(client.used(), 1)
        self.assertNotIn('secret-key', str(caught.exception))
        self.assertNotIn('secret-key', self.sent[0].full_url)

    def test_requests_are_spaced_one_per_second_and_empty_filters_dropped(self):
        client = self.client(cap=5)
        client.get('count', {'countryCode': 'kr', 'title': None})
        client.get('count', {'countryCode': 'kr'})
        self.assertEqual(client.clock.slept, [1.1])
        self.assertNotIn('title', self.sent[0].full_url)

    def test_spacing_holds_across_separate_runs(self):
        clock = FakeClock()
        self.client(cap=5, clock=clock).get('count', {'countryCode': 'kr'})
        clock.now += 0.3
        # A new process reads the persisted last request time from the usage file.
        self.client(cap=5, clock=clock).get('count', {'countryCode': 'kr'})
        self.assertEqual(clock.slept, [0.8])


if __name__ == '__main__':
    unittest.main()
