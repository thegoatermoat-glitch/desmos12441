import { BareMuxConnection } from '/bare-mux/index.mjs';

const parentOrigin = new URLSearchParams(location.search).get('parent');
if (!parentOrigin || new URL(parentOrigin).origin === location.origin) throw new Error('An isolated parent origin is required.');
const send = (type, extra = {}) => parent.postMessage({ channel: 'workspace', type, ...extra }, parentOrigin);
let frame, currentUrl, enginePromise, requestId, pending = false;
const fail = message => { if (pending) { pending = false; send('error', { message, requestId }); } };
async function initialize() {
  const { ScramjetController } = globalThis.$scramjetLoadController();
  const controller = new ScramjetController({ prefix: '/browse/service/', files: {
    wasm: '/scramjet/scramjet.wasm.wasm', all: '/scramjet/scramjet.all.js', sync: '/scramjet/scramjet.sync.js',
  }, flags: { serviceworkers: false, syncxhr: false, captureErrors: true } });
  await controller.init();
  const registration = await navigator.serviceWorker.register('/browse/sw.js', { scope: '/browse/', updateViaCache: 'none' });
  const worker = registration.installing || registration.waiting || registration.active;
  if (!worker) throw new Error('The content service did not start.');
  if (worker.state !== 'activated') await new Promise((resolve, reject) => {
    const cleanup = () => { clearTimeout(timer); worker.removeEventListener('statechange', changed); };
    const changed = () => {
      if (worker.state === 'activated') { cleanup(); resolve(); }
      else if (worker.state === 'redundant') { cleanup(); reject(new Error('The content service could not activate.')); }
    };
    const timer = setTimeout(() => { cleanup(); reject(new Error('The content service did not start.')); }, 15000);
    worker.addEventListener('statechange', changed); changed();
  });
  frame = controller.createFrame();
  frame.frame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-pointer-lock');
  frame.frame.title = 'Web page'; frame.frame.dataset.testid = 'proxied-website-frame';
  frame.frame.allow = 'autoplay; fullscreen; picture-in-picture'; frame.frame.allowFullscreen = true;
  frame.frame.referrerPolicy = 'no-referrer';
  frame.frame.addEventListener('load', () => {
    if (!currentUrl || !pending) return;
    const doc = frame.frame.contentDocument;
    if (!doc || doc.URL === 'about:blank') return;
    // The proxied document can expose the original site's URL through its API.
    // Inspect the shell-owned iframe URL, not the rewritten document.URL getter.
    if (!new URL(frame.frame.src).pathname.startsWith('/browse/service/') || doc.querySelector('[data-proxy-error]')) {
      fail('The website did not load through the content service.'); return;
    }
    pending = false; send('loaded', { url: currentUrl, title: doc.title, requestId });
  });
  frame.addEventListener('urlchange', event => { currentUrl = String(event.url); send('navigate', { url: currentUrl }); });
  document.getElementById('content').append(frame.frame);
  return new BareMuxConnection('/bare-mux/worker.js');
}
window.addEventListener('message', async event => {
  if (event.source !== parent || event.origin !== parentOrigin || event.data?.channel !== 'workspace' || event.data.type !== 'open') return;
  const incomingId = event.data.requestId;
  try {
    requestId = incomingId; pending = true;
    const url = new URL(event.data.url);
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Unsupported address.');
    enginePromise ||= initialize().catch(error => { enginePromise = null; throw error; });
    const connection = await enginePromise;
    if (requestId !== incomingId) return;
    await connection.setTransport('/epoxy/index.mjs', [{ wisp: event.data.endpoint, wisp_v2: false, udp_extension_required: false }]);
    if (requestId !== incomingId) return;
    currentUrl = url.href; frame.go(currentUrl);
  } catch (error) { if (requestId === incomingId) fail(error.message); }
});
navigator.serviceWorker?.addEventListener('message', event => {
  if (event.data?.type === 'proxy-navigation-error' && event.data.url === frame?.frame.src) fail('The website could not be reached.');
});
send('ready', { protocol: 2 });