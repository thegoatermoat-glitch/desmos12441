# Scientific Calculator & Companion Pages

## Original request
Recreate https://www.desmos.com/testing/kentucky/scientific one-to-one. Clicking Kentucky Version opens games from CoolDude2349/Offline-HTML-Games-Pack/offline. Clicking Scientific Calculator opens a Wisp-backed browser with automatic failover between the user-provided wisp and wisp2 endpoints. Clicking the attached Desmos logo opens Desmos-themed OpenRouter AI chat. Ask for confirmation when leaving a page. All pages retain the basic Desmos visual style.

## Explicit choices
- English; proceed autonomously after initial clarification.
- User supplied an OpenRouter key; backend environment only, never include in client, logs, or documents.
- User attached Desmos logo PNG and reference screenshot.
- The actual reference is a green 50px header, white page, centered 540x440 scientific calculator with gray keypad and blue enter button. Live reference takes precedence over inaccurate colors in generated design guidelines.

## Architecture
- React 19 / CRA / React Router, FastAPI, MongoDB via existing MONGO_URL and DB_NAME.
- MathLive math input and Cortex Compute Engine, not arbitrary JavaScript evaluation.
- OpenRouter via server-side httpx; multi-turn anonymous UUID sessions in MongoDB.
- Allowlisted GitHub game catalogue, lazy fetch/cache, sandboxed game player.
- Scramjet 1.1.0 / bare-mux 2.1.9 / Epoxy 3.0.1 for Wisp browser; service worker and honest failover/error states.
- Native beforeunload warning only. Latest user request explicitly removes all internal leave modals and their buttons.

## Status — 2026-09-25
- Calculator UI and library/notes/web pages implemented. Initial test report iteration_1: 7 backend tests passed, one live-chat test skipped, frontend core flows passed with bugs below.
- Fixed ans insertion selection, blocker callback guards, settings boolean initialization. Retest pending.
- Initial OpenRouter free-model429: switched to playbook-recommended Gemini2.5 Flash-Lite with GPT4o-mini fallback. Live validation pending.
- Initial Wisp handshake mismatch: now probes v1 without WebSocket subprotocol, compatible Epoxy2.1.28, v1 configuration. Live validation pending. Sandboxed external content may have storage/SharedWorker restrictions.
- No mocked integrations.

## Additional user requests / choices
- Exact tab name `Desmos | Testing`; favicon generated from attached blue-d image (favicon.webp / favicon-32.png / favicon.ico / apple-touch-icon.png).
- Companion pages simplified into Library, Web, Notes with neutral wording, no sparkles or promotional headers. Calculator preserved. Visible shell avoids games/unblocked/proxy/AI; original embedded content and generated conversations are not rewritten.
- Removed leave-confirmation description entirely; retained question and stay/leave controls.
- Namecheap for desmos.lol; arbitrary one-label subdomains desired.
- User selected one Render Docker web service + MongoDB Atlas. Deployment package added: Dockerfile, .dockerignore, render.yaml, scripts/start-render.sh, clean generated backend/requirements-render.txt, backend/frontend_host.py, /api/health, README.md and RENDER_SETUP.md.
- Production uses frontend REACT_APP_BACKEND_URL=/ (same-origin API for all wildcard hosts); preview protected environment unchanged.
- Render official documentation confirms wildcard domain support. Requires apex + wildcard in Render and Namecheap wildcard, _acme-challenge, _cf-custom-hostname CNAMEs. Earlier support guidance about no wildcard support applied to Emergent, not Render; use RENDER_SETUP.md verified docs.
- Actual Render/Atlas/DNS account setup has not been performed. Docker CLI is not available in the workspace; production build/static hosting/configuration will be validated separately.

## Priority / next tasks
- P0: Retest functional fixes and live integrations; verify Render production configuration and SPA hosting; complete deployment-readiness scan.
- P1: User supplies Atlas URI and OpenRouter key in Render, configures Namecheap DNS and TLS; verify live wildcard hostnames after account setup.
- P2: Isolated browsing origin for broader interactive site support; broader third-party title compatibility verification; optional conversation export.

## 2026-09-26 continuation
- User confirmed GN-Math cover source and generic 3D-title WebGL testing; then explicitly repeated removal of the entire internal leave prompt and requested Render instructions again.
- Removed the React route blocker/dialog completely. Kept native browser beforeunload. Removed outgoing-chat-link custom window.confirm too.
- Root-cause ans bug: MathLive rewrites `operatorname{ans}` into nested `operatorname{mathrm{ans}}` after another key. Parser replacement now handles both forms; verify chain2+3→ans+2=7.
- GN-Math cover metadata exact-normalized match importer added (`scripts/import_covers.py`).158 verified PNG covers downloaded to frontend/public/covers;142 unmatched/oversized entries retain fallback. No fuzzy sequel substitutions. CDN403 fixed by downloading from original GitHub raw files. Mapping/attribution: backend/data/game-covers.json.
- Bundle.js error RCA: opaque sandbox bypassed Scramjet service-worker navigation, so React's SPA fallback loaded inside the browser. Earlier test iteration2's connected status was insufficient proof of target content.
- Replaced default Web playback with real Wisp/BareClient fetch + DOMPurify script-free reader; target HTML is required before connected status. Links route through Wisp. No unsafe same-origin access granted to third-party pages.
- Full interactive workspace now supports separate CONTENT_ORIGIN via public/workspace/frame.html and frame.mjs; blank in preview means reader mode. Render docs reserve content.desmos.lol through wildcard DNS. Library also uses this isolated hostname when configured, allowing origin-dependent Unity/WebGL APIs without exposing app storage. The hostname has NOT been provisioned here.
- Production frontend hosting rejects unhandled browse/service routes rather than returning app index. CONTENT_ORIGIN private API boundary added.
- Iteration3 verified no internal confirmation, native browser beforeunload, ans5→7/negative/fractional cases,158coverPNGs, no responsiveoverflow. Found nonce-serialization bug, preview service-pathfallback, and hiddenfailoverstatus; all three corrected and self-verified.
- Post-fix checks:8backend/productionhosting regressiontests passed; `/browse/service/health`503 in preview; real Example Domain content confirmed inside reader; injected firstendpointfailure reached actualcontent viaendpoint2 and bothattemptrows visible; Learnmore link posts navigationtoIANA correctly. No ownReactbundle inreader.
- GNcovers imported and bundled locally. PublicmetadataURLs only; no keys inclientbuild. API/contentcache now streams downloads and caps cachedfiles500MB for Render disk/memory use.
- Unity/WebGL limitation remains: contexts initialize, but representative originalUnitytitles have storage/runtime/asset errors inopaque mode. SeparateCONTENT_ORIGIN architecture is implemented but cannot be live-verified until user's DNS/TLS is configured; don't claim all3Dtitles fixed. No unsafe allow-same-origin added toapphost.
- RenderDockerfiles/Blueprint/Atlas+Namecheapguide prepared, productionbuild previouslypassed; finalreadinessscanpending. NoDockerdaemonavailable, noRender/Atlas/DNSaccountprovisioningperformed.

## Known constraints
- Browser-controlled unload prompts cannot use custom text and may require interaction first.
- Public Wisp endpoints and arbitrary target websites cannot be guaranteed available.
- Third-party game compatibility varies; do not promise every listed file is fully offline.
- This is an independent recreation, not an official testing tool.