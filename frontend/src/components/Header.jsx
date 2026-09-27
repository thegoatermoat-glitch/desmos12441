import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Calculator, Library, Globe2, NotebookPen } from 'lucide-react';
import { useState } from 'react';
import { insideBlankWindow, openBlankWindow } from '../lib/blankWindow';

export const Header = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [launchError, setLaunchError] = useState('');
  const launch = (event, path) => {
    event.preventDefault(); setLaunchError('');
    if (insideBlankWindow()) { navigate(path); return; }
    if (!openBlankWindow(path)) setLaunchError('The new window was blocked. Allow pop-ups for this site and try again.');
  };
  const home = pathname === '/' || pathname === '/testing/kentucky/scientific';
  return <header className="site-header" data-testid="site-header">
    <Link to="/notes" onClick={event => launch(event, '/notes')} className="brand" title="Notes" data-testid="desmos-logo-link"><img src="/assets/desmos-logo.png" alt="desmos" data-testid="desmos-logo-image" /></Link>
    <span className="header-divider" />
    <Link to="/web" onClick={event => launch(event, '/web')} className="header-label" data-testid="scientific-calculator-link">Scientific Calculator</Link>
    <span className="header-divider" />
    <Link to="/library" onClick={event => launch(event, '/library')} className="header-label" data-testid="kentucky-version-link">Kentucky Version</Link>
    {!home && <Link to="/" className="return-calculator" data-testid="return-calculator-link"><ArrowLeft size={16} /><span>Calculator</span></Link>}
    {launchError && <div className="window-launch-error" role="alert" data-testid="about-blank-launch-error">{launchError}<button type="button" aria-label="Dismiss window error" data-testid="about-blank-error-dismiss" onClick={() => setLaunchError('')}>×</button></div>}
  </header>;
};

export const CompanionNav = () => {
  const { pathname } = useLocation();
  return <nav className="companion-nav" aria-label="Companion pages" data-testid="companion-nav">{[
    ['/library', 'Library', Library], ['/web', 'Web', Globe2], ['/notes', 'Notes', NotebookPen], ['/', 'Calculator', Calculator],
  ].map(([path, label, Icon]) => <Link key={path} to={path} className={pathname.startsWith(path) && path !== '/' ? 'active' : ''} data-testid={`nav-${path === '/' ? 'calculator' : path.slice(1)}`}><Icon size={16} />{label}</Link>)}</nav>;
};