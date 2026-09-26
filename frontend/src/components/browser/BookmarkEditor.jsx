import { useState } from 'react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';

export const BookmarkEditor = ({ initial, save, cancel, remove }) => {
  const [title, setTitle] = useState(initial.title || ''), [url, setUrl] = useState(initial.url || '');
  const [error, setError] = useState('');
  const submit = event => {
    event.preventDefault(); setError('');
    try { save({ ...initial, title, url }); } catch (failure) { setError(failure.message); }
  };
  return <form className="bookmark-editor" onSubmit={submit} noValidate data-testid="bookmark-editor">
    <label htmlFor="bookmark-name">Name</label>
    <Input id="bookmark-name" data-testid="bookmark-name" value={title} onChange={event => setTitle(event.target.value)} maxLength={100} autoFocus />
    <label htmlFor="bookmark-url">Address</label>
    <Input id="bookmark-url" data-testid="bookmark-url" value={url} onChange={event => setUrl(event.target.value)} maxLength={4096} autoComplete="url" spellCheck={false} />
    {error && <div className="error-banner" role="alert" data-testid="bookmark-error">{error}</div>}
    <div className="bookmark-editor-actions">
      {initial.id && <Button type="button" variant="ghost" className="bookmark-remove-button" data-testid="bookmark-editor-remove" onClick={() => remove(initial.id)}>Remove</Button>}
      <Button type="button" variant="outline" data-testid="bookmark-cancel" onClick={cancel}>Cancel</Button>
      <Button type="submit" className="bookmark-save-button" data-testid="bookmark-save">Save</Button>
    </div>
  </form>;
};