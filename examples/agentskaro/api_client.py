"""Source-derived AgentsKaro website API client; live deployment not verified."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class APIError(Exception):
    def __init__(self, status: int, response: Any):
        self.status = status
        self.response = response
        super().__init__(f"AgentsKaro API returned HTTP {status}: {response}")


class AgentsKaroClient:
    def __init__(self, base_url: str = "https://agentskaro.co.in", timeout: float = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None,
                 headers: dict[str, str] | None = None, raw: bytes | None = None) -> dict[str, Any]:
        request_headers = {"Accept": "application/json", **(headers or {})}
        data = raw
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=data, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except HTTPError as exc:
            body = exc.read()
            try:
                result = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                result = body.decode("utf-8", errors="replace")
            raise APIError(exc.code, result) from exc
        except URLError as exc:
            raise ConnectionError(f"AgentsKaro request failed: {exc.reason}") from exc
        result = json.loads(body)
        if not isinstance(result, dict):
            raise ValueError("Expected an API JSON object")
        return result

    def subscribe(self, email: str, source: str = "download_modal") -> dict[str, Any]:
        """Save an email and attempt to send a welcome message (side effect)."""
        return self._request("POST", "/api/subscribe", {"email": email, "source": source})

    def create_order(self, plan_id: str) -> dict[str, Any]:
        """Create a real Razorpay order; does not complete payment."""
        if plan_id not in {"monthly", "yearly", "lifetime"}:
            raise ValueError("plan_id must be monthly, yearly, or lifetime")
        return self._request("POST", "/api/create-order", {"planId": plan_id})

    def verify_payment(self, order_id: str, payment_id: str, signature: str,
                       plan_id: str, plan_name: str, user_email: str = "") -> dict[str, Any]:
        """Verify an actual checkout and potentially issue a license and send email."""
        return self._request("POST", "/api/verify-payment", {
            "razorpay_order_id": order_id, "razorpay_payment_id": payment_id,
            "razorpay_signature": signature, "planId": plan_id,
            "planName": plan_name, "userEmail": user_email,
        })

    def check_license(self, *, email: str | None = None, key: str | None = None) -> dict[str, Any]:
        """Look up a license; source accepts key but does not implement lookup by key."""
        if not email and not key:
            raise ValueError("email or key is required")
        params = {k: v for k, v in (("email", email), ("key", key)) if v is not None}
        return self._request("GET", "/api/check-license?" + urlencode(params))

    def broadcast(self, *, secret_key: str, subject: str, message: str,
                  headline: str = "", cta_text: str = "", cta_url: str = "") -> dict[str, Any]:
        """Send email to active subscribers; use only on a server you administer."""
        return self._request("POST", "/api/broadcast", {
            "secretKey": secret_key, "subject": subject, "message": message,
            "headline": headline, "ctaText": cta_text, "ctaUrl": cta_url,
        })

    def razorpay_webhook(self, raw_body: bytes, signature: str) -> dict[str, Any]:
        """Send an already signed webhook body without changing its bytes."""
        return self._request("POST", "/api/razorpay-webhook", raw=raw_body,
                             headers={"Content-Type": "application/json",
                                      "X-Razorpay-Signature": signature})
