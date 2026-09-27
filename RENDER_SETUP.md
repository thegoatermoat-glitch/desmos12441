# Render setup — no database cluster required

The app now uses **browser-only conversation history**. You do not need MongoDB Atlas, a database cluster, or a database subscription. Conversations live in IndexedDB on each device/browser/hostname. The backend forwards requests without retaining conversation messages.

## 1. Save and configure the service

1. Use **Save to Github** to save the latest project.
2. In Render, open your existing Docker web service or create a Web Service from that repository.
3. Runtime: **Docker**; Root Directory: **blank**; Dockerfile: `./Dockerfile`; Docker Build Context: `.`.
4. Leave Build Command and Start/Docker Command **blank**. Health Check Path: `/api/health`.
5. Alternatively, New → Blueprint uses the root `render.yaml` and requests only your OpenRouter key. No database is created or requested.

## 2. Environment variables

For a manually configured service, add the following. Replace the key and public service URL; do not leave those placeholders as literal values.

```env
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
OPENROUTER_MODEL=cognitivecomputations/dolphin-mistral-24b-venice-edition
OPENROUTER_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_REQUEST_BUDGET_USD=0.01
OPENROUTER_MAX_OUTPUT_TOKENS=1024
APP_ORIGIN=https://YOUR-SERVICE.onrender.com
CORS_ORIGINS=https://YOUR-SERVICE.onrender.com
HOST=0.0.0.0
CONTENT_ORIGIN=https://content.desmos.lol
BROWSER_SHORTCUTS=[{"id":"tiktok","name":"TikTok","url":"https://www.tiktok.com/"},{"id":"youtube","name":"YouTube","url":"https://www.youtube.com/"}]
SERVE_FRONTEND=true
FRONTEND_BUILD_DIR=/app/frontend/build
WISP_ENDPOINTS=wss://wisp-proxy.emergent.host/api/wisp,wss://wisp-proxy.emergent.host/api/wisp2
GAME_RAW_BASE=https://raw.githubusercontent.com/CoolDude2349/Offline-HTML-Games-Pack/master/offline/
GAME_SOURCE_URL=https://github.com/CoolDude2349/Offline-HTML-Games-Pack/tree/master/offline
GAME_CACHE_DIR=/tmp/library-cache
GAME_MAX_BYTES=100000000
GAME_CACHE_MAX_BYTES=500000000
```

- `MONGO_URL` and `DB_NAME` are **not required**. Existing values can remain; they are used only if you explicitly import earlier server-stored conversations.
- `OPENROUTER_FALLBACK_MODEL` is no longer used. The latest mode tries free models first, then **one cheapest eligible paid attempt**, selected using current pricing.
- Existing services must add `OPENROUTER_REQUEST_BUDGET_USD` and `OPENROUTER_MAX_OUTPUT_TOKENS` before deploying this version. The budget is an application **estimate threshold**, not a provider-enforced billing cap. Set it to `0` to prohibit paid attempts. Keep an OpenRouter key-level spending limit for actual account protection.
- `CONTENT_ORIGIN` now uses the user's confirmed HTTPS hostname, `https://content.desmos.lol`, enabling full-page Web browsing. For another domain, configure its own separate HTTPS content origin; if it is not ready, leave the value empty for script-free reader mode only.
- Existing manually configured Render services must set **both** `CONTENT_ORIGIN` and `BROWSER_SHORTCUTS` from the block above. Updating repository code does not automatically update dashboard environment values. The Blueprint contains both settings for new/synced services.
- Render supplies `PORT`. The Dockerfile sets the frontend's public `REACT_APP_BACKEND_URL=/`; do not override either with a preview value.
- Keep the OpenRouter key private. Rotate any key previously shared in a message. Never put it in Git, frontend code, or DNS.

## 3. Deploy and check

Save the settings, then **Manual Deploy → Deploy latest commit**. Open:

```text
https://YOUR-SERVICE.onrender.com/api/health
```

Expected response:

```json
{"status":"ok","storage":"browser","database_required":false}
```

The health check no longer contacts MongoDB. An unavailable database cannot make this app's normal startup or health check fail.

## 4. Unmoderated-provider selection, cheapest paid fallback, and privacy

**Current policy is stricter than an unmoderated provider flag:** only exact IDs in `backend/model_allowlist.json`, backed by a publisher's explicit “uncensored” or “unrestricted” description, can appear or be attempted. Their live canonical slug and publisher artifact must match the audited identity. The additional `top_provider.is_moderated === false` and all pricing/capability guards still apply. An OpenRouter description or model-family name alone is not accepted as publisher proof.

