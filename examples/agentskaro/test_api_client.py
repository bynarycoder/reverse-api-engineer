import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from api_client import APIError, AgentsKaroClient


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.reply()

    def do_POST(self):
        self.reply()

    def reply(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        status = 400 if self.path == "/error" else 200
        output = json.dumps({"method": self.command, "path": self.path,
                             "body": body.decode(),
                             "signature": self.headers.get("X-Razorpay-Signature")}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = AgentsKaroClient(f"http://127.0.0.1:{cls.server.server_port}")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_license_encodes_query(self):
        r = self.client.check_license(email="a+b@example.com")
        self.assertEqual(r["path"], "/api/check-license?email=a%2Bb%40example.com")
        self.assertEqual(r["method"], "GET")
        with self.assertRaises(ValueError):
            self.client.check_license()

    def test_order_and_subscribe(self):
        r = self.client.create_order("monthly")
        self.assertEqual(json.loads(r["body"]), {"planId": "monthly"})
        with self.assertRaises(ValueError):
            self.client.create_order("other")
        r = self.client.subscribe("a@example.com")
        self.assertEqual(json.loads(r["body"])["source"], "download_modal")

    def test_verification_and_broadcast(self):
        r = self.client.verify_payment("order", "payment", "signature", "yearly", "Yearly")
        self.assertEqual(json.loads(r["body"])["razorpay_order_id"], "order")
        r = self.client.broadcast(secret_key="test", subject="Subject", message="Message")
        self.assertEqual(json.loads(r["body"])["secretKey"], "test")

    def test_webhook_preserves_body(self):
        raw = b'{ "event": "test" }'
        r = self.client.razorpay_webhook(raw, "signed")
        self.assertEqual(r["body"].encode(), raw)
        self.assertEqual(r["signature"], "signed")

    def test_http_error(self):
        with self.assertRaises(APIError) as caught:
            self.client._request("GET", "/error")
        self.assertEqual(caught.exception.status, 400)
        self.assertEqual(caught.exception.response["path"], "/error")


if __name__ == "__main__":
    unittest.main()
