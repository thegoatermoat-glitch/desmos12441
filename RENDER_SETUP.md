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
OPENROUTER_MODEL=qwen/qwen3.8-27b:free
OPENROUTER_URL=https://openrouter.ai/api/v1/chat/completions
APP_ORIGIN=https://YOUR-SERVICE.onrender.com
CORS_ORIGINS=https://YOUR-SERVICE.onrender.com
HOST=0.0.0.0
CONTENT_ORIGIN=
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
- `OPENROUTER_FALLBACK_MODEL` is no longer used. No paid model fallback exists.
- Keep `CONTENT_ORIGIN` present and empty until configuring the isolated content hostname below.
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

## 4. Free model selection and privacy

The Notes page loads OpenRouter's current catalogue and offers free text models. Every request is checked against the free catalogue, restricted to `:free` IDs or `openrouter/free`, and sent with zero prompt/completion/request price caps and provider fallback disabled. Paid model IDs are rejected, even if manually submitted.

The default model is a preference, not a billing escape hatch: if it disappears from the free catalogue, the picker selects another currently listed free model. Each message tries that selection first, then automatically tries other distinct, currently free models after model-specific rate limits, temporary server/network errors, timeouts, or empty answers — **five model attempts maximum**. The same conversation context is sent on every attempt. No paid model is substituted.

Requests have a 55-second overall budget (including catalogue lookup), a 12-second per-model limit, and honor `Retry-After`; fewer than five attempts may run if the time budget expires, fewer models are available, or a provider requires a longer wait. Invalid credentials, account-wide quota, billing/account errors, or policy rejection stop retries rather than switching around those restrictions. The response shows the answering model, whether it switched, and an expandable attempt list. The successful **free routing ID**, not a potentially different provider-reported model name, becomes the selection for the next turn.

Free rate limits, provider availability, account settings, and model policies still apply; fallback improves resilience but cannot guarantee an answer. A provider listed as unmoderated does not mean a model has no built-in rules. The picker uses the live catalogue rather than inventing model availability.

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

## Troubleshooting

- **Old MongoDB503 health response:** the server is running older code. Deploy the latest commit and check the new response above.
- **Model429/503:** automatic retries tried available free alternatives or stopped at the shared quota/wait/time limit. Expand the attempt list for model-level results. The unsent message remains a local draft; retry later. There is no paid fallback.
- **Model401/402:** verify the server-side key/account limits. No paid request is substituted.
- **Notes disappear on another hostname/device:** browser-only storage is intentionally separate. Use Export notes for a backup.
- **No lockfile in a repository export:** the existing Dockerfile generates one during install when absent; including `frontend/yarn.lock` is still recommended.
- **Content loads slowly:** library HTML is cached on first use; its disposable cache is capped at500MB. No persistent disk or database is required for notes.

These instructions do not mean the Render account, DNS, or certificates have already been configured for you. Hosting costs and provider quotas are separate from eliminating the database requirement.