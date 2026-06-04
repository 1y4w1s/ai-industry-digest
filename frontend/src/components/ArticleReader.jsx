import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

export default function ArticleReader({ articleId, onBack }) {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [bookmarkId, setBookmarkId] = useState(null);
  const chatEndRef = useRef(null);
  const chatInputRef = useRef(null);

  const isBookmarked = !!bookmarkId;

  useEffect(() => {
    if (!articleId) return;
    setLoading(true);
    setMessages([]);
    setSessionId(null);
    setBookmarkId(null);
    api.getArticle(articleId).then((data) => {
      setArticle(data);
      api.addHistory(articleId).catch(() => {});
      // Check if article is bookmarked
      api.getBookmarks(1).then((bks) => {
        const found = (bks.items || []).find((b) => b.article_id === articleId);
        if (found) setBookmarkId(found.id);
      }).catch(() => {});
    }).catch(() => {}).finally(() => setLoading(false));
  }, [articleId]);

  const toggleBookmark = async () => {
    if (isBookmarked) {
      try {
        await api.removeBookmark(bookmarkId);
        setBookmarkId(null);
      } catch {}
    } else {
      try {
        await api.addBookmark(articleId);
        // Refetch to get the new bookmark id
        const bks = await api.getBookmarks(1);
        const found = (bks.items || []).find((b) => b.article_id === articleId);
        if (found) setBookmarkId(found.id);
      } catch {}
    }
  };

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
      <div className="flex items-center gap-3 px-4 lg:px-5 py-2.5 flex-shrink-0 no-print" style={{ borderBottom: '1px solid #E8EAED', background: '#FFFFFF' }}>
        <button onClick={onBack}
          style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>
          ← 返回
        </button>
        <span className="text-sm font-medium truncate flex-1" style={{ color: '#1A1C1E' }}>
          {loading ? '加载中...' : article?.title}
        </span>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="flex gap-1.5 justify-center mb-3">
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
            </div>
            <span style={{ fontSize: '13px', color: '#686C72' }}>加载中...</span>
          </div>
        </div>
      ) : article ? (
        <div className="flex-1 flex overflow-hidden">
          {/* Left: AI精读 + Original */}
          <div className="flex-1 min-w-0 overflow-y-auto" style={{ borderRight: '1px solid #E8EAED', background: '#FBFCFD' }}>
            <div className="p-5 lg:p-8 max-w-3xl mx-auto">
              {/* AI 精读 — moved from right panel to here */}
              {article.summary && (
                <div className="no-print" style={{ background: '#F6F7F8', borderRadius: '4px', padding: '16px', marginBottom: '24px' }}>
                  <h3 className="font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: '#8C9096' }}>AI 精读</h3>
                  <div className="text-sm leading-relaxed" style={{ color: '#2C2E32' }}>
                    {article.summary}
                  </div>
                  {article.importance_reason && (
                    <div className="mt-2 text-xs italic" style={{ color: '#8C9096' }}>{article.importance_reason}</div>
                  )}
                  {article.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {article.tags.map((t) => (
                        <span key={t} className="px-2 py-0.5 text-xs rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <h2 className="print-only" style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '22px', fontWeight: 700, color: '#1A1C1E', lineHeight: 1.35, marginBottom: '12px' }}>
                {article.title}
              </h2>
              <div className="flex items-center gap-3 mb-6" style={{ color: '#686C72', fontSize: '13px' }}>
                <span className="print-only">{article.source_name}</span><span className="print-only">·</span><span className="print-only">{article.published_at?.slice(0, 10)}</span>
                <div className="ml-auto flex items-center gap-3 no-print">
                  <button onClick={toggleBookmark} title={isBookmarked ? '取消收藏' : '收藏'}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: isBookmarked ? '#C8960A' : '#8C9096', transition: 'color 0.15s' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill={isBookmarked ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                    <span>{isBookmarked ? '已收藏' : '收藏'}</span>
                  </button>
                  {article.url && (
                    <a href={article.url} target="_blank" rel="noreferrer" style={{ color: '#2864A8' }}>在新窗口阅读 ↗</a>
                  )}
                </div>
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: '#2C2E32', lineHeight: '1.8', fontSize: '15px' }}>
                {stripHtml(article.raw_content) || '暂无原文内容'}
              </div>

              {/* PDF export */}
              <div className="mt-8 pt-6 text-center no-print" style={{ borderTop: '1px solid #E8EAED' }}>
                <button onClick={() => window.print()}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '12px', color: '#686C72', background: 'transparent', border: '1px solid #D8DCE0', borderRadius: '4px', cursor: 'pointer', transition: 'all 0.15s' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6 9V2h12v7" />
                    <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2" />
                    <path d="M6 14h12v8H6z" />
                    <circle cx="18" cy="11.5" r="1" />
                  </svg>
                  导出 PDF
                </button>
              </div>
            </div>
          </div>

          {/* Right: only 深入对话 */}
          <div className="w-[380px] xl:w-[420px] flex-shrink-0 flex flex-col no-print" style={{ background: '#F6F7F8' }}>
            <div className="flex flex-col flex-1 min-h-0">
              <div className="px-5 pt-4 pb-1">
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
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: '#F0F1F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8C9096" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <p style={{ fontSize: '14px', color: '#1A1C1E', marginBottom: '8px' }}>文章加载失败</p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => window.location.reload()} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}>
                重试
              </button>
              <button onClick={onBack} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}>
                返回
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
