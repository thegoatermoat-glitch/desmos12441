import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';
import { normalizeAddress, probeWisp } from '../lib/proxy';
import { pageTitle } from '../lib/browserWorkspace';
import { createReader } from '../lib/reader';
import { createIsolatedBrowser } from '../lib/isolatedBrowser';

export const useProxyBrowser = (host, options = {}) => {
  const initial = useRef(options.initial || {}), onChange = useRef(options.onChange);
  onChange.current = options.onChange;
  const [status, setStatus] = useState('idle'), [error, setError] = useState(''), [active, setActive] = useState(-1);
  const [address, setAddress] = useState(initial.current.url || ''), [attempts, setAttempts] = useState([]), [mode, setMode] = useState('reader');
  const [shortcuts, setShortcuts] = useState([]), [navigation, setNavigation] = useState({ back: initial.current.position > 0, forward: initial.current.position < (initial.current.history?.length || 0) - 1 });
  const config = useRef(null), renderer = useRef(null), socket = useRef(null), abort = useRef(null), frame = useRef(null);
  const alive = useRef(true), working = useRef(false), current = useRef(initial.current.url || '');
  const history = useRef(initial.current.history || []), position = useRef(initial.current.position ?? -1), navigateRef = useRef(null), connectRef = useRef(null);
  const stop = () => { if (socket.current) { socket.current.onclose = null; socket.current.close(); socket.current = null; } };
  const publish = (url, title) => {
    current.current = url; setAddress(url);
    if (position.current >= 0) history.current[position.current] = url;
    setNavigation({ back: position.current > 0, forward: position.current < history.current.length - 1 });
    onChange.current?.({ url, title: typeof title === 'string' && title.trim() ? title.slice(0, 160) : pageTitle(url), history: [...history.current], position: position.current });
  };
  const append = url => {
    history.current = [...history.current.slice(0, position.current + 1), url].slice(-100);
    position.current = history.current.length - 1;
  };
  useEffect(() => {
    alive.current = true;
    api('/config').then(value => {
      if (!alive.current) return;
      config.current = value; setShortcuts(value.browser_shortcuts || []);
      setMode(value.content_origin ? 'interactive' : 'reader');
    }).catch(() => { if (alive.current) setError('Web settings could not be loaded. Try opening an address again.'); });
    if (initial.current.url) connectRef.current(initial.current.url);
    return () => { alive.current = false; abort.current?.abort(); stop(); renderer.current?.destroy(); renderer.current = null; };
  }, []);
  useEffect(() => {
    if (host.current?.firstElementChild) host.current.firstElementChild.dataset.testid = options.frameId || 'browser-iframe';
  }, [options.frameId, status, host]);
  const connect = async (url, start = 0) => {
    if (working.current || !alive.current) return;
    working.current = true; setError(''); setAttempts([]); stop();
    abort.current?.abort(); abort.current = new AbortController();
    let lastError;
    try {
      config.current ||= await api('/config');
      if (!alive.current) return;
      setShortcuts(config.current.browser_shortcuts || []);
      if (new URL(url).origin === config.current.content_origin) throw new Error('Open a website other than the content hostname.');
      if (!renderer.current) {
        const isolated = config.current.content_origin;
        setMode(isolated ? 'interactive' : 'reader');
        renderer.current = isolated ? createIsolatedBrowser(host.current, isolated, (value, title) => {
          if (!alive.current) return;
          let normalized;
          try { normalized = normalizeAddress(value); } catch { return; }
          if (!working.current && normalized !== current.current) append(normalized);
          publish(normalized, title);
        }) : createReader(host.current, value => navigateRef.current(value));
        host.current.firstElementChild.dataset.testid = options.frameId || 'browser-iframe';
      }
      for (let index = start; index < config.current.wisp_endpoints.length; index++) {
        if (!alive.current) return;
        setActive(index); setStatus(index ? 'switching' : 'connecting');
        setAttempts(previous => [...previous, { index, state: 'Connecting' }]);
        try {
          const endpoint = config.current.wisp_endpoints[index];
          socket.current = await probeWisp(endpoint, () => {
            if (!working.current && alive.current) connectRef.current(current.current, index + 1);
          }, abort.current.signal);
          setStatus('loading');
          const signal = abort.current, timeout = setTimeout(() => signal.abort(), 30000);
          let resolved;
          try { resolved = await renderer.current.open(url, endpoint, signal.signal); }
          finally { clearTimeout(timeout); }
          if (!alive.current) return;
          publish(typeof resolved === 'string' ? resolved : resolved?.url || url, resolved?.title);
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
  connectRef.current = connect;
  const navigate = value => {
    try {
      const url = normalizeAddress(value);
      if ([window.location.origin, config.current?.content_origin].includes(new URL(url).origin)) throw new Error('Open a different website here.');
      if (working.current) return;
      if (url !== current.current || !history.current.length) append(url);
      publish(url); connect(url);
    } catch (failure) { setError(failure.message); }
  };
  navigateRef.current = navigate;
  const move = delta => {
    const target = position.current + delta;
    if (working.current || target < 0 || target >= history.current.length) return;
    position.current = target; const url = history.current[target]; publish(url); connect(url);
  };
  frame.current = { back: () => move(-1), forward: () => move(1) };
  return { status, error, active, address, setAddress, attempts, navigate, frame, mode, shortcuts,
    canBack: navigation.back, canForward: navigation.forward,
    retry: () => current.current ? connect(current.current) : navigate(address) };
};