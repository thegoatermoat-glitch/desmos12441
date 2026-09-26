import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';
import { normalizeAddress, probeWisp } from '../lib/proxy';
import { createReader } from '../lib/reader';
import { createIsolatedBrowser } from '../lib/isolatedBrowser';

export const useProxyBrowser = host => {
  const [status, setStatus] = useState('idle'), [error, setError] = useState(''), [active, setActive] = useState(-1);
  const [address, setAddress] = useState(''), [attempts, setAttempts] = useState([]), [mode, setMode] = useState('reader');
  const config = useRef(null), renderer = useRef(null), socket = useRef(null), abort = useRef(null), frame = useRef(null);
  const alive = useRef(true), working = useRef(false), current = useRef(''), history = useRef([]), position = useRef(-1), navigateRef = useRef(null);
  const stop = () => { if (socket.current) { socket.current.onclose = null; socket.current.close(); socket.current = null; } };
  useEffect(() => { alive.current = true; return () => { alive.current = false; abort.current?.abort(); stop(); renderer.current?.destroy(); }; }, []);
  const connect = async (url, start = 0) => {
    if (working.current || !alive.current) return;
    working.current = true; setError(''); setAttempts([]); stop();
    abort.current?.abort(); abort.current = new AbortController();
    let lastError;
    try {
      config.current ||= await api('/config');
      if (!alive.current) return;
      if (!renderer.current) {
        const isolated = config.current.content_origin;
        setMode(isolated ? 'interactive' : 'reader');
        renderer.current = isolated ? createIsolatedBrowser(host.current, isolated, value => setAddress(value))
          : createReader(host.current, value => navigateRef.current(value));
      }
      for (let index = start; index < config.current.wisp_endpoints.length; index++) {
        if (!alive.current) return;
        setActive(index); setStatus(index ? 'switching' : 'connecting');
        setAttempts(previous => [...previous, { index, state: 'Connecting' }]);
        try {
          const endpoint = config.current.wisp_endpoints[index];
          socket.current = await probeWisp(endpoint, () => {
            if (!working.current && alive.current) connect(current.current, index + 1);
          }, abort.current.signal);
          setStatus('loading');
          const timeout = setTimeout(() => abort.current?.abort(), 30000);
          let resolved;
          try { resolved = await renderer.current.open(url, endpoint, abort.current.signal); }
          finally { clearTimeout(timeout); }
          if (!alive.current) return;
          setAddress(resolved || url); current.current = resolved || url;
          stop();
          setAttempts(previous => previous.map(a => a.index === index ? { ...a, state: 'Connected' } : a));
          setStatus('connected'); return;
        } catch (failure) {
          lastError = failure; stop();
          if (!alive.current) return;
          setAttempts(previous => previous.map(a => a.index === index ? { ...a, state: 'Unavailable' } : a));
          if (abort.current.signal.aborted) abort.current = new AbortController();
        }
      }
      setStatus('unavailable'); setError(lastError?.message || 'Neither connection is available right now.');
    } catch (failure) { if (alive.current) { setStatus('unavailable'); setError(failure.message); } }
    finally { working.current = false; }
  };
  const navigate = value => {
    try {
      const url = normalizeAddress(value);
      if (new URL(url).origin === window.location.origin) throw new Error('Open a different website here.');
      if (working.current) return;
      history.current = [...history.current.slice(0, position.current + 1), url]; position.current = history.current.length - 1;
      current.current = url; setAddress(url); connect(url);
    } catch (failure) { setError(failure.message); }
  };
  navigateRef.current = navigate;
  frame.current = {
    back: () => { if (position.current > 0) connect(history.current[--position.current]); },
    forward: () => { if (position.current < history.current.length - 1) connect(history.current[++position.current]); },
  };
  return { status, error, active, address, setAddress, attempts, navigate, frame, mode,
    retry: () => current.current ? connect(current.current) : navigate(address) };
};