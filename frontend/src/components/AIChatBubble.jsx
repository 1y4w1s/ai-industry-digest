import { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';

export default function AIChatBubble() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const toggle = () => {
    setOpen(!open);
    if (!open) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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

  return (
    <>
      {/* Bubble button */}
      <button
        onClick={toggle}
        className="fixed bottom-6 right-6 z-50 w-12 h-12 bg-accent hover:bg-accent-subtle text-white rounded-full shadow-lg shadow-accent/30 flex items-center justify-center transition-all duration-200 hover:scale-110"
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

      {/* Chat window */}
      <div className={`
        fixed bottom-20 right-6 z-50 w-[360px] max-w-[calc(100vw-32px)]
        bg-bg-surface border border-border-primary rounded-2xl shadow-2xl
        flex flex-col transition-all duration-300 origin-bottom-right
        ${open ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border-primary">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center text-white text-xs font-bold">
              AI
            </div>
            <span className="font-heading font-semibold text-sm text-text-primary">AI 助手</span>
          </div>
          <button
            onClick={() => { setMessages([]); setSessionId(null); }}
            className="text-xs text-text-tertiary hover:text-text-primary transition-colors"
          >
            清空对话
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[400px]">
          {messages.length === 0 && (
            <div className="text-center text-text-tertiary text-xs py-8">
              <div className="text-2xl mb-2">🤖</div>
              <p>你好！我是 AI 助手</p>
              <p className="mt-1">可以问我关于 AI 行业的任何问题</p>
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {['今天有什么大新闻？', '最近AI融资情况？', '推荐几篇好文章'].map((q) => (
                  <button
                    key={q}
                    onClick={() => {
                      setInput(q);
                      setTimeout(() => inputRef.current?.focus(), 100);
                    }}
                    className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary hover:border-accent/30 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] px-3.5 py-2.5 rounded-xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-accent text-white'
                  : 'bg-bg-raised text-text-primary'
              }`}>
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
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-3.5 py-2 bg-bg-base border border-border-primary rounded-xl text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-2 bg-accent text-white rounded-xl hover:bg-accent-subtle disabled:opacity-40 transition-all"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </form>
      </div>
    </>
  );
}
