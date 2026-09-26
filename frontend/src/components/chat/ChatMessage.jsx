import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Copy, Check, MessageSquare, UserRound } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import 'katex/dist/katex.min.css';

export const ChatMessage = ({ message, index }) => {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(message.content); setCopied(true); setTimeout(() => setCopied(false), 1800); } catch { toast.error('Clipboard is not available.'); }
  };
  return <article className={`chat-message ${message.role}`} data-testid={`chat-message-${index}`}>
    <div className="message-avatar">{message.role === 'user' ? <UserRound size={17} /> : <MessageSquare size={17} />}</div>
    <div className="message-body"><div className="message-author">{message.role === 'user' ? 'You' : 'Response'}</div>
      <div className="markdown-content" data-testid={`chat-message-content-${index}`}><ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]} components={{ a: ({ node, ...props }) => <a {...props} data-testid={`chat-message-link-${index}-${node.position?.start.offset}`} rel="noopener noreferrer" /> }}>{message.content}</ReactMarkdown></div>
      {message.role === 'assistant' && <button className="copy-message" title="Copy response" data-testid={`copy-message-${index}`} onClick={copy}>{copied ? <Check size={14} /> : <Copy size={14} />}{copied ? 'Copied' : 'Copy'}</button>}
    </div>
  </article>;
};