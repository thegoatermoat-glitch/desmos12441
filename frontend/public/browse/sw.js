/* Scramjet is restricted to /browse/ so application APIs and games are untouched. */
self.importScripts('/scramjet/scramjet.all.js');
const { ScramjetServiceWorker } = self.$scramjetLoadWorker();
const scramjet = new ScramjetServiceWorker();
async function reportNavigationFailure(event) {
  if (event.request.mode !== 'navigate') return;
  const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
  clients.forEach(client => client.postMessage({ type: 'proxy-navigation-error', url: event.request.url }));
}
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  if (!new URL(event.request.url).pathname.startsWith('/browse/service/')) return;
  event.respondWith((async () => {
    try {
      await scramjet.loadConfig();
      const response = await scramjet.fetch(event);
      if (event.request.mode === 'navigate' && response.status >= 500) {
        await reportNavigationFailure(event);
      }
      return response;
    } catch {
      await reportNavigationFailure(event);
      return new Response('<!doctype html><title>Website unavailable</title><p data-proxy-error>This website could not be reached.</p>', { status: 502, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
    }
  })());
});