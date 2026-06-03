import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function ArticleDrawer({ articleId, onClose }) {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const { isLoggedIn } = useAuth();

  // AI Chat state (article-specific)
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSessionId, setChatSessionId] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (!articleId) {
      setArticle(null);
      setMessages([]);
      setChatSessionId(null);
      return;
    }

    setLoading(true);
    setMessages([]);
    setChatSessionId(null);

    api.getArticle(articleId)
      .then((data) => {
        setArticle(data);
        // Auto-add to history
        api.addHistory(articleId).catch(() => {});
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [articleId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!articleId) return null;

  const handleExportPDF = () => {
    const win = window.open('', '_blank');
    win.document.write(`
      <html><head><meta charset="utf-8"><title>${article.title}</title>
      <style>
        body { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; padding: 40px; max-width: 700px; margin: 0 auto; color: #333; }
        h1 { font-size: 22px; margin-bottom: 8px; }
        .meta { color: #888; font-size: 13px; margin-bottom: 16px; }
        h3 { font-size: 15px; margin: 16px 0 8px; color: #555; }
        p { font-size: 14px; line-height: 1.8; }
        .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #999; text-align: center; }
      </style></head><body>
      <h1>${escapeHtml(article.title)}</h1>
      <div class="meta">${escapeHtml(article.source_name)} · ${article.published_at?.slice(0,10) || ''} · AI Industry Digest</div>
      ${article.url ? `<div style="font-size:12px;color:#6366f1;margin-bottom:16px">原文: ${escapeHtml(article.url)}</div>` : ''}
      <h3>AI 摘要</h3>
      <p>${escapeHtml(article.summary || '暂无摘要')}</p>
      ${article.raw_content ? `<h3>原文概要</h3><p>${escapeHtml(article.raw_content.slice(0,3000))}</p>` : ''}
      <div class="footer">由 AI Industry Digest 自动生成</div>
      </body></html>
    `);
    win.document.close();
    win.print();
  };

  const handleFeedback = async (type) => {
    setFeedback(type);
    try {
      await api.submitFeedback(article.id, type);
    } catch {
      // ignore
    }
  };

  const handleBookmark = async () => {
    if (!isLoggedIn) return;
    try {
      if (bookmarked) {
        // Can't remove without bookmark ID - simplified
        setBookmarked(false);
      } else {
        await api.addBookmark(article.id);
        setBookmarked(true);
      }
    } catch {
      // ignore
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMsg = chatInput.trim();
    setChatInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);

    try {
      const res = await api.chat(userMsg, article.id, chatSessionId);
      setChatSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `❌ ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/40 z-40 transition-opacity lg:hidden"
        style={{ display: articleId ? 'block' : 'none' }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div className={`
        fixed top-0 right-0 h-full w-full sm:w-[480px] lg:w-[520px]
        bg-bg-surface border-l border-border-primary shadow-2xl
        z-50 transform transition-transform duration-300
        ${articleId ? 'translate-x-0' : 'translate-x-full'}
        flex flex-col
      `}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-primary">
          <span className="font-heading font-semibold text-sm text-text-secondary">文章详情</span>
          <button onClick={onClose} className="p-1 text-text-tertiary hover:text-text-primary transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex-1 flex items-center justify-center text-text-tertiary text-sm">加载中...</div>
        ) : article ? (
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 pb-0">
              <h2 className="font-heading font-bold text-lg text-text-primary leading-relaxed mb-3">
                {article.title}
              </h2>
              <div className="flex items-center gap-3 text-sm text-text-secondary mb-4">
                <span>{article.source_name}</span>
                <span>·</span>
                <span>{article.published_at?.slice(0, 10) || ''}</span>
              </div>

              {/* Tags */}
              {article.tags?.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {article.tags.map((t) => (
                    <span key={t} className="px-2.5 py-0.5 bg-accent/10 text-accent text-xs rounded-full border border-accent/20">
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex items-center gap-3 mb-6 pb-6 border-b border-border-primary">
                <button onClick={handleExportPDF} className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary hover:border-accent/50 transition-all">
                  📥 PDF
                </button>
                <button onClick={() => handleFeedback('thumbs_up')} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs border transition-all ${feedback === 'thumbs_up' ? 'bg-accent/10 border-accent/30 text-accent' : 'bg-bg-raised border-border-primary text-text-secondary hover:text-text-primary'}`}>
                  👍 有用
                </button>
                <button onClick={() => handleFeedback('thumbs_down')} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs border transition-all ${feedback === 'thumbs_down' ? 'bg-error/10 border-error/30 text-error' : 'bg-bg-raised border-border-primary text-text-secondary hover:text-text-primary'}`}>
                  👎 没用
                </button>
                <button onClick={handleBookmark} className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs border transition-all ${bookmarked ? 'bg-accent/10 border-accent/30 text-accent' : 'bg-bg-raised border-border-primary text-text-secondary hover:text-text-primary'}`}>
                  {bookmarked ? '⭐ 已收藏' : '☆ 收藏'}
                </button>
                {article.url && (
                  <a href={article.url} target="_blank" rel="noreferrer" className="ml-auto flex items-center gap-1 px-3 py-1.5 bg-accent/10 text-accent text-xs rounded-lg hover:bg-accent/20 transition-all">
                    原文 ↗
                  </a>
                )}
              </div>
            </div>

            {/* Content area: AI Summary + Original */}
            <div className="px-6 pb-6">
              {/* AI Summary */}
              <div className="mb-6">
                <h3 className="font-heading font-semibold text-sm text-accent mb-3 flex items-center gap-2">
                  <span className="w-1 h-4 bg-accent rounded-full" />
                  AI 精读
                </h3>
                <div className="bg-bg-raised rounded-xl p-4 text-sm text-text-primary leading-relaxed">
                  {article.summary || '暂无摘要'}
                </div>
                {article.importance_reason && (
                  <div className="mt-2 text-xs text-text-tertiary italic">
                    💬 {article.importance_reason}
                  </div>
                )}
              </div>

              {/* Original content */}
              {article.raw_content && (
                <div>
                  <h3 className="font-heading font-semibold text-sm text-text-secondary mb-3 flex items-center gap-2">
                    <span className="w-1 h-4 bg-text-tertiary rounded-full" />
                    原文概要
                  </h3>
                  <div className="bg-bg-base rounded-xl p-4 text-sm text-text-secondary leading-relaxed max-h-60 overflow-y-auto">
                    {article.raw_content.slice(0, 3000)}
                    {(article.raw_content?.length || 0) > 3000 && (
                      <span className="text-text-tertiary"> ...</span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* AI Chat */}
            <div className="border-t border-border-primary">
              <div className="px-6 py-4">
                <h3 className="font-heading font-semibold text-xs text-text-secondary mb-3 uppercase tracking-wider">
                  对话 AI · 深入分析这篇文章
                </h3>
                <div className="space-y-3 mb-3 max-h-48 overflow-y-auto">
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] px-3.5 py-2 rounded-xl text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-accent text-white'
                          : 'bg-bg-raised text-text-primary'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="flex justify-start">
                      <div className="bg-bg-raised rounded-xl px-4 py-3 flex gap-1">
                        <span className="w-1.5 h-1.5 bg-text-tertiary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1.5 h-1.5 bg-text-tertiary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1.5 h-1.5 bg-text-tertiary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
                <form onSubmit={handleChat} className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="问关于这篇文章的问题..."
                    className="flex-1 px-3 py-2 bg-bg-base border border-border-primary rounded-lg text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30"
                  />
                  <button
                    type="submit"
                    disabled={chatLoading || !chatInput.trim()}
                    className="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-subtle disabled:opacity-40 transition-all"
                  >
                    发送
                  </button>
                </form>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-text-tertiary text-sm">加载失败</div>
        )}
      </div>
    </>
  );
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