As verified2026-09-27, the only qualifying live model is **`cognitivecomputations/dolphin-mistral-24b-venice-edition`** (Dolphin Mistral24B Venice Edition / Venice:Uncensored). Its [publisher card](https://huggingface.co/dphn/Dolphin-Mistral-24B-Venice-Edition) states the goal of creating “the most uncensored version of Mistral24B”. This is currently a **paid** listing: $0.20/M input and $0.90/M output at verification time. There is **no verified free listing currently available**, and no `:free` alias is invented. Prices and availability are rechecked live.

Ordinary models, even those with an unmoderated provider, are excluded from both primary requests and fallback. If the audited model disappears, identity metadata changes, or its response reports an unknown model, requests fail clearly rather than switching to an ordinary model. Audited publisher source links are visible in Notes. New exact model IDs require explicit review and deployment; the allowlist is not expanded by keyword matching.

Moderated, unknown and malformed flags, dynamic OpenRouter routers, unknown/negative prices, request fees, separately priced reasoning, write surcharges and tier-price overrides are excluded. **Publisher descriptions are not guarantees of unrestricted answers or every actual provider's behavior.** Model/provider policies still apply; no permissive publisher demo prompt was added.

Free-first/cheapest-paid policy is retained **within the audited set only**. The picker selects a verified free model if one becomes available after audit; otherwise it clearly shows Paidonly before sending. Each request refreshes the catalogue and allows at most one lowest-estimated-cost paid attempt. With only one current paid entry, this means one attempt and no alternative fallback. The general max-five policy remains for a future audited multi-model set; it never authorizes ordinary models. A stale OPENROUTER_MODEL preference cannot override the allowlist.

Default limits: **$0.01 estimated request threshold**, **1024 output tokens**,55 seconds overall and12 seconds per attempt. Estimate uses UTF-8 bytes with margin/message framing, not characters÷4. Only models fitting the context and estimated budget are attempted. Paid provider input/output caps use USD per million tokens, with request fee capped at0, provider fallback disabled, and cheaper-provider routing. Reasoning is disabled when supported; no tools/search/plugins/media are requested.

**Estimates are not guaranteed charges:** OpenRouter does not provide a documented total-dollar cap per chat call. Timeouts, malformed/empty replies and failed requests may still incur charges, so this mode never sends a second paid attempt. Provider-reported `usage.cost` is labeled as reported cost; missing usage is labeled unavailable, with estimate shown separately. Keep the server key's real spending limit low: this application is public and has no account login.

Explicit free-tier-only quotas can advance to the authorized paid fallback. Authentication failures, exhausted-credit/key-limit402, policy403, and general account-wide quotas stop retries. Provider Retry-After is respected; insufficient time can mean fewer attempts. Full history and the same session ID are sent to each attempt. Fallback cannot guarantee an answer or remove a model's own rules.

Messages are sent to OpenRouter/the selected provider for a response, but this application's server does not save them. Browser history is not synced across devices or subdomains. Export notes before clearing site data, changing browsers, or moving to another hostname. Deleting a local conversation does not delete any copy retained by a third-party provider under its own policy.

Older server conversations are not deleted automatically. If the browser still has their old IDs, an **Import earlier notes** control attempts a read-only import using the original database, if it is still configured. This optional recovery is never part of startup, health, or new conversations. You do not need to create or retain a cluster for new usage.

## 5. Optional Namecheap domain and wildcard setup

1. In Render → Settings → Custom Domains, add `desmos.lol` and `*.desmos.lol` to this same service.
2. In Namecheap → Domain List → Manage → Advanced DNS (or your actual DNS provider if using other nameservers), add:

| Type | Host | Value |
| --- | --- | --- |
| ALIAS | `@` | Your assigned `<service>.onrender.com` hostname |
| CNAME | `www` | The same Render hostname |
| CNAME | `*` | The same Render hostname |
| CNAME | `_acme-challenge` | Exact certificate-validation target supplied by Render |
| CNAME | `_cf-custom-hostname` | Exact ownership-validation target supplied by Render |

Use Automatic TTL. DNS values have no `https://` or path. If ALIAS is unavailable, use the apex **A record IP address** shown by Render instead; never put a hostname into an A record. Remove only conflicting records and keep mail/unrelated records. Verify both hostnames in Render and wait for HTTPS certificates. Official wildcard instructions: https://render.com/docs/custom-domains#wildcard-domains.

3. After HTTPS works, set:

```env
APP_ORIGIN=https://desmos.lol
CORS_ORIGINS=https://desmos.lol,https://YOUR-SERVICE.onrender.com
CONTENT_ORIGIN=https://content.desmos.lol
```

4. Save/restart and test `desmos.lol`, `123.desmos.lol`, and `wwd.desmos.lol`. They share the same app, not separate service instances. Each hostname still has separate browser history. A one-level wildcard does not cover `a.b.desmos.lol`.

Reserve `content.desmos.lol` for embedded third-party content, not the main Notes/calculator. Before the isolated hostname is configured, Web uses script-free reader mode. Some interactive/Unity titles need the isolated origin; individual third-party assets or runtimes can still have compatibility issues. No network-filter or universal site-access guarantee is made.

### Web browsing and close-tab warning

- After saving the environment settings and deploying the latest code, `/api/config` must show the nonempty content origin and TikTok/YouTube shortcuts. Web should show **Full-page browsing**, not **Reader view**.
- Full pages use the existing Scramjet/Wisp browser on the separate content origin; no plain third-party iframe is used. Sites can still block proxies, require sign-in, or limit embedded features. Video playback is not guaranteed. **Open in new tab** opens the entered public URL directly when in-page browsing is restricted.
- Deploy the latest frontend assets to the same service that serves `content.desmos.lol` so the shell and service worker are updated together. HTTPS alone does not enable interactive mode while `CONTENT_ORIGIN` remains blank.
- The native close/reload warning is installed on the app shell. Test after clicking or typing inside the page, then close/reload the tab. The browser controls the wording and can suppress the warning before user interaction, in restricted embedded previews, or on mobile. Internal calculator/Library/Web/Notes navigation does not display a leave modal.
- Web tabs and bookmarks are stored in this browser's localStorage under `calculator-web-workspace-v1`. Tabs keep separate address/history and stay mounted when switching. After reopening Web, saved addresses/history are restored, but only the active tab loads until others are selected. Closing the last tab creates a new blank tab; up to20 Web tabs can be open at once.
- Bookmarks can be added from the address-bar star or Bookmarks manager, renamed, edited, removed, searched, and opened in the current or a new Web tab. These are app bookmarks, not the browser's native bookmark database. They do not sync across devices/hostnames or require a server database. Clearing site data removes them.
- Current compatibility check: YouTube rendered its real page in the isolated browser; TikTok rendered its own error page with proxy/script compatibility errors. Use **Open in new tab** for sites that do not work inside Web. Do not interpret a connected transport as proof every site feature works.

### Header window launcher

The Desmos logo, Scientific Calculator and Kentucky Version labels open the full app in an `about:blank` wrapper window, initially showing their existing Notes/Web/Library destinations. The original tab is not redirected or closed. Inside the wrapper, these labels and app navigation change the inner route without opening more wrappers; the top-level address stays `about:blank`. Pop-ups must be allowed. A blocked window produces a visible error without navigating away.

**This is a presentation feature, not monitoring protection.** Real domains are still used. GoGuardian, browser extensions, managed-device software and network monitoring can still observe destinations. The launcher does not disable or hide from them. Direct external links intentionally open their actual destination separately.

## Troubleshooting

- **A health503 log but the Render URL now returns200:** check the log timestamp and deployment it belongs to. Compare the current `https://YOUR-SERVICE.onrender.com/api/health` response before changing code. A historical log alone does not prove the current release is failing.
- **Render URL works but custom-domainHTTPS fails:** check Settings→Custom Domains for domain verification and certificate status. Compare wildcard validation targets with the exact values Render supplies. A TLS handshake failure occurs before the app's health handler and is not fixed by adding MongoDB, changing CORS, or forcing the health response to200.
- **Old MongoDB503 health response:** the server is running older code. Deploy the latest commit and check the new response above.
- **Model429/503:** expand the attempt list for free and paid attempts. Free-only quota may trigger the single paid fallback; general account quota/time limits can stop routing. Failed paid attempts can still bill. Your draft remains local.
- **Model402:** check OpenRouter credit and key spending limit. No further model is tried; don't disable spending protection just to hide the error.
- **Model401/402:** verify the server-side key/account limits. No paid request is substituted.
- **Notes disappear on another hostname/device:** browser-only storage is intentionally separate. Use Export notes for a backup.
- **No lockfile in a repository export:** the existing Dockerfile generates one during install when absent; including `frontend/yarn.lock` is still recommended.
- **Content loads slowly:** library HTML is cached on first use; its disposable cache is capped at500MB. No persistent disk or database is required for notes.

These instructions do not mean the Render account, DNS, or certificates have already been configured for you. Hosting costs and provider quotas are separate from eliminating the database requirement.