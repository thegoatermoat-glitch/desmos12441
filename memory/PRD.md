# Scientific Calculator & Companion Pages

## Original request
Recreate https://www.desmos.com/testing/kentucky/scientific one-to-one. Clicking Kentucky Version opens games from CoolDude2349/Offline-HTML-Games-Pack/offline. Clicking Scientific Calculator opens a Wisp-backed browser with automatic failover between the user-provided wisp and wisp2 endpoints. Clicking the attached Desmos logo opens Desmos-themed OpenRouter AI chat. Ask for confirmation when leaving a page. All pages retain the basic Desmos visual style.

## Explicit choices
- English; proceed autonomously after initial clarification.
- User supplied an OpenRouter key; backend environment only, never include in client, logs, or documents.
- User attached Desmos logo PNG and reference screenshot.
- The actual reference is a green 50px header, white page, centered 540x440 scientific calculator with gray keypad and blue enter button. Live reference takes precedence over inaccurate colors in generated design guidelines.

## Architecture
- React 19 / CRA / React Router and stateless FastAPI. Normal usage requires NO database. Full conversations and failed-message drafts live in browser IndexedDB; localStorage holds UI preferences/pointers. Optional explicit legacy import is read-only and never runs during normal startup or chat.
- MathLive math input and Cortex Compute Engine, not arbitrary JavaScript evaluation.
- OpenRouter via server-side httpx; client-generated UUID sessions and client-supplied bounded multi-turn history. Live free-model catalogue; up to five distinct free model attempts, strict zero-price caps, no paid fallback. Actual responder and retry metadata are displayed and saved locally.
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
- P0: Five-free-model fallback completed and verified (2026-09-26; iteration_7 report, iteration8-named XML artifacts). No known blocker in the requested scope. Preserve verified Node20 dependency pins.
- P1: User requested Render instructions; RENDER_SETUP.md is current and database-free. User must save latest code and perform/verify their Render rollout; no account, DNS/TLS, or live Docker runtime provisioned here.
- P2: Loader explicitly skipped for this continuation; do not change it. Isolated browsing-origin/Unity compatibility remains dependent on user's DNS/TLS. Optional enhancement: import previously exported browser notes.

## 2026-09-26 continuation
- Render reported missing `/frontend/yarn.lock` during Docker COPY although Root Directory/build context were correct. Workspace lockfile exists but Render checkout did not contain it. Updated Dockerfile to copy frontend directory once and conditionally use frozen install when lockfile exists, otherwise generate it from package.json.
- Lockfile fix VERIFIED: iteration_4 tested real installs with and without lockfile, checksum preserved for frozen install, generated lock for absent-file install, production-equivalent React build passed,8regressiontests passed. Test fixtures live outside repo in /root/render-lock-check. No DockerCLI available, so actual Render image build must be verified by user redeploying latest commit.
- Secrets remain excluded from Git and Docker intentionally for external Render. Repeated generic readiness scan reports only an Emergent-managed-deployment `.gitignore` requirement, inapplicable to this Render Docker target; all other checks pass. Do NOT expose .env/API keys to satisfy that false positive or change protected previewdatabasevariables.
- Immediate next action: Save to Github, then Render Manual Deploy → Deploy latest commit. Keep runtimeDocker, rootdirectoryblank, buildcontextdot, Dockerfile./Dockerfile, and custombuild/startcommandsblank. Optional reliability improvement: retain frontend/yarn.lock in repository exports so all installs stay pinned.
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

