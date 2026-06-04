import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

export default function ArticleReader({ articleId, onBack }) {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
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
    api.getArticle(articleId).then((data) => {
      setArticle(data);
      api.addHistory(articleId).catch(() => {});
    }).catch(() => {}).finally(() => setLoading(false));
  }, [articleId]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

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
    } finally { setChatLoading(false); }
  };

  const stripHtml = (html) => {
    if (!html) return '';
    return html.replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>/gi, '\n\n').replace(/<\/div>/gi, '\n').replace(/<\/li>/gi, '\n')
      .replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\n{3,}/g, '\n\n').trim();
  };

  return (
    <div className="h-full flex flex-col animate-fade-in" style={{ background: '#FBFCFD' }}>
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 lg:px-5 py-2.5 flex-shrink-0" style={{ borderBottom: '1px solid #E8EAED', background: '#fff' }}>
        <button onClick={onBack} className="flex items-center gap-1 px-2.5 py-1 text-xs rounded transition-all" style={{ background: '#F0F1F2', color: '#686C72' }}>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回
        </button>
        <span className="text-sm font-medium truncate flex-1" style={{ color: '#1A1C1E' }}>
          {loading ? '加载中...' : article?.title}
        </span>
        <span className="text-xs flex-shrink-0" style={{ color: '#8C9096' }}>{article?.source_name}</span>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-sm" style={{ color: '#8C9096' }}>加载中...</div>
      ) : article ? (
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Original */}
          <div className="flex-1 min-w-0 overflow-y-auto" style={{ borderRight: '1px solid #E8EAED', background: '#fff' }}>
            <div className="p-5 lg:p-8 max-w-3xl mx-auto">
              <h2 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '22px', fontWeight: 700, color: '#1A1C1E', lineHeight: 1.35, marginBottom: '12px' }}>
                {article.title}
              </h2>
              <div className="flex items-center gap-3 mb-6" style={{ color: '#686C72', fontSize: '13px' }}>
                <span>{article.source_name}</span><span>·</span><span>{article.published_at?.slice(0, 10)}</span>
                {article.url && (
                  <a href={article.url} target="_blank" rel="noreferrer" className="ml-auto text-xs" style={{ color: '#2864A8' }}>在新窗口阅读 ↗</a>
                )}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: '#2C2E32', lineHeight: '1.8', fontSize: '15px' }}>
                {stripHtml(article.raw_content) || '暂无原文内容'}
              </div>
            </div>
          </div>

          {/* Right: AI */}
          <div className="w-[380px] xl:w-[420px] flex-shrink-0 flex flex-col" style={{ background: '#F6F7F8' }}>
            <div className="flex-[3] min-h-0 overflow-y-auto p-5" style={{ borderBottom: '1px solid #E8EAED' }}>
              <h3 className="font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: '#686C72' }}>AI 精读</h3>
              <div className="text-sm leading-relaxed" style={{ color: '#2C2E32', background: '#fff', padding: '14px', borderRadius: '4px' }}>
                {article.summary || '暂无摘要'}
              </div>
              {article.importance_reason && <div className="mt-2 text-xs italic" style={{ color: '#8C9096' }}>{article.importance_reason}</div>}
              {article.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {article.tags.map((t) => (
                    <span key={t} className="px-2 py-0.5 text-xs rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{t}</span>
                  ))}
                </div>
              )}
            </div>
            <div className="flex-[2] flex flex-col min-h-0">
              <div className="px-5 pt-3 pb-1">
                <h3 className="font-semibold text-xs uppercase tracking-wider" style={{ color: '#8C9096' }}>深入对话</h3>
              </div>
              <div className="flex-1 overflow-y-auto px-5 pb-2 space-y-2.5">
                {messages.length === 0 && (
                  <div className="text-center py-4">
                    <p className="text-xs mb-2" style={{ color: '#8C9096' }}>问关于这篇文章的问题</p>
                    <div className="flex flex-wrap gap-1.5 justify-center">
                      {['总结核心观点', '有哪些技术细节？', '有什么争议？'].map((q) => (
                        <button key={q} onClick={() => { setChatInput(q); setTimeout(() => chatInputRef.current?.focus(), 100); }}
                          className="px-2.5 py-1 text-[10px] rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{q}</button>
                      ))}
                    </div>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] px-3 py-2 text-xs leading-relaxed rounded ${msg.role === 'user' ? 'text-white' : ''}`}
                      style={msg.role === 'user' ? { background: '#1A1C1E' } : { background: '#fff', color: '#2C2E32' }}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="px-3 py-2 rounded flex gap-1" style={{ background: '#fff' }}>
                      <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              <div className="p-4" style={{ borderTop: '1px solid #E8EAED' }}>
                <form onSubmit={handleChat} className="flex gap-2">
                  <input ref={chatInputRef} type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)}
                    placeholder="输入问题..." className="flex-1 px-2.5 py-1.5 text-xs rounded" style={{ background: '#fff', border: '1px solid #E8EAED', color: '#2C2E32' }} />
                  <button type="submit" disabled={chatLoading || !chatInput.trim()}
                    className="px-3 py-1.5 text-xs rounded disabled:opacity-40" style={{ background: '#1A1C1E', color: '#fff' }}>
                    发送
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-sm" style={{ color: '#8C9096' }}>加载失败</div>
      )}
    </div>
  );
}
