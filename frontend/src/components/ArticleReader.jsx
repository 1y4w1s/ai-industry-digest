import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { api } from '../api/client';
import { renderMd, renderArticleContent } from '../utils/markdown';
import DOMPurify from 'dompurify';
import { Cache, CACHE_TTL } from '../utils/cache';
import { useToast } from './Toast';
import ErrorBoundary from './ErrorBoundary';
import CommentSection from './CommentSection';
import AiSummaryCard from './AiSummaryCard';
import { IconPlay, IconPause, IconStop, IconBookmark, IconBookmarkFilled, IconPDF, IconShare } from './icons';
import useTTS from '../hooks/useTTS';
import ArticleMetaActions from './ArticleMetaActions';
import ChatPanel from './ChatPanel';
import PDFExportButton from './PDFExportButton';
import ScrollToTopButton from './ScrollToTopButton';

// html2canvas / jspdf 仅在用户点击「导出 PDF」时才需要，改为动态导入，避免首屏加载 ~300KB

/* ── stripHtml for TTS ───────────────────────── */
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
export default function ArticleReader({ articleId, onBack }) {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [bookmarkId, setBookmarkId] = useState(null);
  const [chatCollapsed, setChatCollapsed] = useState(false);  // 移动端对话面板折叠
  const [showTop, setShowTop] = useState(false);              // 回到顶部按钮
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
  const readingMinutes = article ? Math.max(1, Math.round((articleText.length || 0) / 300)) : 0;
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
          setShowTop(scrollTop > 500);
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
      try { await api.removeBookmark(bookmarkId); setBookmarkId(null); Cache.remove('bookmarks'); toast('已取消收藏', 'info'); } catch (e) { if (e.message.includes('401') || e.message.includes('未登录')) toast('请先登录才能收藏', 'info'); }
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
      } catch (e) { if (e.message.includes('401') || e.message.includes('未登录')) toast('请先登录才能收藏', 'info'); }
    }
  };

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const downloadPDF = async () => {
    if (!article) return;
    const el = pdfContentRef.current;
    if (!el) return;
    try {
      const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
        import('html2canvas'),
        import('jspdf'),
      ]);
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

  const handleShare = async () => {
    if (!article) return;
    const url = `${window.location.origin}/?article=${encodeURIComponent(articleId)}`;
    try {
      if (navigator.share) {
        await navigator.share({ title: article.title, url });
        return;
      }
    } catch {
      // 用户取消系统分享 → 降级到复制链接
    }
    try {
      await navigator.clipboard.writeText(url);
      toast('链接已复制', 'success');
    } catch {
      toast('复制失败，请手动复制地址栏链接', 'info');
    }
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
              {article.summary && <AiSummaryCard summary={article.summary} importanceReason={article.importance_reason} tags={article.tags} />}

              <h2 style={{ fontFamily: "var(--font-display)", fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)', lineHeight: 1.35, marginBottom: '12px' }}>{article.title}</h2>
              <ArticleMetaActions
                article={article}
                readingMinutes={readingMinutes}
                articleText={articleText}
                tts={{ supported: ttsSupported, state: ttsState, toggle: ttsToggle, stop: ttsStop }}
                isBookmarked={!!bookmarkId}
                onShare={handleShare}
                onBookmark={toggleBookmark}
                onExportPDF={downloadPDF}
                exporting={loading}
              />
              <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-body)', lineHeight: '1.8', fontSize: '15px' }}>
                <span dangerouslySetInnerHTML={{ __html: renderArticleContent(articleText) }} />
              </div>

              {/* 评论区（§3.2） */}
              <CommentSection articleId={articleId} />
            </div>
          </div>

          <ChatPanel
            messages={messages}
            chatInput={chatInput}
            chatLoading={chatLoading}
            chatCollapsed={chatCollapsed}
            article={article}
            chatEndRef={chatEndRef}
            ref={chatInputRef}
            onInputChange={(v) => setChatInput(v)}
            onSubmit={handleChat}
            onToggleCollapse={() => setChatCollapsed(!chatCollapsed)}
            onSelectPrompt={(q) => { setChatInput(q); setTimeout(() => chatInputRef.current?.focus(), 100); }}
          />
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

            {/* 回到顶部 */}
      <ScrollToTopButton visible={showTop} onClick={() => contentScrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' })} />
    </div>
  );
}
