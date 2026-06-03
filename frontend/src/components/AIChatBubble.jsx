import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '../api/client';

export default function AIChatBubble({ visible = true }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [position, setPosition] = useState({ x: window.innerWidth - 80, y: window.innerHeight - 80 });
  const [dragging, setDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [showHint, setShowHint] = useState(true);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const bubbleRef = useRef(null);

  // Auto-hide hint after 5s
  useEffect(() => {
    if (!open) {
      const t = setTimeout(() => setShowHint(false), 5000);
      return () => clearTimeout(t);
    }
  }, [open]);

  // Auto-close when hidden (article reading mode)
  useEffect(() => {
    if (!visible) setOpen(false);
  }, [visible]);

  // Follow window resize
  useEffect(() => {
    const handleResize = () => {
      setPosition((prev) => ({
        x: Math.min(prev.x, window.innerWidth - 80),
        y: Math.min(prev.y, window.innerHeight - 120),
      }));
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggle = () => {
    setOpen(!open);
    setShowHint(false);
    if (!open) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  };

  // ── Dragging ───────────────
  const handleMouseDown = useCallback((e) => {
    setDragging(true);
    setDragOffset({
      x: e.clientX - bubbleRef.current.getBoundingClientRect().left,
      y: e.clientY - bubbleRef.current.getBoundingClientRect().top,
    });
    // Scale up on drag start
    if (bubbleRef.current) {
      bubbleRef.current.style.transform = 'scale(1.12)';
    }
  }, []);

  useEffect(() => {
    if (!dragging) return;
    const handleMove = (e) => {
      setPosition({
        x: Math.max(0, Math.min(e.clientX - dragOffset.x, window.innerWidth - 56)),
        y: Math.max(0, Math.min(e.clientY - dragOffset.y, window.innerHeight - 56)),
      });
    };
    const handleUp = () => {
      setDragging(false);
      // Bounce animation on drop
      if (bubbleRef.current) {
        bubbleRef.current.style.transform = 'scale(1)';
        bubbleRef.current.style.transition = 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
        setTimeout(() => {
          if (bubbleRef.current) bubbleRef.current.style.transition = '';
        }, 400);
      }
    };
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
    };
  }, [dragging, dragOffset]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);
    try {
      const res = await api.chat(userMsg, null, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `❌ ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return !visible ? null : (
    <>
      {/* Bubble */}
      <div
        ref={bubbleRef}
        style={{ left: position.x, top: position.y, cursor: dragging ? 'grabbing' : 'grab' }}
        className="fixed z-50"
        onMouseDown={handleMouseDown}
      >
        <button
          onClick={toggle}
          className="w-11 h-11 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-110 select-none"
          style={{ background: '#282848', backdropFilter: 'blur(12px)' }}
        >
          {open ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
          )}
        </button>

        {/* Hint */}
        {!open && showHint && (
          <div className="absolute right-14 top-1/2 -translate-y-1/2 bg-bg-raised border border-border-primary rounded-xl px-3.5 py-2 text-xs text-text-secondary whitespace-nowrap shadow-lg animate-fade-in">
            🤖 问我任何 AI 相关问题
            <div className="absolute right-[-6px] top-1/2 -translate-y-1/2 w-3 h-3 bg-bg-raised border-r border-t border-border-primary rotate-45" />
          </div>
        )}
      </div>

      {/* Chat window */}
      <div
        style={{
          left: Math.max(16, position.x - 300 + 56),
          top: Math.min(position.y - 420, position.y - 420),
        }}
        className={`fixed z-50 w-[340px] max-w-[calc(100vw-32px)] bg-bg-surface border border-border-primary rounded-2xl shadow-2xl flex flex-col transition-all duration-300 origin-bottom-left ${open ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border-primary">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md flex items-center justify-center text-white text-[10px] font-bold" style={{ background: '#5886FF' }}>AI</div>
            <span className="font-heading font-semibold text-sm text-text-primary">AI 助手</span>
          </div>
          <button onClick={() => { setMessages([]); setSessionId(null); }} className="text-xs text-text-tertiary hover:text-text-primary transition-colors">清空</button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5 min-h-[180px] max-h-[360px]">
          {messages.length === 0 && (
            <div className="text-center text-text-tertiary text-xs py-6">
              <div className="text-2xl mb-2">🤖</div>
              <p className="mb-3">你好！我是 AI 助手</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {['今天有什么大新闻？', '最近AI融资情况？', '推荐几篇文章'].map((q) => (
                  <button key={q} onClick={() => { setInput(q); setTimeout(() => inputRef.current?.focus(), 100); }}
                    className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary hover:border-accent/30 transition-all">{q}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] px-3.5 py-2.5 rounded-xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-accent text-white' : 'bg-bg-raised text-text-primary'}`}>
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-bg-raised rounded-xl px-4 py-3 flex gap-1">
                <span className="w-2 h-2 bg-text-tertiary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-text-tertiary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-text-tertiary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex items-center gap-2 p-3 border-t border-border-primary">
          <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-3 py-2 bg-bg-base border border-border-primary rounded-xl text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all" />
          <button type="submit" disabled={loading || !input.trim()}
            className="p-2 bg-accent text-white rounded-xl hover:bg-accent-subtle disabled:opacity-40 transition-all">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </form>
      </div>
    </>
  );
}
