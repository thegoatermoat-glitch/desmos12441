export function probeWisp(endpoint, onDisconnect, signal) {
  return new Promise((resolve, reject) => {
    let socket, settled = false;
    const fail = () => {
      if (settled) return;
      settled = true; clearTimeout(timer); socket?.close();
      reject(new Error('The connection could not be established.'));
    };
    const timer = setTimeout(fail, 6500);
    if (signal?.aborted) { fail(); return; }
    const abort = () => { if (!settled) fail(); else { socket.onclose = null; socket.close(); } };
    signal?.addEventListener('abort', abort, { once: true });
    try { socket = new WebSocket(endpoint); socket.binaryType = 'arraybuffer'; } catch { fail(); return; }
    socket.onmessage = event => {
      if (settled) return;
      const packet = event.data instanceof ArrayBuffer ? new Uint8Array(event.data) : null;
      // INFO (v2) or CONTINUE (v1) for stream zero, never just an open socket.
      if (!packet || packet.length < 5 || ![3, 5].includes(packet[0]) || packet.slice(1, 5).some(v => v !== 0)) { fail(); return; }
      clearTimeout(timer); settled = true;
      socket.onclose = () => { signal?.removeEventListener('abort', abort); onDisconnect?.(); };
      resolve(socket);
    };
    socket.onerror = fail;
    socket.onclose = fail;
  });
}

export function normalizeAddress(input) {
  const value = input.trim();
  if (!value) throw new Error('Enter a website address.');
  const candidate = /^[a-z][a-z\d+.-]*:/i.test(value) ? value : `https://${value}`;
  let url;
  try { url = new URL(candidate); } catch { throw new Error('Enter a valid website address, such as example.com.'); }
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || !url.hostname.includes('.')) throw new Error('Enter a public HTTP or HTTPS website address.');
  if (/^(localhost|127\.|10\.|192\.168\.|169\.254\.|0\.|172\.(1[6-9]|2\d|3[01])\.)/.test(url.hostname)) throw new Error('Local network addresses are not supported.');
  return url.href;
}