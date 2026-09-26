import { Link, useLocation } from 'react-router-dom';
import { ArrowLeft, Calculator, Library, Globe2, NotebookPen } from 'lucide-react';

export const Header = () => {
  const { pathname } = useLocation();
  const home = pathname === '/' || pathname === '/testing/kentucky/scientific';
  return <header className="site-header" data-testid="site-header">
    <Link to="/notes" className="brand" title="Notes" data-testid="desmos-logo-link"><img src="/assets/desmos-logo.png" alt="desmos" data-testid="desmos-logo-image" /></Link>
    <span className="header-divider" />
    <Link to="/web" className="header-label" data-testid="scientific-calculator-link">Scientific Calculator</Link>
    <span className="header-divider" />
    <Link to="/library" className="header-label" data-testid="kentucky-version-link">Kentucky Version</Link>
    {!home && <Link to="/" className="return-calculator" data-testid="return-calculator-link"><ArrowLeft size={16} /><span>Calculator</span></Link>}
  </header>;
};

export const CompanionNav = () => {
  const { pathname } = useLocation();
  return <nav className="companion-nav" aria-label="Companion pages" data-testid="companion-nav">{[
    ['/library', 'Library', Library], ['/web', 'Web', Globe2], ['/notes', 'Notes', NotebookPen], ['/', 'Calculator', Calculator],
  ].map(([path, label, Icon]) => <Link key={path} to={path} className={pathname.startsWith(path) && path !== '/' ? 'active' : ''} data-testid={`nav-${path === '/' ? 'calculator' : path.slice(1)}`}><Icon size={16} />{label}</Link>)}</nav>;
};