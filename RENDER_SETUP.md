# Render + MongoDB Atlas + Namecheap

This project is packaged for **one Render Docker web service**. React's compiled files and all `/api` routes are served by the same process. The database is MongoDB Atlas, not a Render Postgres database.

## 1. Create the MongoDB Atlas database

1. Create an Atlas project and cluster at https://www.mongodb.com/cloud/atlas.
2. Under **Database Access**, create a database user with read/write access to the application's database. Use a strong, unique password.
3. Under **Network Access**, allow the outbound IP ranges shown for your Render service. Avoid allowing every IP permanently. If you use a temporary open rule while setting up, restrict it afterward.
4. Choose **Connect → Drivers → Python**, and copy the `mongodb+srv://...` URI. Replace placeholders with your database username and URL-encoded password. Keep TLS enabled.
5. You will put this URI in `MONGO_URL` in Render. Do not commit it to the repository. `DB_NAME` is a separate variable, set to `desmos_testing` in the Blueprint; the existing preview value is not changed.

## 2. Create the Render service

1. Save the project to your GitHub repository using **Save to Github**.
2. In https://dashboard.render.com choose **New → Blueprint** and select that repository.
3. Render reads the root `render.yaml`. Keep the build context at the repository root.
4. Enter the two requested secrets:
   - `MONGO_URL`: your Atlas connection URI.
   - `OPENROUTER_API_KEY`: your server-side OpenRouter key. Use a newly rotated key if one was shared in a message.
5. Apply the Blueprint. Wait for the build and `/api/health` check to succeed.
6. Visit the service's `https://<assigned-name>.onrender.com` address. Confirm `/api/health` returns `{"status":"ok","database":"connected"}`.

`PORT` is provided by Render. Do not replace it with the preview's port. `APP_ORIGIN` and `CORS_ORIGINS` are populated from the service's own `RENDER_EXTERNAL_URL`. If self-references are not populated in your account, set both manually to that HTTPS origin. Do not use the old preview URL.

The Docker build sets **only the public frontend setting** `REACT_APP_BACKEND_URL=/`. Requests stay on the current hostname, including wildcard domains. Keys and the Atlas URI are never included in the frontend build. Regular development still uses the existing frontend `.env` URL.

## 3. Add desmos.lol and wildcard hostnames

**Render supports wildcard custom domains.** The earlier limitation described for the preview host does not apply to Render. Official instructions: https://render.com/docs/custom-domains#wildcard-domains.

1. In your Render service, open **Settings → Custom Domains**.
2. Add `desmos.lol` and `*.desmos.lol` to this same service. Render also adds the corresponding `www` redirect for the apex.
3. Keep the domain-verification screen open. Copy its exact service-specific DNS targets.
4. In Namecheap, open **Domain List → Manage → Advanced DNS**. These instructions assume Namecheap BasicDNS manages your DNS; if custom nameservers are configured, make the changes with that DNS provider instead.
5. Remove only conflicting parking/redirect/A/AAAA/CNAME records for the hosts you are replacing. Keep mail records and unrelated records intact. Do not use a URL Redirect for the apex.
6. Add the records below. Use the values shown by Render, not example values copied from another service:

| Type | Host | Value |
| --- | --- | --- |
| ALIAS Record | `@` | Your service's `<assigned-name>.onrender.com` |
| CNAME Record | `www` | Your service's `<assigned-name>.onrender.com` |
| CNAME Record | `*` | Your service's `<assigned-name>.onrender.com` |
| CNAME Record | `_acme-challenge` | Exact `…verify.renderdns.com` target shown by Render |
| CNAME Record | `_cf-custom-hostname` | Exact `…hostname.renderdns.com` target shown by Render |

Use Automatic TTL. Namecheap expects the **Host** portion only, not the full domain repeated. If your Namecheap DNS mode does not offer ALIAS, use the apex **A record value currently displayed by Render** instead. Official Namecheap guide: https://render.com/docs/configure-namecheap-dns.

**The apex must also point to Render for its wildcard configuration to work.** The two verification CNAME records are required for wildcard certificate issuance/renewal and ownership validation. Leave them in place. If you have CAA records, allow `letsencrypt.org` and `pki.goog` for both `issue` and `issuewild`, as documented by Render.

7. Save the records, allow time for propagation, then click **Verify** in Render for both domains. Wait until HTTPS certificates are issued.
8. Open `https://desmos.lol`, `https://wwd.desmos.lol`, and `https://123.desmos.lol`. They should all show the same application.
9. Set `APP_ORIGIN=https://desmos.lol` for the provider's referring-site metadata. You may set `CORS_ORIGINS` to your exact apex and Render origins separated by commas. Wildcard frontend calls are same-origin and do not need permissive cross-origin access.

This is **wildcard DNS routing**, not a new service or DNS record created for every name. Valid one-label hostnames (letters, digits, and internal hyphens) share the app. Existing explicit DNS records override the wildcard. A certificate for `*.desmos.lol` does not cover `a.b.desmos.lol`. Browser history/favorites/conversation lists are separate for each hostname.

## 4. Operational checks

### Enable interactive websites and origin-dependent 3D titles

Reserve `content.desmos.lol` as an isolated content origin, served by the **same Render service** through the wildcard domain you configured above. Then set `CONTENT_ORIGIN=https://content.desmos.lol` in Render and restart the service. Do not open the calculator or Notes on this reserved hostname. It must not equal the main app hostname. Do not set cookies for the entire `.desmos.lol` domain.

The embedded workspace and library can then use real-origin storage and service workers without granting third-party content access to the calculator's private browser storage. Until this hostname is configured and has valid HTTPS, the Web page uses a real Wisp-backed **script-free reader**, not a full interactive browser. It does not pretend a successful socket means the destination page loaded. Some 3D titles also need this isolation to load textures or save data.

Internal navigation no longer shows any leave confirmation. Only the browser-controlled warning remains when closing, reloading, or leaving the site (subject to the browser's interaction rules). This does not prevent network filtering.

- **Health check fails:** verify Atlas URI/password encoding, Atlas outbound IP allowlist, and `DB_NAME`. No MongoDB server runs inside the app container.
- **Notes returns insufficient credits:** add provider balance or change `OPENROUTER_MODEL` to a model available to your account. Free endpoints can be rate-limited. The configured economical primary is `google/gemini-2.5-flash-lite`, with `openai/gpt-4o-mini` fallback.
- **External browsing fails:** both configured endpoints are external dependencies. No DNS setup can guarantee arbitrary destination compatibility. Sandboxing restricts websites that require origin-bound browser APIs.
- **Library loads slowly:** HTML is fetched on first use. Downloads stream to disk, and the disposable `/tmp/library-cache` is capped at500MB using `GAME_CACHE_MAX_BYTES`; older entries are refetched when needed. No persistent disk is needed for conversations; they live in Atlas.
- **Wrong/missing asset after refresh:** the production server serves actual static files, and SPA paths fall back to `index.html`; unknown API/static-file paths return404, not HTML.
- **Rotate or change a key:** change the Render environment variable only. Never put it in Git, frontend settings, or DNS.

## Current verification boundary

Code, frontend build, backend integration, and configuration can be checked in this workspace. Actual Render provisioning, Atlas network access, Namecheap ownership, wildcard DNS, and TLS issuance must be completed in your accounts. This guide does not claim those account-level actions have already happened.