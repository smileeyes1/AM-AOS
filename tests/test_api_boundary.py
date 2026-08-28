import json
import os
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen

from am_aos.api import APIStore, Handler, ThreadingHTTPServer


class TestAPIBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        Handler.store = APIStore(self.tmp.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        os.unlink(self.tmp.name)

    def post(self, payload, key):
        req = Request(
            self.base + "/v1/authorize",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Idempotency-Key": key},
            method="POST",
        )
        with urlopen(req) as r:
            return r.status, json.loads(r.read())

    def test_rbac_denies_execute_for_viewer(self):
        code, body = self.post({"actor":"a","role":"viewer","action":"execute","request_id":"1"}, "k1")
        self.assertEqual(code, 200)
        self.assertFalse(body["allowed"])

    def test_operator_can_execute(self):
        code, body = self.post({"actor":"a","role":"operator","action":"execute","request_id":"2"}, "k2")
        self.assertEqual(code, 200)
        self.assertTrue(body["allowed"])

    def test_idempotent_replay(self):
        payload = {"actor":"a","role":"operator","action":"execute","request_id":"3"}
        _, first = self.post(payload, "k3")
        _, second = self.post(payload, "k3")
        self.assertFalse(first.get("replayed", False))
        self.assertTrue(second["replayed"])

    def test_idempotency_key_cannot_change_request(self):
        self.post({"actor":"a","role":"operator","action":"execute","request_id":"4"}, "k4")
        with self.assertRaises(Exception):
            self.post({"actor":"a","role":"admin","action":"admin","request_id":"4"}, "k4")

    def test_missing_idempotency_is_rejected(self):
        req = Request(
            self.base + "/v1/authorize",
            data=json.dumps({"actor":"a","role":"operator","action":"execute"}).encode(),
            headers={"Content-Type":"application/json"},
            method="POST",
        )
        try:
            urlopen(req)
            self.fail("expected HTTP 400")
        except Exception as exc:
            self.assertIn("400", str(exc))

    def test_health_endpoint(self):
        with urlopen(self.base + "/health") as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(json.loads(r.read())["status"], "ok")


if __name__ == "__main__":
    unittest.main()
