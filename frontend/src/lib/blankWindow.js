export function insideBlankWindow() {
  try {
    return window.self !== window.top && window.top.location.href === 'about:blank'
      && window.top.document.documentElement.dataset.calculatorWindow === 'true';
  } catch { return false; }
}

export function openBlankWindow(path) {
  const target = new URL(path, window.location.origin);
  if (target.origin !== window.location.origin) throw new Error('Only app pages can open in this window.');
  let popup;
  try { popup = window.open('about:blank', '_blank'); } catch { return false; }
  if (!popup || popup.closed) return false;
  try {
    popup.opener = null;
    const doc = popup.document;
    doc.title = document.title;
    doc.documentElement.dataset.calculatorWindow = 'true';
    doc.documentElement.style.cssText = 'height:100%;margin:0;';
    doc.body.style.cssText = 'height:100%;margin:0;overflow:hidden;';
    const favicon = doc.createElement('link');
    favicon.rel = 'icon'; favicon.href = new URL('/favicon.ico', window.location.origin).href;
    doc.head.appendChild(favicon);
    const frame = doc.createElement('iframe');
    frame.title = 'Scientific Calculator';
    frame.dataset.testid = 'about-blank-app-frame';
    frame.style.cssText = 'display:block;width:100%;height:100%;border:0;';
    frame.allow = 'autoplay; fullscreen; picture-in-picture; clipboard-write';
    frame.allowFullscreen = true;
    frame.referrerPolicy = 'no-referrer';
    frame.src = target.href;
    doc.body.replaceChildren(frame);
    popup.focus();
    return true;
  } catch {
    popup.close();
    return false;
  }
}