import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

export default function ArticleReader({ articleId, onBack }) {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [iframeError, setIframeError] = useState(false);

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
    setIframeError(false);

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

  const iframeUrl = article?.url;

  return (
    <div className="h-full flex flex-col animate-fade-in">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border-subtle bg-bg-surface flex-shrink-0">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary bg-bg-raised border border-border-primary rounded-lg transition-all"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回列表
        </button>
        <span className="text-sm font-medium text-text-primary truncate flex-1">
          {loading ? '加载中...' : article?.title}
        </span>
        {article?.source_name && (
          <span className="text-xs text-text-tertiary flex-shrink-0">{article.source_name}</span>
        )}
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-text-tertiary text-sm">加载中...</div>
      ) : article ? (
        <div className="flex-1 flex overflow-hidden">
          {/* ── Left: Original Article ─────────── */}
          <div className="flex-1 min-w-0 border-r border-border-subtle bg-white">
            {iframeUrl && !iframeError ? (
              <iframe
                src={iframeUrl}
                className="w-full h-full"
                title="原文"
                onError={() => setIframeError(true)}
                sandbox="allow-scripts allow-same-origin allow-forms"
              />
            ) : (
              <div className="p-8 overflow-y-auto h-full">
                <h2 className="font-heading text-xl font-bold text-gray-900 mb-4">{article.title}</h2>
                <div className="flex items-center gap-3 text-sm text-gray-500 mb-6">
                  <span>{article.source_name}</span>
                  <span>·</span>
                  <span>{article.published_at?.slice(0, 10)}</span>
                  {article.url && (
                    <a href={article.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline ml-2">
                      在新窗口打开 →
                    </a>
                  )}
                </div>
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {article.raw_content?.slice(0, 10000) || '暂无原文内容'}
                </div>
              </div>
            )}
          </div>

          {/* ── Right: AI Summary + Chat ─────────── */}
          <div className="w-[400px] xl:w-[480px] flex-shrink-0 flex flex-col bg-bg-surface overflow-y-auto">
            {/* AI Summary */}
            <div className="p-5 border-b border-border-subtle">
              <h3 className="font-heading font-semibold text-xs text-accent uppercase tracking-wider mb-3 flex items-center gap-2">
                <span className="w-1 h-4 bg-accent rounded-full" />
                AI 精读
              </h3>
              <div className="bg-bg-raised rounded-xl p-4 text-sm text-text-primary leading-relaxed">
                {article.summary || '暂无摘要'}
              </div>
              {article.importance_reason && (
                <div className="mt-2 text-xs text-text-tertiary italic">💬 {article.importance_reason}</div>
              )}
              {article.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {article.tags.map((t) => (
                    <span key={t} className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full border border-accent/20">{t}</span>
                  ))}
                </div>
              )}
            </div>

            {/* AI Chat */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="p-5 pb-2">
                <h3 className="font-heading font-semibold text-xs text-text-secondary uppercase tracking-wider flex items-center gap-2">
                  <span className="w-1 h-4 bg-text-tertiary rounded-full" />
                  深入对话
                </h3>
              </div>
              <div className="flex-1 overflow-y-auto px-5 pb-2 space-y-3">
                {messages.length === 0 && (
                  <div className="text-center text-text-tertiary text-xs py-6">
                    <p className="mb-3">问关于这篇文章的问题</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {['总结核心观点', '有哪些技术细节？', '有什么争议？', '同类产品对比'].map((q) => (
                        <button
                          key={q}
                          onClick={() => { setChatInput(q); setTimeout(() => chatInputRef.current?.focus(), 100); }}
                          className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary hover:border-accent/30 transition-all"
                        >{q}</button>
                      ))}
                    </div>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] px-3.5 py-2.5 rounded-xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-accent text-white' : 'bg-bg-raised text-text-primary'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
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
              <div className="p-4 border-t border-border-subtle">
                <form onSubmit={handleChat} className="flex gap-2">
                  <input
                    ref={chatInputRef}
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="输入问题..."
                    className="flex-1 px-3 py-2 bg-bg-base border border-border-primary rounded-xl text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all"
                  />
                  <button
                    type="submit"
                    disabled={chatLoading || !chatInput.trim()}
                    className="px-4 py-2 bg-accent text-white text-sm rounded-xl hover:bg-accent-subtle disabled:opacity-40 transition-all"
                  >
                    发送
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-text-tertiary text-sm">加载失败</div>
      )}
    </div>
  );
}
