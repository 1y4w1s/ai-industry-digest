import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { api } from '../api/client';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { renderMd, renderArticleContent } from '../utils/markdown';
import DOMPurify from 'dompurify';
import { Cache, CACHE_TTL } from '../utils/cache';
import { useToast } from './Toast';
import ErrorBoundary from './ErrorBoundary';

/* ── TTS hook (guarded for mobile browsers without SpeechSynthesis) ───── */
function getSS() {
  return typeof window !== 'undefined' && window.speechSynthesis ? window.speechSynthesis : null;
}

function useTTS() {
  const [state, setState] = useState('idle');
  const utteranceRef = useRef(null);
  const textChunksRef = useRef([]);
  const chunkIdxRef = useRef(0);

  const stop = useCallback(() => {
    const ss = getSS();
    if (ss) ss.cancel();
    utteranceRef.current = null;
    textChunksRef.current = [];
    chunkIdxRef.current = 0;
    setState('idle');
  }, []);

  useEffect(() => {
    return () => { const ss = getSS(); if (ss) ss.cancel(); };
  }, []);

  const speak = useCallback((text) => {
    const ss = getSS();
    if (!ss || !text) return;
    ss.cancel();
    const chunks = [];
    let current = '';
    for (const char of text) {
      current += char;
      if (current.length > 150 && /[。！？\n.!?]/.test(char)) {
        chunks.push(current.trim());
        current = '';
      }
    }
    if (current.trim()) chunks.push(current.trim());
    textChunksRef.current = chunks;
    chunkIdxRef.current = 0;

    const speakChunk = (idx) => {
      if (idx >= chunks.length) { setState('idle'); return; }
      const utt = new SpeechSynthesisUtterance(chunks[idx]);
      utt.lang = 'zh-CN';
      utt.rate = 1.0;
      utt.pitch = 1.0;
      const voices = ss.getVoices();
      const zhVoice = voices.find((v) => v.lang.startsWith('zh'));
      if (zhVoice) utt.voice = zhVoice;
      utt.onend = () => { chunkIdxRef.current = idx + 1; speakChunk(idx + 1); };
      utt.onerror = () => setState('idle');
      utteranceRef.current = utt;
      ss.speak(utt);
      setState('playing');
    };

    if (ss.getVoices().length === 0) {
      ss.onvoiceschanged = () => speakChunk(0);
    } else {
      speakChunk(0);
    }
  }, []);

  const pause = useCallback(() => { const ss = getSS(); if (ss) ss.pause(); setState('paused'); }, []);
  const resume = useCallback(() => { const ss = getSS(); if (ss) ss.resume(); setState('playing'); }, []);

  const toggle = useCallback((text) => {
    if (state === 'idle') { speak(text); }
    else if (state === 'playing') { pause(); }
    else if (state === 'paused') { resume(); }
  }, [state, speak, pause, resume]);

  return { state, toggle, stop };
}

function stripHtml(html) {
  if (!html) return '';
  // Used for TTS only — get plain text without formatting
  let text = html;
  // Decode common entities first
  text = text.replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&#821[12];/g, "'")
    .replace(/&#8220;|&#8221;/g, '"').replace(/&#821[12];/g, '—').replace(/&#8230;/g, '…');
  // Strip HTML tags
  text = text.replace(/<[^>]+>/g, '');
  // Normalize whitespace
  text = text.replace(/\n{3,}/g, '\n\n').trim();
  return text;
}

/* ── SVG icons ───────────── */
const IconPlay = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>);
const IconPause = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2"><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></svg>);
const IconStop = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2"><rect x="4" y="4" width="16" height="16" rx="2" /></svg>);
const IconBookmark = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>);
const IconBookmarkFilled = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>);
const IconPDF = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9V2h12v7" /><path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2" /><path d="M6 14h12v8H6z" /><circle cx="18" cy="11.5" r="1" /></svg>);

