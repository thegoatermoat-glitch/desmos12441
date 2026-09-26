import { openDB } from 'idb';

let connection;
function database() {
  if (!connection) connection = openDB('calculator-notes', 1, {
    upgrade(db) { db.createObjectStore('conversations', { keyPath: 'id' }); },
    blocking() { connection?.then(db => db.close()); connection = null; },
    terminated() { connection = null; },
  }).catch(error => { connection = null; throw error; });
  return connection;
}
export async function listConversations() {
  const sessions = await (await database()).getAll('conversations');
  return sessions.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}
export async function saveConversation(session) {
  await (await database()).put('conversations', session);
  window.dispatchEvent(new CustomEvent('notes-updated', { detail: session.id }));
}
export async function getConversation(id) { return (await database()).get('conversations', id); }
export async function deleteConversation(id) {
  await (await database()).delete('conversations', id);
  window.dispatchEvent(new CustomEvent('notes-updated', { detail: id }));
}
export function newConversation(model) {
  return { id: crypto.randomUUID(), title: 'New conversation', messages: [],
    model, draft: '', updated_at: new Date().toISOString() };
}
export function requestMessages(session, content) {
  const previous = session.messages.slice(-20).map(({ role, content }) => ({ role, content }));
  while (previous.length && (previous[0].role !== 'user' || previous.reduce((n, m) => n + m.content.length, content.length) > 48000)) previous.shift();
  return [...previous, { role: 'user', content }];
}
export function downloadConversations(sessions) {
  const blob = new Blob([JSON.stringify({ version: 1, exported_at: new Date().toISOString(), conversations: sessions }, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = 'notes-backup.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}