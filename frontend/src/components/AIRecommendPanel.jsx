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
    <div className="h-full flex flex-col" style={{ background: 'white', borderRadius: '8px', border: '1px solid #E8EAED' }}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#E8EAED]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px]" style={{ background: '#1A1C1E', color: 'white' }}>
            AI
          </div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#1A1C1E' }}>智能推荐</span>
        </div>
        {keyword && (
          <p style={{ fontSize: '11px', color: '#8C9096', marginTop: '2px' }}>
            基于 "{keyword}" 的推荐
          </p>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading && (
          <div className="flex justify-center py-8">
            <div className="flex gap-1.5">
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        
        {!loading && messages.length === 0 && (
          <div className="py-4">
            <p style={{ fontSize: '12px', color: '#686C72', marginBottom: '8px' }}>
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
                  className="w-full text-left px-3 py-2 rounded text-xs transition-all hover:bg-[#F0F1F2]"
                  style={{ background: '#F8F9FA', border: '1px solid #E8EAED', color: '#686C72' }}
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
              style={msg.role === 'user' ? { background: '#1A1C1E' } : { background: '#F0F1F2', color: '#2C2E32' }}>
              {msg.content}
            </div>
          </div>
        ))}
        
        {loading && messages.length > 0 && (
          <div className="flex justify-start">
            <div className="px-3 py-2 rounded flex gap-1" style={{ background: '#F0F1F2' }}>
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-[#E8EAED]">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-3 py-2 text-xs rounded"
            style={{ background: '#F8F9FA', border: '1px solid #E8EAED', color: '#2C2E32', outline: 'none' }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 text-xs rounded transition-all disabled:opacity-50"
            style={{ background: '#1A1C1E', color: 'white' }}
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
