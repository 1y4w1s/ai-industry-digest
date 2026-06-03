import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

export default function ArticleReader({ articleId, onBack }) {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);
  const chatInputRef = useRef(null);

  useEffect(() => {
    if (!articleId) return;
    setLoading(true);
    setMessages([]);
    setSessionId(null);

    api.getArticle(articleId)
      .then((data) => {
        setArticle(data);
        api.addHistory(articleId).catch(() => {});
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [articleId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setChatLoading(true);
    try {
      const res = await api.chat(msg, article?.id, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `❌ ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Strip HTML tags for clean display, keep paragraphs
  const stripHtml = (html) => {
    if (!html) return '';
    // Replace common block tags with newlines
    let text = html
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>/gi, '\n\n')
      .replace(/<\/div>/gi, '\n')
      .replace(/<\/li>/gi, '\n')
      .replace(/<[^>]+>/g, '')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");
    // Collapse multiple newlines
    text = text.replace(/\n{3,}/g, '\n\n');
    return text.trim();
  };

  return (
    <div className="h-full flex flex-col animate-fade-in" style={{ background: '#0F1020' }}>
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 lg:px-5 py-2.5 flex-shrink-0" style={{ background: '#1A1B33', borderBottom: '1px solid #2E2F4F' }}>
        <button onClick={onBack}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-all hover:brightness-110"
          style={{ background: '#22233D', border: '1px solid #2E2F4F', color: '#9197C2' }}>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回列表
        </button>
        <span className="text-sm font-medium truncate flex-1" style={{ color: '#E2E6F9' }}>
          {loading ? '加载中...' : article?.title}
        </span>
        <span className="text-xs flex-shrink-0" style={{ color: '#6E739C' }}>{article?.source_name}</span>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-sm" style={{ color: '#6E739C' }}>加载中...</div>
      ) : article ? (
        <div className="flex-1 flex overflow-hidden">
          {/* ── Left: Original Content ─────────── */}
          <div className="flex-1 min-w-0 overflow-y-auto" style={{ borderRight: '1px solid #2E2F4F', background: '#13152A' }}>
            <div className="p-5 lg:p-8 max-w-3xl mx-auto">
              <h2 className="font-heading font-bold text-xl lg:text-2xl mb-3" style={{ color: '#E2E6F9', lineHeight: 1.4 }}>
                {article.title}
              </h2>
              <div className="flex items-center gap-3 text-sm mb-6" style={{ color: '#9197C2' }}>
                <span>{article.source_name}</span>
                <span>·</span>
                <span>{article.published_at?.slice(0, 10)}</span>
                {article.url && (
                  <a href={article.url} target="_blank" rel="noreferrer" className="ml-auto text-xs transition-all hover:brightness-110" style={{ color: '#6395FF' }}>
                    在新窗口阅读原文 ↗
                  </a>
                )}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: '#C8CCE6', lineHeight: '1.8', fontSize: '15px' }}>
                {stripHtml(article.raw_content) || '暂无原文内容'}
              </div>
            </div>
          </div>

          {/* ── Right: AI Summary + Chat ─────────── */}
          <div className="w-[400px] xl:w-[480px] flex-shrink-0 flex flex-col" style={{ background: '#1A1B33' }}>
            {/* AI Summary — 60% */}
            <div className="flex-[3] min-h-0 overflow-y-auto p-5" style={{ borderBottom: '1px solid #2E2F4F' }}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-heading font-semibold text-xs uppercase tracking-wider flex items-center gap-2" style={{ color: '#6395FF' }}>
                  <span className="w-1 h-4 rounded-full" style={{ background: '#6395FF' }} />
                  AI 精读
                </h3>
                {article.url && (
                  <a href={article.url} target="_blank" rel="noreferrer" className="text-xs transition-all hover:brightness-110" style={{ color: '#6395FF' }}>
                    原文 ↗
                  </a>
                )}
              </div>
              <div className="rounded-xl p-4 text-sm leading-relaxed" style={{ background: '#22233D', color: '#E2E6F9' }}>
                {article.summary || '暂无摘要'}
              </div>
              {article.importance_reason && (
                <div className="mt-2 text-xs italic" style={{ color: '#6E739C' }}>💬 {article.importance_reason}</div>
              )}
              {article.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {article.tags.map((t) => (
                    <span key={t} className="px-2 py-0.5 text-xs rounded-full" style={{ background: 'rgba(99,149,255,0.1)', color: '#6395FF', border: '1px solid rgba(99,149,255,0.2)' }}>{t}</span>
                  ))}
                </div>
              )}
            </div>

            {/* AI Chat — 40% */}
            <div className="flex-[2] flex flex-col min-h-0">
              <div className="px-5 pt-3 pb-1">
                <h3 className="font-heading font-semibold text-xs uppercase tracking-wider flex items-center gap-2" style={{ color: '#9197C2' }}>
                  <span className="w-1 h-4 rounded-full" style={{ background: '#9197C2' }} />
                  深入对话
                </h3>
              </div>
              <div className="flex-1 overflow-y-auto px-5 pb-2 space-y-3">
                {messages.length === 0 && (
                  <div className="text-center py-6">
                    <p className="text-xs mb-3" style={{ color: '#6E739C' }}>问关于这篇文章的问题</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {['总结核心观点', '有哪些技术细节？', '有什么争议？'].map((q) => (
                        <button key={q} onClick={() => { setChatInput(q); setTimeout(() => chatInputRef.current?.focus(), 100); }}
                          className="px-3 py-1.5 text-xs rounded-lg transition-all hover:brightness-110"
                          style={{ background: '#23243E', color: '#9197C2', border: '1px solid #2E2F4F' }}>{q}</button>
                      ))}
                    </div>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] px-3.5 py-2.5 rounded-xl text-sm leading-relaxed ${
                      msg.role === 'user' ? 'text-white' : ''
                    }`} style={msg.role === 'user' ? { background: '#6395FF' } : { background: '#22233D', color: '#E2E6F9' }}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="rounded-xl px-4 py-3 flex gap-1" style={{ background: '#22233D' }}>
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#6E739C', animationDelay: '0ms' }} />
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#6E739C', animationDelay: '150ms' }} />
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#6E739C', animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              <div className="p-4" style={{ borderTop: '1px solid #2E2F4F' }}>
                <form onSubmit={handleChat} className="flex gap-2">
                  <input ref={chatInputRef} type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)}
                    placeholder="输入问题..."
                    className="flex-1 px-3 py-2 rounded-xl text-sm transition-all"
                    style={{ background: '#16172D', border: '1px solid #2E2F4F', color: '#E2E6F9' }} />
                  <button type="submit" disabled={chatLoading || !chatInput.trim()}
                    className="px-4 py-2 rounded-xl text-sm disabled:opacity-40 transition-all hover:brightness-110"
                    style={{ background: '#6395FF', color: '#fff' }}>
                    发送
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-sm" style={{ color: '#6E739C' }}>加载失败</div>
      )}
    </div>
  );
}
