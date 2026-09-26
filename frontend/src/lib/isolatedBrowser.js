export function createIsolatedBrowser(host, origin, onNavigate) {
  origin = new URL(origin).origin;
  if (new URL(origin).origin === window.location.origin) throw new Error('The content hostname must be different from the application hostname.');
  const frame = document.createElement('iframe');
  frame.title = 'Website browser'; frame.dataset.testid = 'browser-iframe';
  frame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-pointer-lock');
  frame.allow = 'autoplay; fullscreen; picture-in-picture'; frame.allowFullscreen = true;
  frame.referrerPolicy = 'no-referrer';
  frame.src = `${origin}/workspace/frame.html?parent=${encodeURIComponent(window.location.origin)}`;
  host.replaceChildren(frame);
  let readyResolve, readyReject, pending, disposed = false, protocol = 1;
  const ready = new Promise((resolve, reject) => { readyResolve = resolve; readyReject = reject; });
  ready.catch(() => {});
  const readyTimer = setTimeout(() => readyReject(new Error('The content hostname is not ready. Check its DNS and HTTPS setup.')), 20000);
  const listener = event => {
    if (event.origin !== origin || event.source !== frame.contentWindow || event.data?.channel !== 'workspace') return;
    if (event.data.type === 'ready') { protocol = event.data.protocol || 1; clearTimeout(readyTimer); readyResolve(); }
    if (['loaded', 'error'].includes(event.data.type) && protocol >= 2 && event.data.requestId !== pending?.id) return;
    if (event.data.type === 'loaded') { pending?.resolve({ url: event.data.url, title: event.data.title }); pending = null; }
    if (event.data.type === 'error') { pending?.reject(new Error(event.data.message)); pending = null; }
    if (event.data.type === 'navigate') onNavigate(event.data.url);
  };
  window.addEventListener('message', listener);
  return {
    async open(url, endpoint, signal) {
      if (disposed || signal?.aborted) throw new Error('Navigation cancelled.');
      await new Promise((resolve, reject) => {
        const onAbort = () => reject(new Error('Navigation cancelled.'));
        signal?.addEventListener('abort', onAbort, { once: true });
        ready.then(resolve, reject).finally(() => signal?.removeEventListener('abort', onAbort));
      });
      if (disposed) throw new Error('Navigation cancelled.');
      if (signal?.aborted) throw new Error('The website took too long to respond.');
      return new Promise((resolve, reject) => {
        const id = crypto.randomUUID();
        const onAbort = () => { pending = null; reject(new Error('The website took too long to respond.')); };
        signal?.addEventListener('abort', onAbort, { once: true });
        pending = {
          id,
          resolve: value => { signal?.removeEventListener('abort', onAbort); resolve(value); },
          reject: error => { signal?.removeEventListener('abort', onAbort); reject(error); },
        };
        frame.contentWindow.postMessage({ channel: 'workspace', type: 'open', url, endpoint, requestId: id }, origin);
      });
    },
    destroy() { disposed = true; clearTimeout(readyTimer); readyReject(new Error('Navigation cancelled.')); pending?.reject(new Error('Navigation cancelled.')); pending = null; window.removeEventListener('message', listener); frame.remove(); },
  };
}