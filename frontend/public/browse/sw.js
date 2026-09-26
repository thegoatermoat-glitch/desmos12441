/* Scramjet is restricted to /browse/ so application APIs and games are untouched. */
self.importScripts('/scramjet/scramjet.all.js');
const { ScramjetServiceWorker } = self.$scramjetLoadWorker();
const scramjet = new ScramjetServiceWorker();
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  if (!new URL(event.request.url).pathname.startsWith('/browse/service/')) return;
  event.respondWith((async () => {
    try {
      await scramjet.loadConfig();
      const response = await scramjet.fetch(event);
      if (event.request.mode === 'navigate' && response.status >= 500) {
        const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
        clients.forEach(client => client.postMessage({ type: 'proxy-navigation-error' }));
      }
      return response;
    } catch {
      const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      clients.forEach(client => client.postMessage({ type: 'proxy-navigation-error' }));
      return new Response('This website could not be reached.', { status: 502, headers: { 'Content-Type': 'text/plain' } });
    }
  })());
});