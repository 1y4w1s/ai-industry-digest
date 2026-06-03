import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import ArticleReader from '../components/ArticleReader';
import SidePanel from '../components/SidePanel';

export default function Home({ onReadArticle, readerArticle }) {
  const [searchParams] = useSearchParams();
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sidePanelOpen, setSidePanelOpen] = useState(true);

  const [keyword, setKeyword] = useState(searchParams.get('q') || '');
  const [importance, setImportance] = useState('');
  const [source, setSource] = useState('');
  const [tag, setTag] = useState('');
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    api.getSources().then((d) => setSources(d.sources || [])).catch(() => {});
    api.getTags().then((d) => setTags(d.tags || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) { setKeyword(q); doSearch(q, '', '', '', 1); }
  }, [searchParams]);

  useEffect(() => {
    if (searching) return;
    setLoading(true);
    api.getReports(page).then((data) => {
      setReports(data.items || []);
      setTotal(data.total || 0);
      if (!selectedDate && data.items?.length > 0) setSelectedDate(data.items[0].report_date);
    }).finally(() => setLoading(false));
  }, [page, searching]);

  useEffect(() => {
    if (!selectedDate || searching) return;
    setDetailLoading(true);
    api.getReport(selectedDate).then((data) => setReport(data)).finally(() => setDetailLoading(false));
  }, [selectedDate, searching]);

  const doSearch = async (kw, imp, src, tg, pg) => {
    setSearching(true); setDetailLoading(true);
    try {
      const data = await api.getArticles({ page: pg, page_size: 50, keyword: kw || undefined, importance: imp || undefined, source: src || undefined, tag: tg || undefined });
      setSearchResults(data); setPage(pg);
    } catch { setSearchResults({ items: [], total: 0, pages: 0 }); }
    finally { setDetailLoading(false); }
  };

  const handleClearSearch = () => {
    setKeyword(''); setImportance(''); setSource(''); setTag('');
    setSearching(false); setSearchResults(null);
  };

  const handleQuickFilter = (imp, src, tg) => {
    if (imp || src || tg) doSearch(keyword || '', imp, src, tg, 1);
    else { setSearching(false); setSearchResults(null); }
  };

  const activeFilterCount = [importance, source, tag].filter(Boolean).length;
  const isFilterActive = searching || activeFilterCount > 0;

  const handleAskAI = (question) => {
    // Find the AI chat bubble button and click it, then set the input
    const aiBubble = document.querySelector('[data-ai-trigger]');
    if (aiBubble) aiBubble.click();
    // Dispatch custom event with the question
    window.dispatchEvent(new CustomEvent('ai-ask', { detail: { question } }));
  };

  if (readerArticle) return <ArticleReader articleId={readerArticle} onBack={() => onReadArticle(null)} />;

  const articles = [];
  if (report && !searching) {
    for (const level of ['high', 'medium', 'low'])
      for (const a of (report.articles?.[level] || [])) articles.push({ ...a, _imp: level });
  }

  const groups = {};
  for (const a of (searchResults?.items || articles)) {
    const src = a.source_name || '其他';
    if (!groups[src]) groups[src] = [];
    groups[src].push(a);
  }

  const topArticles = articles.filter((a) => a._imp === 'high').slice(0, 5);
  const displayReporting = !searching && report;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* ═══ Unified Filter Bar ═══ */}
      <div className="flex-shrink-0" style={{ 
        background: 'linear-gradient(180deg, #1A1B33 0%, #13152A 100%)',
        borderBottom: '1px solid #2E2F4F',
        padding: '8px 16px'
      }}>
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Importance pills */}
          <div className="flex items-center gap-1.5">
            {[
              { key: 'high', label: '高', color: '#F27070', bg: 'rgba(242,112,112,0.12)' },
              { key: 'medium', label: '中', color: '#D4A44A', bg: 'rgba(212,164,74,0.12)' },
              { key: 'low', label: '低', color: '#6E739C', bg: 'rgba(110,115,156,0.12)' },
            ].map((opt) => (
              <button
                key={opt.key}
                onClick={() => {
                  const next = importance === opt.key ? '' : opt.key;
                  setImportance(next);
                  if (keyword.trim() || next || source || tag) {
                    doSearch(keyword, next, source, tag, 1);
                  } else { setSearching(false); setSearchResults(null); }
                }}
                className="text-xs font-medium rounded-full px-3 py-[5px] transition-all cursor-pointer"
                style={{
                  background: importance === opt.key ? opt.bg : 'transparent',
                  color: importance === opt.key ? opt.color : '#6E739C',
                  border: importance === opt.key ? `1px solid ${opt.color}40` : '1px solid transparent',
                }}
              >
                <span className="inline-block w-1.5 h-1.5 rounded-full mr-1.5" style={{ background: opt.color }} />
                {opt.label}
              </button>
            ))}
          </div>

          {/* Source dropdown */}
          <select value={source} onChange={(e) => { setSource(e.target.value); handleQuickFilter(importance, e.target.value, tag); }}
            className="h-[30px] px-2.5 text-xs rounded-[6px] cursor-pointer focus:outline-none transition-all"
            style={{ background: '#1A1B33', border: '1px solid #2E2F4F', color: source ? '#E2E6F9' : '#6E739C', maxWidth: '100px' }}>
            <option value="">来源</option>
            {sources.map((s) => <option key={s} value={s} style={{ background: '#1A1B33' }}>{s}</option>)}
          </select>

          {/* Tag dropdown */}
          <select value={tag} onChange={(e) => { setTag(e.target.value); handleQuickFilter(importance, source, e.target.value); }}
            className="h-[30px] px-2.5 text-xs rounded-[6px] cursor-pointer focus:outline-none transition-all"
            style={{ background: '#1A1B33', border: '1px solid #2E2F4F', color: tag ? '#E2E6F9' : '#6E739C', maxWidth: '100px' }}>
            <option value="">标签</option>
            {tags.map((t) => <option key={t} value={t} style={{ background: '#1A1B33' }}>{t}</option>)}
          </select>

          {/* Filter status + clear */}
          {isFilterActive && (
            <div className="flex items-center gap-2 ml-1">
              <span className="text-[11px] whitespace-nowrap" style={{ color: '#6395FF' }}>
                {searching ? `${searchResults?.total || 0} 条结果` : `${activeFilterCount} 个筛选中`}
              </span>
              <button onClick={handleClearSearch} className="text-[11px] transition-all hover:brightness-110 whitespace-nowrap" style={{ color: '#6E739C' }}>
                清除
              </button>
            </div>
          )}

          {/* Side panel toggle (tablet) */}
          <button onClick={() => setSidePanelOpen(!sidePanelOpen)}
            className="hidden lg:flex xl:hidden ml-auto h-[30px] px-2 text-xs rounded-[6px] items-center gap-1 transition-all cursor-pointer"
            style={{ background: '#1A1B33', border: '1px solid #2E2F4F', color: '#9197C2' }}>
            <span className={sidePanelOpen ? 'rotate-180' : ''} style={{ display: 'inline-block', transition: 'transform 0.2s' }}>◀</span>
          </button>
        </div>
      </div>

      {/* ═══ Three-column Content ═══ */}
      <div className="flex-1 flex overflow-hidden" style={{ background: '#13152A' }}>
        {/* Main content area */}
        <div className="flex-1 min-w-0 overflow-y-auto">
          <div className="px-5" style={{ paddingTop: '20px', paddingBottom: '32px' }}>
            {/* Date chips */}
            {!searching && reports.length > 0 && (
              <div className="flex gap-[10px] mb-5 overflow-x-auto pb-1">
                {reports.map((r) => (
                  <button key={r.report_date} onClick={() => { setSelectedDate(r.report_date); setPage(1); }}
                    className="flex-shrink-0 px-4 py-[6px] rounded-md text-xs font-medium transition-all hover:border-accent/50"
                    style={{
                      background: selectedDate === r.report_date ? '#202A4F' : '#1A1B33',
                      color: selectedDate === r.report_date ? '#E2E6F9' : '#9197C2',
                      border: selectedDate === r.report_date ? '1px solid transparent' : '1px solid #2E2F4F',
                    }}>
                    <span className="opacity-70">{formatDateShort(r.report_date)}</span>
                    <span className="ml-1.5 font-semibold">{r.report_date}</span>
                  </button>
                ))}
              </div>
            )}

            {searching && (
              <div className="text-xs mb-4" style={{ color: '#9197C2' }}>
                {searchResults ? `搜索到 ${searchResults.total} 条结果` : '搜索中...'}
                <span className="mx-2">·</span>
                <button onClick={handleClearSearch} className="hover:underline" style={{ color: '#6395FF' }}>返回日报</button>
              </div>
            )}

            {detailLoading ? (
              <div className="text-center py-16 text-sm" style={{ color: '#6E739C' }}>加载中...</div>
            ) : displayReporting ? (
              <>
                {/* Bento Stats */}
                <div className="grid grid-cols-3 gap-4 mb-5">
                  {[
                    { label: '文章总数', value: articles.length, icon: '📰', color: '#6395FF' },
                    { label: '信息源', value: Object.keys(groups).length, icon: '📡', color: '#39C488' },
                    { label: '高重要性', value: articles.filter((a) => a._imp === 'high').length, icon: '🔥', color: '#F27070' },
                  ].map((s) => (
                    <div key={s.label} className="stat-card text-center rounded-xl" style={{ background: '#16172D', padding: '22px 12px' }}>
                      <div className="text-lg mb-1">{s.icon}</div>
                      <div className="font-heading font-bold" style={{ fontSize: '28px', color: s.color, lineHeight: 1.2 }}>{s.value}</div>
                      <div className="text-xs mt-1" style={{ color: '#9197C2' }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                {/* Overview */}
                {report.summary_insight && (
                  <div className="mb-5 p-4 rounded-xl" style={{ background: '#1A1B33', border: '1px solid #2E2F4F' }}>
                    <div className="text-sm leading-relaxed" style={{ color: '#E2E6F9', borderLeft: '3px solid #6395FF', paddingLeft: '14px' }}>
                      {report.summary_insight}
                    </div>
                    {report.trending_keywords?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {report.trending_keywords.map((k) => (
                          <span key={k} className="px-2.5 py-0.5 text-xs rounded-full" style={{ background: 'rgba(99,149,255,0.08)', color: '#6395FF', border: '1px solid rgba(99,149,255,0.15)' }}>{k}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Source groups */}
                {Object.entries(groups).sort(([,a],[,b]) => b.filter(x=>x._imp==='high').length - a.filter(x=>x._imp==='high').length).map(([src, arts]) => (
                  <div key={src} className="mb-5">
                    <div className="flex items-center pb-3 mb-3" style={{ borderBottom: '1px solid #2E2F4F', marginTop: '24px' }}>
                      <span className="font-heading font-semibold text-sm" style={{ color: '#E2E6F9' }}>{src}</span>
                      <span className="text-xs ml-auto" style={{ color: '#6E739C' }}>{arts.length} 篇</span>
                    </div>
                    <div className="space-y-2">
                      {arts.sort((a, b) => ({high:0,medium:1,low:2}[a._imp]||2) - ({high:0,medium:1,low:2}[b._imp]||2)).map((a) => (
                        <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                          className={`article-card ${a._imp === 'high' ? 'article-card-high' : a._imp === 'medium' ? 'article-card-medium' : 'article-card-low'}`}>
                          <div className="title">{a.title}</div>
                          <div className="flex items-center gap-2 mt-1 text-xs" style={{ color: '#9197C2' }}>
                            <span>{a.source_name}</span>
                            {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                {articles.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#6E739C' }}>暂无内容</div>}
              </>
            ) : searching && searchResults ? (
              <div className="space-y-2">
                {searchResults.items.map((a) => (
                  <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                    className="article-card" style={{ borderLeft: '3px solid ' + (a.importance === 'high' ? '#F27070' : a.importance === 'medium' ? 'rgba(212,164,74,0.5)' : 'transparent') }}>
                    <div className="title">{a.title}</div>
                    <div className="flex items-center gap-2 mt-1 text-xs" style={{ color: '#9197C2' }}>
                      <span>{a.source_name}</span>
                      {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                    </div>
                    {a.summary && <p className="text-xs mt-1.5 line-clamp-2" style={{ color: '#6E739C' }}>{a.summary}</p>}
                  </div>
                ))}
                {searchResults.items.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#6E739C' }}>未找到相关文章</div>}
              </div>
            ) : (
              <div className="text-center py-16 text-sm" style={{ color: '#6E739C' }}>暂无数据</div>
            )}

            {/* Pagination */}
            {searching && searchResults?.pages > 1 && (
              <div className="flex justify-center gap-2 mt-6">
                <button disabled={page <= 1} onClick={() => doSearch(keyword, importance, source, tag, page - 1)}
                  className="px-3 py-1.5 rounded-lg text-xs transition-all disabled:opacity-40" style={{ background: '#22233D', border: '1px solid #2E2F4F', color: '#9197C2' }}>←</button>
                {Array.from({ length: Math.min(searchResults.pages, 5) }, (_, i) => {
                  const p = Math.max(1, page - 2) + i;
                  if (p > searchResults.pages) return null;
                  return <button key={p} onClick={() => doSearch(keyword, importance, source, tag, p)}
                    className="px-3 py-1.5 rounded-lg text-xs transition-all"
                    style={p === page ? { background: '#6395FF', color: '#fff' } : { background: '#22233D', border: '1px solid #2E2F4F', color: '#9197C2' }}>{p}</button>;
                })}
                <button disabled={page >= searchResults.pages} onClick={() => doSearch(keyword, importance, source, tag, page + 1)}
                  className="px-3 py-1.5 rounded-lg text-xs transition-all disabled:opacity-40" style={{ background: '#22233D', border: '1px solid #2E2F4F', color: '#9197C2' }}>→</button>
              </div>
            )}
          </div>
        </div>

        {/* ═══ Right Side Panel ═══ */}
        <div
          className={`flex-shrink-0 overflow-y-auto transition-all duration-300 ${
            sidePanelOpen ? 'w-[340px] xl:w-[380px] opacity-100' : 'w-0 opacity-0 overflow-hidden'
          } ${searching ? 'hidden' : ''}`}
          style={{ borderLeft: '1px solid #2E2F4F', padding: '20px 16px', background: '#13152A' }}
        >
          <SidePanel
            keywords={report?.trending_keywords || []}
            insight={report?.summary_insight || ''}
            topArticles={topArticles}
            allArticles={articles}
            sources={Object.keys(groups)}
            onArticleClick={(id) => onReadArticle(id)}
            onAskAI={handleAskAI}
          />
        </div>
      </div>
    </div>
  );
}

function formatDateShort(dateStr) {
  const d = new Date(dateStr);
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} 周${weekdays[d.getDay()]}`;
}