## Native Emergent build bug — Node 20.19.2
- Latest user target is native Emergent/Kubernetes, not the earlier Render setup. User explicitly forbids Docker-related changes and approved Node-20-compatible dependencies.
- Reported yarn install failure: root Compute Engine0.135.0 requiresNode>=22.3.0. Direct dependency inspection also found MathLive0.110.0 pulls incompatible ComputeEngine0.58.0 (Node>=21.7.3), and KaTeX0.18.9 pulls Commander15 (Node>=22.12.0).
- Original failure reproduced using exactNode20.19.2 and production install command; evidence `/app/test_reports/node20-before.log`.
- Changed only application dependency versions using Yarn: ComputeEngine0.27.0, MathLive0.103.0 (transitive ComputeEngine0.24.1), KaTeX0.18.4 (Commander8). Exact pins and lockfile updated. MathLive public fonts resynchronized. No forced resolutions/engine bypass introduced for this fix.
- Dockerfile/.dockerignore/Render scripts, protected MONGO_URL/DB_NAME, and auth configuration were NOT modified.
- General deployment scanner initially returnedpass despite suppliedenginefailure; it is not sufficient evidence. Mandatory testing_agent verification must include strict clean install and build underNode20.19.2 plus calculator/KaTeX regression tests before this bug is calledfixed.
- Iteration5 independenttests reproducedoriginalNode22engineerror, passedcalculator/KaTeXregressions and20/20fontchecks, but found strictfreshfixture install invoking Scramjet's `npx only-allow pnpm` preinstall. Npx-wrappedruntime can additionally leak npm_config_call into nestednpx; finalverification must put the exactNode20.19.2binary directlyonPATH toavoidtest-harnessartifacts.
- Removedunused@mercuryworkshop/scramjet npmdependency viaYarn. Its already-vendored publicJS/WASMassets are preservedandcontinuebeingloadedbyworkspace/frame.htmlandserviceworker; noapplicationcodeimportedthepackage. OriginalpackageLICENSE copiedto public/scramjet/LICENSE.txt andprovenancedocumentedNOTICE.txt. Noengine/scriptbypassflags introduced.
- VERIFIED by testing_agent iteration6: realstrictcleaninstall andproductionbuild underexactNode20.19.2/Yarn1.22.22 withlock ANDwithoutlock bothpass, withoutengine/scriptbypass. NativebinaryPATHused; wrappercheckalsopassedafterunusedpackageremoval. Reports/logs: `/app/test_reports/iteration_6.json` andnode20-iteration6-*.log.
- Independentregressions:14/14pytestdependency/coreAPItests pass; calculatorarithmetic,ans,DEG/RADtrig,sqrt,fractions pass; NotesKaTeX/responsive/20fontchecks passiniteration5. VendoredScramjetJS/WASMreturn200withcorrectMIMEtypes. No APIsmocked.
- Finaldeployment_agentrecheckreturnedPASS/nofindings. Actualproductionrollout has NOTbeenstarted orclaimedverifiedhere. Usernextaction: retry native Emergent deployment. Existing isolated-host/Unity limitations areunchangedandoutside thisdependencyfix.
- Futuremaintenanceenhancement: automateexact-runtimeclean-install/build compatibilitytests on eachdependencyupdate. ExistingnonfatalYarnpeer/resolutionwarningscanbecleaned separately withoutremovingplatformsecurityresolutions.

## Latest request — browser-only notes, free-only model choices, loading screen
- User approved browser-only full conversation history (no paid cluster), less-restrictive OpenRouter options from current catalogue, **free models only with no paid fallback**.
- User supplied full Desmos loader HTML. Only its pulse/wordmark visual is adapted with the supplied local Desmos logo; foreign calculator API key, proprietary SPA script links, and analytics are intentionally not imported. Title/favicon/calculator design unchanged.
- Live public model catalogue checked directly: free Qwen/Gemma/Nemotron/etc options exist; Dolphin/Hermes are NOT currently listed as free despite stale playbook examples. UI reports actual provider-moderation metadata, not a guarantee of unrestricted replies.
- Backend rewritten stateless POST/api/chat/completions with UUID session_id and bounded prior messages. GET/api/chat/models returns live free-text allowlist. Providermax_price prompt/completion/request=0, allow_fallbacks=false, require_parameters=true; no models fallback array. Paid IDs rejectedserver-side. Existing paidfallbackenvkey leftblank/unused; preferredmodelqwen/qwen3.8-27b:free.
- Startup and/api/health no longer create/query MongoDB. database.py removed. Protected MONGO_URL/DB_NAME environment keys preserved untouched but not required. Optional explicit read-only legacy import lazily connects only when the user asks to recover an old session; original records are not deleted. Obsolete writable session/status APIs return410.
- Frontend idb8.0.3 installed underNode20.19.2. Full conversations/drafts in IndexedDB; browser-local deletion, exportbackup, session switching, and free-model selector. Native browser leave warning retained; no internal leave dialogs.
- Boot/lazy-page loader uses public/loader.css plusAppLoader, matching supplied140px pulse and120x25wordmark. No new external analytics; existing session recording/autocapture disabled to protect local transcript display.
- RenderBlueprint/startscript no longer request or require MongoDB/DB_NAME. Dockerfile unchanged. RENDER_SETUP.md rewritten without cluster steps; READMEupdated. Newhealthresponse {status:ok,storage:browser,database_required:false}.
- Historical pending checks above are superseded for the fallback scope by the verified continuation below. Loader remains outside the latest approved scope. No production integration is mocked.

