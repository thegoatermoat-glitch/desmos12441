import { BareMuxConnection } from '/bare-mux/index.mjs';

const parentOrigin = new URLSearchParams(location.search).get('parent');
if (!parentOrigin || new URL(parentOrigin).origin === location.origin) throw new Error('An isolated parent origin is required.');
const send = (type, extra = {}) => parent.postMessage({ channel: 'workspace', type, ...extra }, parentOrigin);
let frame, currentUrl, enginePromise;
async function initialize() {
  const { ScramjetController } = globalThis.$scramjetLoadController();
  const controller = new ScramjetController({ prefix: '/browse/service/', files: {
    wasm: '/scramjet/scramjet.wasm.wasm', all: '/scramjet/scramjet.all.js', sync: '/scramjet/scramjet.sync.js',
  }, flags: { serviceworkers: false, syncxhr: false, captureErrors: true } });
  await controller.init();
  const registration = await navigator.serviceWorker.register('/browse/sw.js', { scope: '/browse/' });
  if (!registration.active) await new Promise((resolve, reject) => {
    const worker = registration.installing || registration.waiting;
    const timer = setTimeout(() => reject(new Error('The content service did not start.')), 15000);
    worker.addEventListener('statechange', () => { if (worker.state === 'activated') { clearTimeout(timer); resolve(); } });
  });
  frame = controller.createFrame();
  frame.frame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-pointer-lock');
  frame.frame.addEventListener('load', () => {
    if (!currentUrl || frame.frame.contentDocument?.URL === 'about:blank') return;
    send('loaded', { url: currentUrl });
  });
  frame.addEventListener('urlchange', event => { currentUrl = String(event.url); send('navigate', { url: currentUrl }); });
  document.getElementById('content').append(frame.frame);
  return new BareMuxConnection('/bare-mux/worker.js');
}
window.addEventListener('message', async event => {
  if (event.source !== parent || event.origin !== parentOrigin || event.data?.channel !== 'workspace' || event.data.type !== 'open') return;
  try {
    const url = new URL(event.data.url);
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Unsupported address.');
    enginePromise ||= initialize();
    const connection = await enginePromise;
    await connection.setTransport('/epoxy/index.mjs', [{ wisp: event.data.endpoint, wisp_v2: false, udp_extension_required: false }]);
    currentUrl = url.href; frame.go(currentUrl);
  } catch (error) { send('error', { message: error.message }); }
});
navigator.serviceWorker?.addEventListener('message', event => { if (event.data?.type === 'proxy-navigation-error') send('error', { message: 'The website could not be reached.' }); });
send('ready');