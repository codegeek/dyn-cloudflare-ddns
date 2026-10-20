import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
from cloudflare import Cloudflare


spec = importlib.util.spec_from_file_location(
    "updater", Path(__file__).resolve().parents[1] / "dyn-cloudflare-ddns" / "__main__.py"
)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

ZONE_ID = "a" * 32
RECORD_ID = "b" * 32


def record(content="192.0.2.1", type="A"):
    return {
        "id": RECORD_ID, "name": "example.com", "type": type,
        "content": content, "proxied": True, "ttl": 300,
        "comment": "keep me", "tags": ["owner:ddns"],
    }


class CloudflareTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"CF_API_TOKEN": "test-token"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.requests = []

    def run_update(self, records, *, ip="192.0.2.2", rtype="A", zones=None,
                   status=200, paginated=False):
        def handle(request):
            self.requests.append(request)
            if request.url.path.endswith("/zones"):
                result = [{"id": ZONE_ID, "name": "example.com"}] if zones is None else zones
            elif request.method == "GET":
                if status != 200:
                    return httpx.Response(status, json={
                        "success": False, "errors": [{"code": 10000, "message": "Denied"}],
                    })
                self.assertEqual(request.url.params["name.exact"], "example.com")
                self.assertEqual(request.url.params["type"], rtype)
                result = records if int(request.url.params.get("page", "1")) == 1 else []
                if paginated:
                    page = int(request.url.params.get("page", "1"))
                    return httpx.Response(200, json={
                        "success": True, "errors": [], "messages": [],
                        "result": records[page - 1:page],
                        "result_info": {"page": page, "per_page": 1,
                                        "total_pages": len(records), "total_count": len(records)},
                    })
            else:
                result = record(ip, rtype)
            return httpx.Response(200, json={
                "success": True, "errors": [], "messages": [], "result": result,
            })

        client = Cloudflare(api_token="test-token", max_retries=0,
                            http_client=httpx.Client(transport=httpx.MockTransport(handle)))
        with patch.object(updater, "Cloudflare", return_value=client):
            updater.updateCloudflare(ip, rtype, "example.com")
        self.assertTrue(client.is_closed())

    def writes(self):
        return [r for r in self.requests if r.method != "GET"]

    def test_unchanged_address_does_not_write(self):
        self.run_update([record()], ip="192.0.2.1")
        self.assertEqual(self.writes(), [])

    def test_update_preserves_required_fields_and_omits_metadata(self):
        self.run_update([record()])
        writes = self.writes()
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0].method, "PATCH")
        self.assertTrue(writes[0].url.path.endswith("/" + RECORD_ID))
        self.assertEqual(json.loads(writes[0].content), {
            "name": "example.com", "type": "A", "ttl": 300, "content": "192.0.2.2",
        })

    def test_missing_record_is_created(self):
        self.run_update([])
        writes = self.writes()
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0].method, "POST")
        self.assertEqual(json.loads(writes[0].content), {
            "name": "example.com", "type": "A", "ttl": 1, "content": "192.0.2.2",
        })

    def test_ipv6(self):
        self.run_update([record("2001:db8::1", "AAAA")], ip="2001:db8::2", rtype="AAAA")
        self.assertEqual(json.loads(self.writes()[0].content), {
            "name": "example.com", "type": "AAAA", "ttl": 300, "content": "2001:db8::2",
        })

    def test_records_on_later_pages_are_updated(self):
        self.run_update([record("192.0.2.2"), record()], paginated=True)
        self.assertEqual(len(self.writes()), 1)
        self.assertEqual(self.writes()[0].method, "PATCH")

    def test_missing_zone(self):
        with self.assertRaisesRegex(SystemExit, "Zone not found"):
            self.run_update([], zones=[])
        self.assertEqual(self.writes(), [])

    def test_api_error_keeps_original_message(self):
        with self.assertRaisesRegex(SystemExit, "Cloudflare API error.*Denied"):
            self.run_update([], status=403)
        self.assertEqual(self.writes(), [])

    def test_invalid_type_is_rejected_before_client_creation(self):
        with patch.object(updater, "Cloudflare") as client:
            with self.assertRaisesRegex(SystemExit, "DDNS_RTYPE"):
                updater.updateCloudflare("192.0.2.1", "TXT", "example.com")
            client.assert_not_called()

    def test_invalid_type_is_rejected_before_dns_resolution(self):
        with patch.dict(os.environ, {"CF_ZONE": "example.com", "DDNS_HOST": "ddns.example",
                                     "DDNS_RTYPE": "TXT"}, clear=True):
            with patch.object(updater, "setupLogging"), patch.object(
                updater, "getExternalIPFromDDNS"
            ) as resolve:
                with self.assertRaisesRegex(SystemExit, "DDNS_RTYPE"):
                    updater.main()
                resolve.assert_not_called()

    def test_credentials(self):
        cases = [
            ({"CF_API_TOKEN": "token"}, {"api_token": "token"}),
            ({"CLOUDFLARE_API_TOKEN": "token"}, {"api_token": "token"}),
            ({"CF_API_KEY": "legacy-token"}, {"api_token": "legacy-token"}),
            ({"CF_API_KEY": "key", "CF_API_EMAIL": "user@example.com"},
             {"api_key": "key", "api_email": "user@example.com"}),
            ({"CLOUDFLARE_API_KEY": "key", "CLOUDFLARE_EMAIL": "user@example.com"},
             {"api_key": "key", "api_email": "user@example.com"}),
            ({"CF_API_TOKEN": "token", "CF_API_KEY": "key", "CF_API_EMAIL": "email"},
             {"api_token": "token"}),
        ]
        for env, expected in cases:
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True):
                self.assertEqual(updater.cloudflare_credentials(), expected)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(SystemExit, "CF_API_TOKEN"):
                updater.cloudflare_credentials()


if __name__ == "__main__":
    unittest.main()
