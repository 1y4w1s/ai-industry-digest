import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

export default function AIRecommendPanel({ keyword }) {
  const [recommendations, setRecommendations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (keyword) {
      fetchRecommendations();
    }
  }, [keyword]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await api.chat(`基于关键词 "${keyword}" 推荐一些相关的 AI 行业文章`, null, null);
      setRecommendations([]);
      setMessages([{ role: 'assistant', content: res.reply }]);
      setSessionId(res.session_id);
    } catch {
      setMessages([{ role: 'assistant', content: '获取推荐失败，请稍后重试' }]);
    } finally {
      setLoading(false);
    }
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

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg-white)', borderRadius: '8px', border: '1px solid var(--color-border-light)' }}>
      <div className="px-4 py-3 border-b border-[var(--color-border-light)]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px]" style={{ background: 'var(--color-text-title)', color: 'white' }}>
            AI
          </div>
          <span style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--color-text-title)' }}>智能推荐</span>
        </div>
        {keyword && (
          <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)', marginTop: '2px' }}>
            基于 "{keyword}" 的推荐
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading && (
          <div className="flex justify-center py-8">
            <div className="flex gap-1.5">
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        
        {!loading && messages.length === 0 && (
          <div className="py-4">
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
              问我关于 AI 行业的问题，或者获取个性化推荐
            </p>
            <div className="space-y-2">
              {['今天有什么重要新闻？', 'AI 融资情况如何？', '推荐热门文章'].map((q) => (
                <button
                  key={q}
                  onClick={() => {
                    setInput(q);
                    setTimeout(() => inputRef.current?.focus(), 100);
                  }}
                  className="w-full text-left px-3 py-2 rounded text-xs transition-all"
                  style={{ background: 'var(--color-bg-off)', border: '1px solid var(--color-border-light)', color: 'var(--color-text-muted)' }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[90%] px-3 py-2 rounded text-xs leading-relaxed ${msg.role === 'user' ? 'text-white' : ''}`}
              style={msg.role === 'user' ? { background: 'var(--color-text-title)' } : { background: 'var(--color-bg-hover)', color: 'var(--color-text-body)' }}>
              {msg.content}
            </div>
          </div>
        ))}
        
        {loading && messages.length > 0 && (
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

      <form onSubmit={handleSubmit} className="p-3 border-t border-[var(--color-border-light)]">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-3 py-2 text-xs rounded"
            style={{ background: 'var(--color-bg-off)', border: '1px solid var(--color-border-light)', color: 'var(--color-text-body)', outline: 'none' }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 text-xs rounded transition-all disabled:opacity-50"
            style={{ background: 'var(--color-text-title)', color: 'white' }}
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