export default function ArticleReader({ articleId, onBack }) {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [bookmarkId, setBookmarkId] = useState(null);
  const [chatCollapsed, setChatCollapsed] = useState(false);  // 移动端对话面板折叠
  const chatEndRef = useRef(null);
  const chatInputRef = useRef(null);
  const pdfContentRef = useRef(null);
  const contentScrollRef = useRef(null);  // 用于追踪滚动
  const startTimeRef = useRef(Date.now()); // 开始阅读时间
  const readPercentRef = useRef(0);        // 最新阅读百分比
  const toast = useToast();

  const isBookmarked = !!bookmarkId;
  const { state: ttsState, toggle: ttsToggle, stop: ttsStop } = useTTS();
  const articleText = useMemo(() => article ? stripHtml(article.raw_content) : '', [article]);
  const ttsSupported = typeof window !== 'undefined' && window.speechSynthesis && typeof SpeechSynthesisUtterance !== 'undefined';

  useEffect(() => {
    if (!articleId) return;
    ttsStop();
    setLoading(true);
    setMessages([]);
    setSessionId(null);
    setBookmarkId(null);
    api.getArticle(articleId).then((data) => {
      setArticle(data);
      // 延迟 2 秒写入历史，不阻塞渲染
      setTimeout(() => api.addHistory(articleId).catch(() => {}), 2000);
      // 从缓存获取 bookmarks，避免额外请求
      const cachedBks = Cache.get('bookmarks');
      if (cachedBks) {
        const found = cachedBks.find((b) => b.article_id === articleId);
        if (found) setBookmarkId(found.id);
      } else {
        api.getBookmarks(1).then((bks) => {
          const items = bks.items || [];
          Cache.set('bookmarks', items, CACHE_TTL.BOOKMARKS);
          const found = items.find((b) => b.article_id === articleId);
          if (found) setBookmarkId(found.id);
        }).catch(() => {});
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, [articleId, ttsStop]);

  // ── 阅读深度追踪 ──
  useEffect(() => {
    if (!articleId) return;
    startTimeRef.current = Date.now();
    readPercentRef.current = 0;

    const el = contentScrollRef.current;
    if (!el) return;

    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          const { scrollTop, scrollHeight, clientHeight } = el;
          const maxScroll = scrollHeight - clientHeight;
          const pct = maxScroll > 0 ? Math.min(100, Math.round((scrollTop / maxScroll) * 100)) : 100;
          readPercentRef.current = pct;
          ticking = false;
        });
        ticking = true;
      }
    };

    el.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      el.removeEventListener('scroll', onScroll);
      // 组件卸载时上报阅读深度
      const finalPct = readPercentRef.current;
      const duration = Math.round((Date.now() - startTimeRef.current) / 1000);
      if (finalPct >= 15) {
        api.addHistoryWithDepth(articleId, finalPct, duration).catch(() => {});
      }
    };
  }, [articleId]);

  const toggleBookmark = async () => {
    if (isBookmarked) {
      try { await api.removeBookmark(bookmarkId); setBookmarkId(null); Cache.remove('bookmarks'); toast('已取消收藏', 'info'); } catch {}
    } else {
      try {
        await api.addBookmark(articleId);
        Cache.remove('bookmarks'); // 缓存失效
        const bks = await api.getBookmarks(1);
        const items = bks.items || [];
        Cache.set('bookmarks', items, CACHE_TTL.BOOKMARKS);
        const found = items.find((b) => b.article_id === articleId);
        if (found) setBookmarkId(found.id);
        toast('已收藏', 'success');
      } catch {}
    }
  };

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const downloadPDF = async () => {
    if (!article) return;
    const el = pdfContentRef.current;
    if (!el) return;
    try {
      const canvas = await html2canvas(el, { scale: 2, useCORS: true, backgroundColor: '#ffffff' });
      const imgData = canvas.toDataURL('image/jpeg', 0.95);
      const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' });
      const pdfW = pdf.internal.pageSize.getWidth();
      const pdfH = pdf.internal.pageSize.getHeight();
      const ratio = pdfW / canvas.width;
      const totalHeight = canvas.height * ratio;
      let pos = 0, page = 0;
      while (pos < totalHeight) {
        if (page > 0) pdf.addPage();
        pdf.addImage(imgData, 'JPEG', 0, -pos, pdfW, totalHeight);
        pos += pdfH;
        page++;
      }
      pdf.save(`${article.title.slice(0, 20).replace(/[\/\\?%*:|"<>]/g, '')}.pdf`);
    } catch (err) { console.error('PDF 生成失败:', err); }
  };

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

  return (
    <div className="flex-1 flex flex-col min-h-0 animate-fade-in" style={{ background: 'var(--color-bg-white)' }}>
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 lg:px-5 py-2.5 flex-shrink-0 no-print" style={{ borderBottom: '1px solid var(--color-border-light)', background: 'var(--color-bg-white)' }}>
        <button onClick={onBack} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>← 返回</button>
        <span className="text-sm font-medium truncate flex-1" style={{ color: 'var(--color-text-title)' }}>{loading ? '加载中...' : article?.title}</span>
      </div>

      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center p-8" style={{ background: 'var(--color-bg-off)' }}>
          <div className="w-full max-w-2xl space-y-6">
            {/* Skeleton title */}
            <div style={{ height: '24px', width: '60%', background: 'var(--color-border-light)', borderRadius: '4px', marginBottom: '8px' }} />
            {/* Skeleton meta */}
            <div style={{ height: '14px', width: '30%', background: 'var(--color-border-light)', borderRadius: '4px', marginBottom: '24px' }} />
            {/* Skeleton lines */}
            {[1,2,3,4,5].map((i) => (
              <div key={i} style={{ height: '14px', width: `${70 + (i % 3) * 10}%`, background: 'var(--color-border-light)', borderRadius: '4px', marginBottom: '10px' }} />
            ))}
          </div>
        </div>
      ) : article ? (
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          <div ref={contentScrollRef} className="flex-1 min-w-0 overflow-y-auto" style={{ borderRight: '1px solid var(--color-border-light)', background: 'var(--color-bg-white)' }}>
            <div className="p-5 lg:p-8 max-w-3xl mx-auto">
              {article.summary && (
                <div className="no-print" style={{ background: 'var(--color-bg-off)', borderRadius: '4px', padding: '16px', marginBottom: '24px' }}>
                  <h3 className="font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>AI 精读</h3>
                  <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-body)' }}>{article.summary}</div>
                  {article.importance_reason && <div className="mt-2 text-xs italic" style={{ color: 'var(--color-text-label)' }}>{article.importance_reason}</div>}
                  {article.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {article.tags.map((t) => (<span key={t} className="px-2 py-0.5 text-xs rounded" style={{ background: 'var(--color-border-light)', color: 'var(--color-text-muted)' }}>{t}</span>))}
                    </div>
                  )}
                </div>
              )}

              <h2 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)', lineHeight: 1.35, marginBottom: '12px' }}>{article.title}</h2>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-6" style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
                <div className="flex items-center gap-2">
                  <span>{article.source_name}</span><span>·</span><span>{article.published_at?.slice(0, 10)}</span>
                </div>
                <div className="flex items-center gap-2 flex-wrap sm:ml-auto no-print">
                  {/* TTS button — hidden on devices without SpeechSynthesis */}
                  {ttsSupported && (<>
                  <button onClick={() => ttsToggle(articleText)}
                    title={ttsState === 'idle' ? '朗读' : ttsState === 'playing' ? '暂停' : '继续'}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: ttsState !== 'idle' ? 'var(--color-blue-link)' : 'var(--color-text-muted)', transition: 'color 0.15s' }}>
                    {ttsState === 'playing' ? <IconPause /> : <IconPlay />}
                    <span>{ttsState === 'idle' ? '朗读' : ttsState === 'playing' ? '暂停' : '继续'}</span>
                  </button>
                  {ttsState !== 'idle' && (
                    <button onClick={() => ttsStop()}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: 'var(--color-text-muted)' }}>
                      <IconStop />
                    </button>
                  )}
                  </>)}

                  {/* Bookmark button */}
                  <button onClick={toggleBookmark} title={isBookmarked ? '取消收藏' : '收藏'}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: isBookmarked ? '#C8960A' : 'var(--color-text-muted)', transition: 'color 0.15s' }}>
                    {isBookmarked ? <IconBookmarkFilled /> : <IconBookmark />}
                    <span>{isBookmarked ? '已收藏' : '收藏'}</span>
                  </button>
                  {article.url && (<a href={article.url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-blue-link)' }}>在新窗口阅读 ↗</a>)}
                </div>
              </div>
              <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-body)', lineHeight: '1.8', fontSize: '15px' }}>
                <span dangerouslySetInnerHTML={{ __html: renderArticleContent(articleText) }} />
              </div>

              {/* PDF export */}
              <div className="mt-8 pt-6 text-center no-print" style={{ borderTop: '1px solid var(--color-border-light)' }}>
                <button onClick={downloadPDF} disabled={loading}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '12px', color: 'var(--color-text-muted)', background: 'transparent', border: '1px solid var(--color-border)', borderRadius: '4px', cursor: 'pointer', transition: 'all 0.15s' }}>
                  <IconPDF />
                  导出 PDF
                </button>
              </div>
            </div>
          </div>

          {/* Right panel: Chat — becomes bottom panel on mobile */}
          <div className="w-full lg:w-[400px] xl:w-[440px] flex-shrink-0 flex flex-col no-print lg:border-t-0" style={{ background: 'var(--color-bg-off)', borderTop: '1px solid var(--color-border-light)' }}>
            <ErrorBoundary>
            <div className="flex flex-col min-h-0 max-h-[40vh] lg:max-h-none h-full" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* 标题栏 + 移动端折叠按钮 */}
              <div className="px-5 pt-4 pb-2 flex-shrink-0 flex items-center justify-between">
                <h3 className="font-semibold text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>深入对话</h3>
                <button onClick={() => setChatCollapsed(!chatCollapsed)}
                  className="lg:hidden flex items-center justify-center"
                  style={{ background: 'var(--color-bg-hover)', border: 'none', borderRadius: '3px', cursor: 'pointer', padding: '2px 8px', fontSize: '11px', color: 'var(--color-text-label)' }}>
                  {chatCollapsed ? '展开' : '折叠'}
                </button>
              </div>

              {/* 折叠内容 — 移动端折叠时隐藏 */}
              <div className={`flex-1 flex flex-col min-h-0 ${chatCollapsed ? 'hidden' : ''}`}>
                {/* 消息区 — 可滚动 */}
                <div className="flex-1 overflow-y-auto px-4 pb-2 space-y-2.5 min-h-0">
                  {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full" style={{ padding: '24px 12px' }}>
                      <p className="text-xs mb-4" style={{ color: 'var(--color-text-label)' }}>问关于这篇文章的问题</p>
                      <div className="flex flex-col gap-2 w-full max-w-[320px]">
                        {(() => {
                          const tags = article?.tags || [];
                          const prompts = ['总结核心观点', '有哪些技术细节？', '有什么争议？', '这篇文章的局限性？'];
                          if (tags.length > 0) {
                            prompts.push(`解释本文中的「${tags[0]}」概念`);
                            if (tags.length > 1) prompts.push(`本文如何体现「${tags[1]}」的发展？`);
                            if (tags.length > 2) prompts.push(`「${tags[2]}」在其中的作用是什么？`);
                            prompts.push(`和同类文章相比，本文的独特之处？`);
                          }
                          return [...new Set(prompts)].slice(0, 7).map((q) => (
                            <button key={q} onClick={() => { setChatInput(q); setTimeout(() => chatInputRef.current?.focus(), 100); }}
                              className="w-full text-left px-3.5 py-2.5 text-xs rounded transition-all hover:brightness-95"
                              style={{ background: 'var(--color-bg-white)', border: '1px solid var(--color-border-light)', color: 'var(--color-text-body)' }}>{q}</button>
                          ));
                        })()}
                      </div>
                    </div>
                  )}
                  {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className="max-w-[90%] px-3 py-2 text-xs leading-relaxed rounded"
                      style={msg.role === 'user'
                        ? { background: 'var(--color-text-title)', color: 'var(--color-bg-white)' }
                        : { background: 'var(--color-bg-white)', color: 'var(--color-text-body)' }}>
                      <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(renderMd(msg.content)) }} />
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="px-3 py-2 rounded flex gap-1" style={{ background: 'var(--color-bg-white)' }}>
                      <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              <div className="p-4 pt-3 flex-shrink-0" style={{ borderTop: '1px solid var(--color-border-light)' }}>
                <form onSubmit={handleChat} className="flex gap-2">
                  <input ref={chatInputRef} type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)}
                    placeholder="输入问题..." className="flex-1 px-3 py-2 text-sm rounded"
                    style={{ background: 'var(--color-bg-white)', border: '1px solid var(--color-border)', color: 'var(--color-text-body)' }} />
                  <button type="submit" disabled={chatLoading || !chatInput.trim()}
                    className="px-4 py-2 text-sm rounded disabled:opacity-40 font-medium"
                    style={{ background: 'var(--color-text-title)', color: 'var(--color-bg-white)' }}>发送</button>
                </form>
              </div>
            </div>
            </div>
            </ErrorBoundary>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center p-8" style={{ background: 'var(--color-bg-off)' }}>
          <div className="text-center">
            <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <p style={{ fontSize: '15px', fontWeight: 500, color: 'var(--color-text-title)', marginBottom: '4px' }}>文章加载失败</p>
            <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '16px' }}>请检查网络连接后重试</p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => window.location.reload()} style={{ fontSize: '13px', padding: '8px 20px', color: 'white', background: 'var(--color-blue-link)', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                重试
              </button>
              <button onClick={onBack} style={{ fontSize: '13px', padding: '8px 20px', color: 'var(--color-blue-link)', background: 'none', border: '1px solid var(--color-blue-link)', borderRadius: '6px', cursor: 'pointer' }}>
                返回
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden PDF source */}
      {article && (
        <div ref={pdfContentRef} style={{ position: 'fixed', top: '-9999px', left: '-9999px', width: '794px', padding: '60px 50px', fontFamily: "'Source Serif 4', 'Noto Serif CJK SC', 'STSong', Georgia, serif", lineHeight: 1.9, color: '#1a1a1a', background: '#ffffff', fontSize: '14px' }}>
          <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '24px', fontWeight: 700, marginBottom: '10px', lineHeight: 1.35 }}>{article.title}</h1>
          <p style={{ fontSize: '11px', color: '#666', marginBottom: '24px' }}>{article.source_name}{article.published_at ? ` · ${article.published_at.slice(0, 10)}` : ''}</p>
          <div style={{ fontSize: '12px', lineHeight: 1.9, whiteSpace: 'pre-wrap' }} dangerouslySetInnerHTML={{ __html: renderArticleContent(articleText) }} />
        </div>
      )}
    </div>
  );
}
