import { useEffect } from 'react';

// Native tab-close/refresh warning only; internal navigation is never blocked.
export const LeaveConfirmation = () => {
  useEffect(() => {
    // A truthy legacy returnValue covers browsers predating preventDefault support.
    // Browsers still require a real user interaction and control the dialog text.
    const beforeUnload = event => { event.preventDefault(); event.returnValue = true; return true; };
    window.addEventListener('beforeunload', beforeUnload, { capture: true });
    return () => window.removeEventListener('beforeunload', beforeUnload, { capture: true });
  }, []);
  return null;
};