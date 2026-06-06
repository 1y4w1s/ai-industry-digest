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

  // 气泡位置（独立）
  const [bubblePos, setBubblePos] = useState({ right: 24, bottom: 24 });
  // 弹窗位置（独立）
  const [panelPos, setPanelPos] = useState({ right: 24, bottom: 108 });

  // 拖拽状态
  const drag = useRef({ target: null, startX: 0, startY: 0, moved: false });

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

  // ── 统一拖拽（分离点击 vs 拖拽） ──
  const handleMouseDown = (e, target) => {
    drag.current = {
      target,
      startX: e.clientX,
      startY: e.clientY,
      moved: false,
    };
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e) => {
    const dx = e.clientX - drag.current.startX;
    const dy = e.clientY - drag.current.startY;
    if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
      drag.current.moved = true;
    }
    if (!drag.current.moved) return;

    if (drag.current.target === 'bubble') {
      setBubblePos((prev) => ({
        right: Math.max(8, Math.min(window.innerWidth - 60, prev.right - dx)),
        bottom: Math.max(8, Math.min(window.innerHeight - 60, prev.bottom - dy)),
      }));
      drag.current.startX = e.clientX;
      drag.current.startY = e.clientY;
    } else if (drag.current.target === 'panel') {
      setPanelPos((prev) => ({
        right: Math.max(8, Math.min(window.innerWidth - 60, prev.right - dx)),
        bottom: Math.max(8, Math.min(window.innerHeight - 60, prev.bottom - dy)),
      }));
      drag.current.startX = e.clientX;
      drag.current.startY = e.clientY;
    }
  };

  const handleMouseUp = () => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    // 如果没有移动 → 视为点击
    if (!drag.current.moved && drag.current.target === 'bubble') {
      toggle();
    }
    drag.current.moved = false;
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

  const bubbleBtnStyle = {
    position: 'fixed', zIndex: 60,
    right: bubblePos.right, bottom: bubblePos.bottom,
    width: 42, height: 42,
    display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    background: 'var(--color-text-title)',
    border: 'none', borderRadius: '50%',
    color: 'var(--color-bg-white)',
    cursor: 'grab',
    transition: 'transform 0.15s, box-shadow 0.15s',
    boxShadow: open ? '0 0 0 3px rgba(0,0,0,0.12)' : '0 2px 12px rgba(0,0,0,0.15)',
  };

  const panelStyle = {
    position: 'fixed', zIndex: 50,
    right: Math.max(8, panelPos.right),
    bottom: panelPos.bottom,
    width: 340, maxWidth: 'calc(100vw - 32px)',
    display: 'flex', flexDirection: 'column',
    background: 'var(--color-bg-white)',
    border: '1px solid var(--color-border)',
    borderRadius: '6px',
    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    opacity: open ? 1 : 0,
    pointerEvents: open ? 'auto' : 'none',
    transform: open ? 'scale(1)' : 'scale(0.95)',
    transition: 'opacity 0.2s, transform 0.2s',
    transformOrigin: 'bottom right',
  };

  return (
    <>
      {/* 气泡按钮 */}
      <button
        onMouseDown={(e) => handleMouseDown(e, 'bubble')}
        style={bubbleBtnStyle}
        className="select-none hover:scale-110"
      >
        {open ? (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        )}
      </button>

      {/* 弹窗 */}
      <div style={panelStyle}>
        {/* 标题栏 — 可拖动 + 独立关闭按钮 */}
        <div
          onMouseDown={(e) => handleMouseDown(e, 'panel')}
          className="flex items-center justify-between px-4 py-2.5 select-none"
          style={{ borderBottom: '1px solid var(--color-border-light)', cursor: 'grab' }}
        >
          <span className="text-xs font-semibold" style={{ color: 'var(--color-text-title)' }}>
            AI 助手
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => { e.stopPropagation(); setMessages([]); setSessionId(null); }}
              style={{ fontSize: 'var(--fs-xs)', color: 'var(--color-text-label)', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 6px', borderRadius: '3px' }}
              className="hover:bg-[var(--color-bg-hover)]"
            >
              清空
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setOpen(false); }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', padding: '2px 4px', borderRadius: '3px' }}
              className="hover:bg-[var(--color-bg-hover)]"
              title="关闭"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
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
              <div
                className="max-w-[85%] px-3 py-2 rounded text-xs leading-relaxed"
                style={
                  msg.role === 'user'
                    ? { background: 'var(--color-text-title)', color: 'var(--color-bg-white)' }
                    : { background: 'var(--color-bg-hover)', color: 'var(--color-text-body)' }
                }
              >
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
