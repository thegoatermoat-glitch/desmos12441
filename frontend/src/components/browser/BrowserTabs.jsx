import { ChevronDown, Globe2, Plus, X } from 'lucide-react';
import { useEffect } from 'react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';

export const BrowserTabs = ({ tabs, activeId, activate, addTab, closeTab }) => {
  useEffect(() => { document.getElementById(`web-tab-${activeId}`)?.scrollIntoView({ block: 'nearest', inline: 'nearest' }); }, [activeId]);
  const move = (event, index) => {
    let target;
    if (event.key === 'ArrowRight') target = (index + 1) % tabs.length;
    else if (event.key === 'ArrowLeft') target = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === 'Home') target = 0;
    else if (event.key === 'End') target = tabs.length - 1;
    else return;
    event.preventDefault(); activate(tabs[target].id);
    document.getElementById(`web-tab-${tabs[target].id}`)?.focus();
  };
  return <div className="web-tabs-row" data-testid="browser-tabs">
    <div className="web-tabs" role="tablist" aria-label="Web tabs" data-testid="browser-tab-list">
      {tabs.map((tab, index) => <div key={tab.id} className={`web-tab ${tab.id === activeId ? 'selected' : ''}`}>
        <button role="tab" id={`web-tab-${tab.id}`} aria-controls={`web-panel-${tab.id}`} aria-selected={tab.id === activeId} tabIndex={tab.id === activeId ? 0 : -1}
          data-testid={`browser-tab-${tab.id}`} title={tab.url || 'New tab'} onClick={() => activate(tab.id)} onKeyDown={event => move(event, index)}>
          <Globe2 size={13} /><span data-testid={`browser-tab-title-${tab.id}`}>{tab.title}</span>
        </button>
        <button className="web-tab-close" title={`Close ${tab.title}`} aria-label={`Close ${tab.title}`} tabIndex={tab.id === activeId ? 0 : -1}
          data-testid={`browser-close-tab-${tab.id}`} onClick={() => closeTab(tab.id)}><X size={13} /></button>
      </div>)}
    </div>
    <button className="icon-button" title="New tab" aria-label="New tab" data-testid="browser-new-tab" onClick={() => addTab()}><Plus size={18} /></button>
    <DropdownMenu><DropdownMenuTrigger asChild>
      <button className="icon-button tab-menu-trigger" title="All tabs" aria-label="All tabs" data-testid="browser-tab-manager"><span data-testid="browser-tab-count">{tabs.length}</span><ChevronDown size={13} /></button>
    </DropdownMenuTrigger><DropdownMenuContent align="end" className="web-tab-menu" data-testid="browser-tab-menu">
      {tabs.map(tab => <DropdownMenuItem key={tab.id} data-testid={`browser-tab-menu-${tab.id}`} onSelect={() => activate(tab.id)}>
        <Globe2 /><span className="tab-menu-label">{tab.title}</span>{tab.id === activeId && <span className="tab-current-marker" data-testid={`browser-current-tab-${tab.id}`}>Current</span>}
      </DropdownMenuItem>)}
      <DropdownMenuItem data-testid="browser-tab-menu-new" onSelect={() => addTab()}><Plus />New tab</DropdownMenuItem>
    </DropdownMenuContent></DropdownMenu>
  </div>;
};