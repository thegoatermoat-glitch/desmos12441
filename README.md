# Desmos | Testing — independent recreation

A scientific calculator with a library, web workspace, and saved conversations. This is not an official Desmos service or an approved assessment tool.

## Render deployment

See **[RENDER_SETUP.md](RENDER_SETUP.md)** for the complete Render + MongoDB Atlas + Namecheap wildcard-domain guide.

- `Dockerfile`: builds React with Node 22; runs FastAPI on Python 3.11 as a non-root user.
- `render.yaml`: creates one Docker web service; asks for the Atlas URI and server-side OpenRouter key.
- `scripts/start-render.sh`: binds to Render's supplied `PORT` and configured `HOST`.
- `/api/health`: checks the MongoDB connection.
- Production frontend uses same-origin `/api` calls, so the apex and wildcard hostnames work without separate frontend builds.

## Application

| Page | Path | Header shortcut |
| --- | --- | --- |
| Calculator | `/` | Calculator return link |
| Library | `/library` | Kentucky Version |
| Web | `/web` | Scientific Calculator |
| Notes | `/notes` | Desmos logo |

Calculator history, display settings, starred titles, and the list of conversation IDs are saved in browser storage. Conversation messages are saved in MongoDB. Clearing browser storage loses the local conversation list. Each hostname has separate browser storage.

Third-party titles are fetched on demand from the requested repository, not included as a multi-gigabyte download. The local content cache is disposable. Some titles need external resources or are not compatible with a restricted iframe. Embedded third-party content can contain its own wording; neutral shell labels do not modify original titles or conversations and do not guarantee passage through network filters.

The two external Wisp endpoints are configurable and automatically retried in order. External service availability and arbitrary website compatibility are not guaranteed. Untrusted content is sandboxed without app-origin access; websites requiring origin-bound storage/SharedWorker may not function. Do not casually add `allow-same-origin` on the app origin.

## Development / preview

The preview environment retains React on port 3000, FastAPI on port 8001, and the existing `MONGO_URL`/`DB_NAME` settings. Render uses a separate production entrypoint; do not change the preview service ports.

- Frontend: `yarn install --frozen-lockfile --ignore-engines`, then `yarn start`.
- Backend runtime dependencies: `backend/requirements-render.txt` (generated from a clean virtual environment).
- Build: `cd frontend && yarn build`.
- Automated backend coverage: `pytest backend/tests` with `REACT_APP_BACKEND_URL` configured.

Keep all `.env` files out of Git and Docker. Never put the OpenRouter key into a `REACT_APP_*` variable. Rotate keys exposed in messages before public use, and set an OpenRouter spending limit. The app has no account login: the public conversation endpoint can consume its configured key's balance.

## Third-party notices

MathLive and Cortex Compute Engine supply math input/evaluation. Scramjet, bare-mux, and Epoxy supply the external transport. Preserve their license notices when distributing. Epoxy is AGPL-licensed. Library entries belong to their original creators; verify rights before redistribution.