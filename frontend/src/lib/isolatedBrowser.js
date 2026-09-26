export function createIsolatedBrowser(host, origin, onNavigate) {
  if (new URL(origin).origin === window.location.origin) throw new Error('The content hostname must be different from the application hostname.');
  const frame = document.createElement('iframe');
  frame.title = 'Website browser'; frame.dataset.testid = 'browser-iframe';
  frame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-pointer-lock');
  frame.src = `${origin}/workspace/frame.html?parent=${encodeURIComponent(window.location.origin)}`;
  host.replaceChildren(frame);
  let readyResolve, readyReject, pending;
  const ready = new Promise((resolve, reject) => { readyResolve = resolve; readyReject = reject; });
  ready.catch(() => {});
  const readyTimer = setTimeout(() => readyReject(new Error('The content hostname is not ready. Check its DNS and HTTPS setup.')), 20000);
  const listener = event => {
    if (event.origin !== origin || event.source !== frame.contentWindow || event.data?.channel !== 'workspace') return;
    if (event.data.type === 'ready') { clearTimeout(readyTimer); readyResolve(); }
    if (event.data.type === 'loaded') { pending?.resolve(event.data.url); pending = null; }
    if (event.data.type === 'error') { pending?.reject(new Error(event.data.message)); pending = null; }
    if (event.data.type === 'navigate') onNavigate(event.data.url);
  };
  window.addEventListener('message', listener);
  return {
    async open(url, endpoint, signal) {
      await ready;
      if (signal?.aborted) throw new Error('The website took too long to respond.');
      return new Promise((resolve, reject) => {
        const onAbort = () => { pending = null; reject(new Error('The website took too long to respond.')); };
        signal?.addEventListener('abort', onAbort, { once: true });
        pending = {
          resolve: value => { signal?.removeEventListener('abort', onAbort); resolve(value); },
          reject: error => { signal?.removeEventListener('abort', onAbort); reject(error); },
        };
        frame.contentWindow.postMessage({ channel: 'workspace', type: 'open', url, endpoint }, origin);
      });
    },
    destroy() { clearTimeout(readyTimer); pending?.reject(new Error('Navigation cancelled.')); window.removeEventListener('message', listener); frame.remove(); },
  };
}