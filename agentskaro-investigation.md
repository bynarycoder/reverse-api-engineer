# AgentsKaro investigation

Reviewed the public landing page and the public [Agentskaro repository](https://github.com/yubisaki-yat/Agentskaro) on 2026-11-17. Source findings below refer to repository commit `1019f2220041577e1ca25fbdc9e0cb4e1a6be64b`. The deployed site may use a different revision or configuration; no live API behavior was tested.

## Website and architecture

The repository contains a Next.js App Router website, its React components, and server route handlers. `package.json` specifies Next.js 16.3.3, React 19, Tailwind CSS, Framer Motion, Lucide and Nodemailer. The README describes Next.js 15 and an Electron desktop client, but the repository tree reviewed does not include desktop application source. The page includes a desktop simulator and a WhatsApp interface; `WhatsAppFeature.tsx` explicitly implements the latter as a local-state mockup, not a WhatsApp integration.

Sources: [package.json](https://github.com/yubisaki-yat/Agentskaro/blob/1019f2220041577e1ca25fbdc9e0cb4e1a6be64b/package.json), [page](https://github.com/yubisaki-yat/Agentskaro/blob/1019f2220041577e1ca25fbdc9e0cb4e1a6be64b/src/app/page.tsx), [WhatsApp mockup](https://github.com/yubisaki-yat/Agentskaro/blob/1019f2220041577e1ca25fbdc9e0cb4e1a6be64b/src/components/WhatsAppFeature.tsx).

## Source-derived API inventory

These are route implementations, not verified live API contracts. All paths are relative to the deployed site's origin.

| Method and path | Inputs and behavior in source |
| --- | --- |
| `POST /api/subscribe` | JSON `email`, optional `source`; validates email, saves subscriber and attempts a welcome email. Returns success, email status and subscriber metadata. |
| `POST /api/create-order` | JSON `planId`; creates a Razorpay order for monthly, yearly or lifetime plans; unknown plans fall back to yearly. Returns order ID, amount, currency, plan name and key ID. |
| `POST /api/verify-payment` | JSON Razorpay order ID, payment ID and signature, plus plan and user details; verifies HMAC, attempts to look up payment details, generates a license and attempts email delivery. |
| `GET /api/check-license` | Accepts `email` or `key`; the implementation actually looks up by email only, with an optional Razorpay fallback. Returns license information if found. |
| `POST /api/razorpay-webhook` | Requires a Razorpay signature header and configured webhook secret. Verifies HMAC; recognized events are logged, with fulfillment left as a comment. |
| `POST /api/broadcast` | Takes announcement fields and an admin secret, then emails active subscribers. Do not invoke without authorization. |

Source: [API routes](https://github.com/yubisaki-yat/Agentskaro/tree/1019f2220041577e1ca25fbdc9e0cb4e1a6be64b/src/app/api).

## Static review notes

- The license checker returns a license key when supplied an email whose record is found, without an apparent user authentication check. It accepts a `key` parameter but does not use it to find or verify a license.
- Payment verification checks the Razorpay signature, but derives license plan and expiry from request-supplied fields instead of establishing them from trusted order data. Payment lookup failures do not stop license creation. This merits owner review; exploitability and deployment configuration have not been tested.
- Broadcast authentication has a hard-coded fallback secret when the environment variable is absent. The owner should configure a strong secret and remove the fallback; no broadcast request was sent.
- License records are written to a local JSON file, with persistence errors caught and logged. That may not be durable or consistent in multi-instance/serverless deployments.
- These are source-level observations, not proof that the public deployment is vulnerable or configured the same way.

## Desktop release

The repository's [release](https://github.com/yubisaki-yat/Agentskaro/releases/tag/v3.1.0) is titled “AgentsKaro Desktop Setup v3.5.0” despite the `v3.1.0` tag. Its asset is `AgentsKaro.Setup.3.5.0.exe` (351,302,704 bytes). The website's download modal points to this latest release asset. It has not been downloaded, executed, or inspected; marketing claims about job automation, encryption, AI and WhatsApp are unverified.

## Next steps and constraints

- Use the website source to map UI flows and build a client against observed behavior; a sanitized HAR can establish what the live deployment actually does. Avoid real purchases, emails or job submissions during testing unless explicitly intended.
- Analyze the installer in an isolated Windows VM with snapshots, ideally with permission and a sample account. Static package inspection can precede execution. Do not upload credentials, cookies or payment details.
- The README states “All rights reserved.” Do not assume the repository grants permission to redistribute its source, branding or assets. An independent implementation can use the observed behavior without copying protected material, subject to applicable rights.

## Additional checkout and release observations

The pricing component loads Razorpay Checkout, creates an order, then posts the checkout response and selected plan to the verification route. It also constructs a fallback license/download display in the browser before backend verification finishes. The fallback download URL names `AgentsKaro.Setup.3.1.0.exe`, whereas the observed release asset is named `AgentsKaro.Setup.3.5.0.exe`; the environment can override the URL. See [Pricing.tsx](https://github.com/yubisaki-yat/Agentskaro/blob/1019f2220041577e1ca25fbdc9e0cb4e1a6be64b/src/components/Pricing.tsx) and [DownloadModal.tsx](https://github.com/yubisaki-yat/Agentskaro/blob/1019f2220041577e1ca25fbdc9e0cb4e1a6be64b/src/components/DownloadModal.tsx).

GitHub reports the release asset SHA-256 as `c6fceec012a213dfdc62589287f68e130921f8180b4644d332f8b7d09552c054`; this is GitHub metadata, not a locally verified hash. Download was attempted but GitHub redirected it to a release-assets host unavailable from this workspace, so static or dynamic installer inspection remains blocked. Supply the installer as an attachment to enable static analysis. Dynamic Windows behavior would still require a suitable isolated Windows environment and authorized test accounts.

A source-derived Python client and offline mock-server tests are available in [`examples/agentskaro`](examples/agentskaro/README.md). Tests establish client request formatting, not production compatibility.

## Local source validation (2026-11-17)

Ran the repository's Next.js application locally, without Razorpay or SMTP credentials, and exercised the source-derived Python client against it. No production service, real payment, welcome email, broadcast, or job application was invoked. Results:

| Request | Observed local result |
| --- | --- |
| `GET /api/check-license` with neither parameter | 400, missing email or key |
| `GET /api/check-license` with an unknown test email | 200, `active: false` |
| `GET /api/check-license` with only a test key | 200, `active: false`; consistent with missing key lookup in source |
| `POST /api/subscribe` with an invalid email | 400, invalid email format |
| `POST /api/create-order` with monthly plan | 500, Razorpay credentials not configured |
| `POST /api/verify-payment` | 500, server secret missing |
| `POST /api/razorpay-webhook` without a signature | 400, missing signature or secret |
| `POST /api/broadcast` with an incorrect secret | 401, unauthorized |

These checks verify limited negative paths on the local source checkout only. They do not verify successful payment, email, license issuance, real credentials, or the deployed site. Reverse API Engineer was installed and its preflight run, but it did not generate this client: its capture-and-generation workflow requires network traffic and configured model access, neither of which was established for the live site here.
