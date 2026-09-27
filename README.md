# Desmos | Testing — independent recreation

A scientific calculator with a library, web workspace, and saved conversations. This is not an official Desmos service or an approved assessment tool.

## Render deployment

See **[RENDER_SETUP.md](RENDER_SETUP.md)** for the complete Render + Namecheap guide. **No database cluster is required.**

- `Dockerfile`: builds React with Node 22; runs FastAPI on Python 3.11 as a non-root user.
- `render.yaml`: creates one Docker web service; asks only for the server-side OpenRouter key.
- `scripts/start-render.sh`: binds to Render's supplied `PORT` and configured `HOST`.
- `/api/health`: reports app health and browser-only storage without connecting to a database.
- Production frontend uses same-origin `/api` calls, so the apex and wildcard hostnames work without separate frontend builds.

## Application

| Page | Path | Header shortcut |
| --- | --- | --- |
| Calculator | `/` | Calculator return link |
| Library | `/library` | Kentucky Version |
| Web | `/web` | Scientific Calculator |
| Notes | `/notes` | Desmos logo |

Calculator history, display settings and starred titles stay in browser storage. Full conversation messages and failed-request drafts now stay in IndexedDB; the backend is stateless for all new conversations. No cluster or server-side history database is required. Clearing site data deletes this device's history; each hostname/browser is separate. Export notes for backups. An explicit read-only import can recover earlier conversations from an already configured original database, but normal startup/health/new messages never use it.

Notes allows only exact models with audited publisher descriptions explicitly calling them uncensored/unrestricted, plus a false listed-provider moderation flag and known pricing. The allowlist and publisher evidence are in backend/model_allowlist.json. Currently only the paid Dolphin Mistral24B Venice Edition listing qualifies; no free alias or ordinary-model fallback is substituted. Free-first/cheapest-paid routing stays within the audited set, with one paid attempt, a conservative$0.01 estimate and1024-output-token default. This is not a hard billing cap; keep the OpenRouter key's real spending limit low. Publisher marketing is not a guarantee of unrestricted answers. Costs distinguish estimates from reported usage; the key stays server-side and conversations stay browser-only. See RENDER_SETUP.md for configuration.

The three header shortcuts launch the full app in an about:blank wrapper at their listed destination. Subsequent app navigation stays inside that window. Blocked pop-ups show an error. This does **not** hide real network destinations from GoGuardian, extensions, or managed-device/network monitoring, and the original tab remains open.

The loading screen adapts the supplied Desmos pulse/wordmark markup. It does not load the supplied external calculator API key, foreign SPA bundles, or Matomo analytics. The tab remains `Desmos | Testing`.

Third-party titles are fetched on demand from the requested repository, not included as a multi-gigabyte download. The local content cache is disposable. Some titles need external resources or are not compatible with a restricted iframe. Embedded third-party content can contain its own wording; neutral shell labels do not modify original titles or conversations and do not guarantee passage through network filters.

The two external Wisp endpoints are configurable and automatically retried in order. External service availability and arbitrary website compatibility are not guaranteed. Untrusted content is sandboxed without app-origin access; websites requiring origin-bound storage/SharedWorker may not function. Do not casually add `allow-same-origin` on the app origin.

## Development / preview

### Native deployment: Node 20 compatibility

The managed build runs Node20.19.2 with Yarn engine checks enabled. Calculator dependencies are intentionally pinned to `@cortex-js/compute-engine@0.27.0`, `mathlive@0.103.0`, and `katex@0.18.4`. Newer releases of these libraries (or their transitive dependencies) require Node21/22. Do not replace these pins without testing the actual build runtime.

The native build must pass `yarn install --prefer-offline --check-files --network-timeout 100000 && yarn build` **without** `--ignore-engines`. MathLive's vendored public fonts must match the installed MathLive version. This compatibility change does not alter Docker files or MongoDB configuration.

Scramjet1.1.0 is already bundled in `frontend/public/scramjet` and loaded as static browser assets. Its unused npm dependency was removed: the package has a `preinstall` invoking a pnpm-only check, which needlessly interferes with clean Yarn installs. Keep the public JS/WASM files, LICENSE.txt, and NOTICE.txt; this removal does not disable the browser runtime. Bare-mux and the transport dependency remain installed.

The preview environment retains React on port 3000, FastAPI on port 8001, and the existing `MONGO_URL`/`DB_NAME` settings. Render uses a separate production entrypoint; do not change the preview service ports.

- Frontend: `yarn install --frozen-lockfile --ignore-engines`, then `yarn start`.
- Backend runtime dependencies: `backend/requirements-render.txt` (generated from a clean virtual environment).
- Build: `cd frontend && yarn build`.
- Automated backend coverage: `pytest backend/tests` with `REACT_APP_BACKEND_URL` configured.

Keep all `.env` files out of Git and Docker. Never put the OpenRouter key into a `REACT_APP_*` variable. Rotate keys exposed in messages before public use, and set an OpenRouter spending limit. The app has no account login: the public conversation endpoint can consume its configured key's balance.

## Third-party notices

MathLive and Cortex Compute Engine supply math input/evaluation. Scramjet, bare-mux, and Epoxy supply the external transport. Preserve their license notices when distributing. Epoxy is AGPL-licensed. Library entries belong to their original creators; verify rights before redistribution.