import { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import { renderMd } from '../utils/markdown';

export default function AIChatBubble({ visible = true }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const dragRef = useRef({ startX: 0, startY: 0, posX: window.innerWidth - 72, posY: window.innerHeight - 100, dragging: false });
  const [btnStyle, setBtnStyle] = useState({ right: 24, bottom: 24 });

  useEffect(() => {
    if (!visible) setOpen(false);
  }, [visible]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggle = () => {
    setOpen(!open);
    if (!open) setTimeout(() => inputRef.current?.focus(), 300);
  };

  // 拖拽控制
  const handleMouseDown = (e) => {
    dragRef.current.dragging = true;
    dragRef.current.startX = e.clientX - btnStyle.right;
    dragRef.current.startY = e.clientY - btnStyle.bottom;
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e) => {
    if (!dragRef.current.dragging) return;
    const newRight = e.clientX - dragRef.current.startX;
    const newBottom = e.clientY - dragRef.current.startY;
    const maxRight = window.innerWidth - 60;
    const maxBottom = window.innerHeight - 60;
    setBtnStyle({
      right: Math.max(8, Math.min(maxRight, newRight)),
      bottom: Math.max(8, Math.min(maxBottom, newBottom)),
    });
  };

  const handleMouseUp = () => {
    dragRef.current.dragging = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const res = await api.chat(msg, null, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `❌ ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  if (!visible) return null;

  return (
    <>
      {/* 按钮 — 弹窗打开时隐藏 */}
      <button
        onClick={toggle}
        onMouseDown={handleMouseDown}
        style={{
          position: 'fixed', zIndex: 50,
          right: btnStyle.right, bottom: btnStyle.bottom,
          width: 42, height: 42,
          display: open ? 'none' : 'flex',
          alignItems: 'center', justifyContent: 'center',
          background: 'var(--color-text-title)',
          border: 'none', borderRadius: '50%',
          color: 'var(--color-bg-white)',
          cursor: 'grab',
          transition: 'transform 0.15s',
          boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
        }}
        className="hover:scale-110 select-none"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
        </svg>
      </button>

      {/* 弹窗 — 位置跟随按钮 */}
      <div
        className={`fixed z-50 w-[340px] max-w-[calc(100vw-32px)] flex flex-col transition-all duration-250 origin-bottom-right ${open ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}
        style={{
          right: Math.max(8, btnStyle.right - 298),
          bottom: btnStyle.bottom + 56,
          background: 'var(--color-bg-white)',
          border: '1px solid var(--color-border)',
          borderRadius: '6px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
        }}
      >
        <div className="flex items-center justify-between px-4 py-2.5" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
          <span className="text-xs font-semibold" style={{ color: 'var(--color-text-title)' }}>AI 助手</span>
          <button onClick={() => { setMessages([]); setSessionId(null); }} style={{ fontSize: 'var(--fs-xs)', color: 'var(--color-text-label)' }}>清空</button>
        </div>

        <div className="overflow-y-auto p-3 space-y-2 min-h-[140px] max-h-[320px]">
          {messages.length === 0 && (
            <div className="text-center py-4">
              <p className="text-xs mb-2" style={{ color: 'var(--color-text-label)' }}>问我关于 AI 行业的问题</p>
              <div className="flex flex-wrap gap-1.5 justify-center">
                {['今天有什么大新闻？', 'AI 融资情况？', '推荐好文章'].map((q) => (
                  <button key={q} onClick={() => { setInput(q); setTimeout(() => inputRef.current?.focus(), 100); }}
                    className="px-2.5 py-1 text-[10px] rounded transition-all"
                    style={{ background: 'var(--color-bg-hover)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border-light)' }}>{q}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] px-3 py-2 rounded text-xs leading-relaxed ${msg.role === 'user' ? 'text-white' : ''}`}
                style={msg.role === 'user' ? { background: 'var(--color-text-title)' } : { background: 'var(--color-bg-hover)', color: 'var(--color-text-body)' }}>
                <span dangerouslySetInnerHTML={{ __html: renderMd(msg.content) }} />
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="px-3 py-2 rounded flex gap-1" style={{ background: 'var(--color-bg-hover)' }}>
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-2 p-3" style={{ borderTop: '1px solid var(--color-border-light)' }}>
          <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-2.5 py-1.5 text-xs rounded transition-all"
            style={{ background: 'var(--color-bg-hover)', border: '1px solid var(--color-border-light)', color: 'var(--color-text-body)' }} />
          <button type="submit" disabled={loading || !input.trim()}
            className="px-3 py-1.5 text-xs rounded disabled:opacity-40 transition-all"
            style={{ background: 'var(--color-text-title)', color: 'var(--color-bg-white)' }}>
            发送
          </button>
        </form>
      </div>
    </>
  );
}
