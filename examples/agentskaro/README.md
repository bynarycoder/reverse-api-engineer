# AgentsKaro website API client

A small standard-library Python client based on a **static review** of the public [website source](https://github.com/yubisaki-yat/Agentskaro/tree/1019f2220041577e1ca25fbdc9e0cb4e1a6be64b/src/app/api). It has not been verified against the live deployment, which may differ. It does not implement the desktop job bot or WhatsApp integration. See [the investigation](../../agentskaro-investigation.md) for limitations and security observations.

```python
from api_client import AgentsKaroClient, APIError

# Prefer your own locally hosted instance for testing.
client = AgentsKaroClient(base_url="http://127.0.0.1:3000")
try:
    result = client.check_license(email="you@example.com")
    print(result)
except APIError as exc:
    print(exc.status, exc.response)
```

Methods reflect the route names: `subscribe`, `create_order`, `verify_payment`, `check_license`, `broadcast` and `razorpay_webhook`. Many have real side effects, including creating payment orders or sending email. Only use accounts and infrastructure you are authorized to access. Never supply secrets in source code, logs or shared captures. The server accepts a license `key` query parameter but its code does not actually look up a license by key. The client rejects invalid plan IDs instead of silently defaulting to yearly as the server does.

Run the offline tests from the repository root:

```sh
python -m unittest discover -s examples/agentskaro -p 'test_*.py'
```
