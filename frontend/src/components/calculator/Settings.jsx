import { Dialog, DialogContent, DialogTitle, DialogDescription } from '../ui/dialog';
import { Switch } from '../ui/switch';

export const Settings = ({ open, setOpen, settings, setSettings }) => <Dialog open={open} onOpenChange={setOpen}>
  <DialogContent className="settings-dialog" data-testid="calculator-settings-dialog">
    <DialogTitle data-testid="calculator-settings-title">Calculator settings</DialogTitle>
    <DialogDescription data-testid="calculator-settings-description">Display preferences</DialogDescription>
    <label className="setting-row" htmlFor="large-type">Larger text<Switch id="large-type" data-testid="large-text-switch" checked={settings.large} onCheckedChange={large => setSettings({ ...settings, large })} /></label>
    <label className="setting-row" htmlFor="high-contrast">High contrast<Switch id="high-contrast" data-testid="high-contrast-switch" checked={settings.contrast} onCheckedChange={contrast => setSettings({ ...settings, contrast })} /></label>
    <p className="independent-note" data-testid="independent-notice">An independent recreation. Not affiliated with Desmos or approved for official assessments.</p>
  </DialogContent>
</Dialog>;