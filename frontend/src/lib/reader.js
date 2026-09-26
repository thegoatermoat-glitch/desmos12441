import { BareClient, BareMuxConnection } from '@mercuryworkshop/bare-mux';
import DOMPurify from 'dompurify';

// A safe, script-free fallback until a separate content hostname is configured.
export function createReader(host, onNavigate) {
  const frame = document.createElement('iframe');
  frame.title = 'Website reader'; frame.dataset.testid = 'browser-iframe';
  frame.setAttribute('sandbox', 'allow-scripts');
  frame.referrerPolicy = 'no-referrer';
  host.replaceChildren(frame);
  const connection = new BareMuxConnection('/bare-mux/worker.js');
  const client = new BareClient('/bare-mux/worker.js');
  let channel;
  const listener = event => {
    if (event.source === frame.contentWindow && event.data?.channel === channel && event.data.type === 'navigate') onNavigate(event.data.url);
  };
  window.addEventListener('message', listener);
  return {
    async open(url, endpoint, signal) {
      await connection.setTransport('/epoxy/index.mjs', [{ wisp: endpoint, wisp_v2: false, udp_extension_required: false }]);
      const response = await client.fetch(url, { signal, headers: { Accept: 'text/html,application/xhtml+xml,text/plain;q=0.9' } });
      if (!response.ok) throw new Error(`The website returned HTTP ${response.status}.`);
      const type = response.headers.get('content-type') || '';
      if (!/text\/|application\/xhtml/.test(type)) throw new Error('This address is not a readable web page.');
      const html = await response.text();
      if (html.length > 8_000_000) throw new Error('This page is too large for reader view.');
      const clean = DOMPurify.sanitize(html, { WHOLE_DOCUMENT: true,
        FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'base', 'meta', 'link', 'form', 'input', 'button', 'textarea'],
        FORBID_ATTR: ['srcset', 'target', 'nonce'] });
      const doc = new DOMParser().parseFromString(clean, 'text/html');
      const base = response.finalURL || url;
      doc.querySelectorAll('[href], [src]').forEach(element => {
        for (const attr of ['href', 'src']) if (element.hasAttribute(attr)) {
          try {
            const resolved = new URL(element.getAttribute(attr), base);
            if (['http:', 'https:'].includes(resolved.protocol)) element.setAttribute(attr, resolved.href);
            else if (!(attr === 'src' && resolved.protocol === 'data:')) element.removeAttribute(attr);
          } catch { element.removeAttribute(attr); }
        }
        if (element.tagName === 'IMG') { element.referrerPolicy = 'no-referrer'; element.crossOrigin = 'anonymous'; }
      });
      channel = crypto.randomUUID();
      const nonce = crypto.randomUUID().replaceAll('-', '');
      const meta = doc.createElement('meta'); meta.httpEquiv = 'Content-Security-Policy';
      meta.content = `default-src 'none'; script-src 'nonce-${nonce}'; img-src https: http: data:; style-src 'unsafe-inline'; font-src https: http: data:; connect-src 'none'; form-action 'none'; base-uri 'none'`;
      doc.head.prepend(meta);
      const style = doc.createElement('style');
      style.textContent = 'html{color-scheme:light}body{margin:32px auto;padding:0 24px;max-width:980px;font:16px/1.65 sans-serif;color:#303030;overflow-wrap:anywhere}img,video{max-width:100%;height:auto}pre,table{max-width:100%;overflow:auto}a{color:#107b3f}';
      doc.head.append(style);
      const scriptText = `document.addEventListener('click',function(e){var a=e.target.closest('a[href]');if(!a)return;e.preventDefault();parent.postMessage({channel:${JSON.stringify(channel)},type:'navigate',url:a.href},${JSON.stringify(window.location.origin)});});`;
      // Browsers hide nonce attributes during DOM serialization. Insert only our
      // trusted script string AFTER serializing the sanitized remote document.
      frame.srcdoc = '<!doctype html>' + doc.documentElement.outerHTML.replace('</body>', `<script nonce="${nonce}">${scriptText}</script></body>`);
      return base;
    },
    destroy() { window.removeEventListener('message', listener); frame.remove(); },
  };
}