## 2026-09-26 — five-free-model fallback continuation (VERIFIED)
- Latest explicit user choice: “Focus only on completing and testing the AI fallback.; also send render instructions”. “Skip the loader for now.” No new integrations or database changes requested.
- Completed backend helper `/backend/free_fallback.py`: selected model first, at most five DISTINCT currently free candidates; retry model-specific429,408,500,502/503/504, unavailable404, network/timeout and empty replies; stop auth/account/billing/policy/shared-quota failures. Invalid/non-finite Retry-After cannot cause a crash. Full request context/session header stays unchanged across attempts.
- Limits: 55 seconds overall (including catalogue lookup),12 seconds per attempt, respecting Retry-After; fewer than five attempts can run when budget/quota/wait limits require. Failure is sanitized with attempts and paid_fallback:false; no guarantee of free provider availability.
- Free catalogue preserves explicit zero prices and deduplicates. OpenRouter currently omits optional request pricing on free variants: absent is accepted only with explicit zero prompt/completion; present nonzero/null is rejected. Provider caps for prompt/completion/request remain0, allow_fallbacks:false, require_parameters:true. No upstream models-array or paid base-slug retry.
- Response has requested_model, actual provider-reported model, used_model (verified-free routing ID), attempts and fallback_used. Frontend switches next selection using used_model, not the potentially differently named provider-reported slug.
- Added `/frontend/src/components/chat/ModelAttempts.jsx`; success and error attempt details, actual “Answered by” name, and switched-free-model indicator. Metadata is stored with the assistant message in IndexedDB and included in export. Failed sends keep the draft; retries do not duplicate the user message.
- Updated RENDER_SETUP.md: no database required, five-model logic, stop conditions/time limits, troubleshooting and privacy. Docker/Render configs and protected environment keys unchanged in this continuation. No loader changes.
- Live curl observed requested qwen/qwen3.8-27b:free →429 → inclusionai/ling-3.0-flash-fin:free →200 READY; fallback_used:true. Testing agent verified real multi-turn marker retention, isolated sessions, browser reload persistence and responsive layouts320/768/1024/1440; production yarn build passed.
- 27/27 backend tests passed: `/test_reports/pytest/pytest_iteration8_full_scope.xml`. Report `/test_reports/iteration_7.json`. Fifth-attempt success/exhaustion/model-alias UI cases used explicit MOCKED test fixtures; real runtime integration is NOT mocked.
- Agent's only low-priority finding (calculator operator/Enter missing test IDs/names) was a false positive: existing calc-key-plus/divide/multiply/minus/enter selectors and aria-label/title verified in browser;2+3=5passed. Calculator code left unchanged; report has main-agent resolution.
- Test files changed by testing agent: `/backend/tests/test_free_fallback_and_catalogue.py` (new), `/backend/tests/test_chat_live_and_unit_contracts.py` (updated obsolete helper/payload contracts). No production code changes by tester. No auth credentials created/modified; existing key stays only in backend environment.
- Next: user deploys latest repository code to Render and checks /api/health plus a Notes conversation. No remaining P0 fallback defects; actual Render rollout is unverified. Future: optional notes-backup import and isolated content-host testing, not part of this work.