import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Header } from './components/Header';
import { LeaveConfirmation } from './components/LeaveConfirmation';
import './App.css';
import './companion.css';

const Games = lazy(() => import('./pages/Games'));
const Calculator = lazy(() => import('./pages/Calculator'));
const Browser = lazy(() => import('./pages/Browser'));
const Chat = lazy(() => import('./pages/Chat'));

function Shell() {
  return <><Header /><Suspense fallback={<div className="page-loading" data-testid="page-loading">Loading…</div>}><Outlet /></Suspense><LeaveConfirmation /><Toaster position="bottom-right" /></>;
}
const router = createBrowserRouter([{ element: <Shell />, children: [
  { path: '/', element: <Calculator /> },
  { path: '/testing/kentucky/scientific', element: <Calculator /> },
  { path: '/games', element: <Games /> },
  { path: '/games/:gameId', element: <Games /> },
  { path: '/library', element: <Games /> },
  { path: '/library/:gameId', element: <Games /> },
  { path: '/browser', element: <Browser /> },
  { path: '/web', element: <Browser /> },
  { path: '/ai', element: <Chat /> },
  { path: '/notes', element: <Chat /> },
  { path: '*', element: <Calculator /> },
]}]);
export default function App() { return <RouterProvider router={router} />; }