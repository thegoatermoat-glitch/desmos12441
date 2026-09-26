import { useEffect } from 'react';

// Native tab-close/refresh warning only; internal navigation is never blocked.
export const LeaveConfirmation = () => {
  useEffect(() => {
    const beforeUnload = event => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, []);
  return null;
};