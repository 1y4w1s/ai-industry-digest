import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useReport } from '../hooks/useReport';
import { useFilter } from '../hooks/useFilter';
import { api } from '../api/client';
import { rankArticles } from '../lib/ranking';
import ArticleReader from '../components/ArticleReader';
import SidePanel from '../components/SidePanel';
import DateNav from '../components/DateNav';
import FilterBar from '../components/FilterBar';
import ArticleGroup from '../components/ArticleGroup';
import HeroArticle from '../components/HeroArticle';
import DataStats from '../components/DataStats';
import RecommendationWidget from '../components/RecommendationWidget';
import MainThreadPanel from '../components/MainThreadPanel';
import DailyBriefing from '../components/DailyBriefing';
import GitHubAgentsCard from '../components/GitHubAgentsCard';
import SubscribeBox from '../components/SubscribeBox';

export default function Home() {
  const [sidePanelOpen, setSidePanelOpen] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const articleId = searchParams.get('article');
  const [visibleCount, setVisibleCount] = useState(10);   // 移动端分批渲染：首次只展示 10 篇

  // 提前读取 URL 中的日期参数，传给 useReport 作为初始值
  const dateParam = searchParams.get('date');

  const goToArticle = (idOrArticle) => {
    // 兼容两种入参：string id 或 article 对象
    const id = typeof idOrArticle === 'string' ? idOrArticle : idOrArticle.id;
    const title = typeof idOrArticle === 'string' ? null : idOrArticle.title;
    // 写入最近浏览（4 条，去重，去旧）
    try {
      const list = JSON.parse(localStorage.getItem('signal.recent.v1') || '[]');
      // 如果 title 缺失，尝试从当前文章列表中查找
      const resolvedTitle = title || articles.find((a) => a.id === id || a.article_id === id)?.title || null;
      const entry = resolvedTitle ? { id, title: resolvedTitle, ts: Date.now() } : { id, ts: Date.now() };
      const dedup = [entry, ...list.filter((x) => x.id !== id)].slice(0, 4);
      localStorage.setItem('signal.recent.v1', JSON.stringify(dedup));
    } catch {}
    navigate(`/?article=${encodeURIComponent(id)}`);
  };

  const {
    reports, selectedDate, setSelectedDate,
    report, loading, detailLoading,
    page, setPage, total, sources, tags,
    articles, highArticles,
    fromCache, cacheAge,
    loadMore, loadingMore, hasMore,
  } = useReport(dateParam);

  // 清除 URL 中的 date 参数（在数据加载完成后）
  useEffect(() => {
    if (dateParam && selectedDate === dateParam) {
      setSearchParams({}, { replace: true });
    }
  }, [dateParam, selectedDate, setSearchParams]);

  const {
    importance, setImportance,
    source, setSource,
    tag, setTag,
    filteredArticles, filteredGroups,
    activeFilterCount, clearFilters, toggleTag,
  } = useFilter(articles);

  // P1a-1 · 零登录推荐排序：拉取 main-thread，配合 ranking.js 排 filteredArticles
  const [mainThread, setMainThread] = useState(null);
  useEffect(() => {
    if (!selectedDate) return;
    let cancelled = false;
    api.getMainThread(selectedDate)
      .then((data) => { if (!cancelled) setMainThread(data); })
      .catch(() => { if (!cancelled) setMainThread({ stories: [] }); });
    return () => { cancelled = true; };
  }, [selectedDate]);

  // 排名后的文章 id 序列（不命中顺序保留）—— ArticleGroup 用它做组内排序
  const rankedArticleIds = rankArticles(filteredArticles, mainThread).map((a) => a.id);

  const handleAskAI = (question) => {
    window.dispatchEvent(new CustomEvent('ai-ask', { detail: { question } }));
  };

  if (articleId) return <ArticleReader articleId={articleId} onBack={() => setSearchParams({})} />;

  const heroArticle = highArticles[0];
  const displayReporting = !!report;

  // Loading state
  if (loading && !fromCache) {
    return (
      <div className="flex-1 flex flex-col overflow-hidden min-h-0" style={{ background: 'var(--color-bg-white)' }}>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="flex gap-1.5 justify-center mb-3">
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
            </div>
            <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>加载中...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden min-h-0" style={{ background: 'var(--color-bg-white)' }}>
      <FilterBar
        importance={importance}
        source={source}
        tag={tag}
        sources={sources}
        tags={tags}
        activeFilterCount={activeFilterCount}
        onImportanceChange={setImportance}
        onSourceChange={setSource}
        onTagChange={setTag}
        onClear={clearFilters}
        onToggleSidePanel={() => setSidePanelOpen(!sidePanelOpen)}
        sidePanelOpen={sidePanelOpen}
      />

      <RecommendationWidget onNavigate={goToArticle} />

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 min-w-0 overflow-y-auto">
          <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px', maxWidth: '800px', margin: '0 auto' }}>
            {/* 品牌 Hero 行 */}
            <div className="reveal-up" style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 20 }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '15px', fontWeight: 700, color: 'var(--color-text-title)', letterSpacing: '0.04em' }}>
                今日速览
              </span>
              <span style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, var(--color-brass) 0%, var(--color-border-light) 100%)' }} />
              <span style={{ fontSize: '11px', color: 'var(--color-brass)', fontWeight: 500 }}>
                编辑部精选
              </span>
            </div>

            {/* 今日速览：首页首屏 hero（每日速览首屏改造 P0），置于文章列表之前 */}
            <DailyBriefing date={selectedDate} />

            {/* 今日主线（从侧栏移入内容区） */}
            {selectedDate && <MainThreadPanel date={selectedDate} />}

            {/* 今日 GitHub 推荐（P3-home）：首页编辑部主干的 GitHub 卡片 */}
            <GitHubAgentsCard range="week" minStars={100} sort="stars" limit={8} />

            {reports.length > 0 && (
              <>
                {fromCache && (
                  <div style={{ fontSize: '11px', color: 'var(--color-brass)', marginBottom: '12px', padding: '6px 12px', background: 'var(--color-brass-bg)', borderRadius: '6px' }}>
                    ⚠ 数据加载失败 · 显示{cacheAge !== null ? `${cacheAge} 分钟前` : ''}的缓存
                  </div>
                )}
                <DateNav
                  reports={reports}
                  selectedDate={selectedDate}
                  onSelect={(date) => { setSelectedDate(date); setPage(1); setVisibleCount(10); }}
                  hasMore={hasMore}
                  onLoadMore={loadMore}
                  loadingMore={loadingMore}
                />
              </>
            )}
            {displayReporting && (
              <DataStats
                totalArticles={articles.length}
                sourceCount={Object.keys(filteredGroups).length}
                highCount={highArticles.length}
              />
            )}

            {detailLoading ? (
              <div className="text-center py-16 text-sm" style={{ color: 'var(--color-text-label)' }}>加载中...</div>
            ) : displayReporting ? (
              <>
                {/* P1b 首页架构反转：原始文章流降级为「全部 AI 信号」归档区，
                    顶部「今日速览」+ 侧栏主线固化为首页编辑部主干。 */}
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 4, marginBottom: 16 }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', fontWeight: 700, color: 'var(--color-text-title)', letterSpacing: '0.04em' }}>
                    全部信号
                  </span>
                  <span style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, var(--color-brass) 0%, var(--color-border-light) 100%)' }} />
                  <span style={{ fontSize: '11px', color: 'var(--color-text-label)', whiteSpace: 'nowrap' }}>
                    共 {articles.length} 篇
                  </span>
                </div>
                {heroArticle && <HeroArticle article={heroArticle} onSelect={goToArticle} />}
                {Object.entries(filteredGroups)
                  .sort(([, a], [, b]) => b.filter((x) => x._imp === 'high').length - a.filter((x) => x._imp === 'high').length)
                  .slice(0, visibleCount)
                  .map(([src, arts]) => (
                    <ArticleGroup key={src} sourceName={src} articles={arts} onSelectArticle={goToArticle} customOrder={rankedArticleIds} />
                  ))}
                {/* 加载更多 */}
                {Object.entries(filteredGroups).length > visibleCount && (
                  <div className="text-center mt-4 no-print">
                    <button
                      onClick={() => setVisibleCount((c) => c + 10)}
                      className="w-full py-2.5 text-xs rounded transition-all"
                      style={{ background: 'var(--color-bg-off)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border-light)', cursor: 'pointer', boxShadow: 'var(--shadow-1)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--glass-bg)'; e.currentTarget.style.boxShadow = 'var(--glass-shadow)'; e.currentTarget.style.borderColor = 'var(--glass-border)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-bg-off)'; e.currentTarget.style.boxShadow = 'var(--shadow-1)'; e.currentTarget.style.borderColor = 'var(--color-border-light)'; }}
                    >
                      加载更多（{Object.entries(filteredGroups).length - visibleCount} 个来源）
                    </button>
                  </div>
                )}
                {articles.length === 0 && <div className="text-center py-16">
                  <div style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '4px' }}>
                    {activeFilterCount > 0 ? '暂无匹配的文章' : '暂无内容'}
                  </div>
                  {activeFilterCount > 0 && (
                    <button onClick={clearFilters}
                      style={{ fontSize: '12px', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                      清除筛选条件
                    </button>
                  )}
                </div>}
              </>
            ) : (
              <div className="text-center py-16 text-sm" style={{ color: 'var(--color-text-label)' }}>暂无数据</div>
            )}

            {/* 自助订阅（网站优化）：零成本增长入口 */}
            <SubscribeBox />
          </div>
        </div>

        <div className={`hidden lg:block flex-shrink-0 overflow-y-auto transition-all duration-300 ${sidePanelOpen ? 'w-[280px] opacity-100' : 'w-0 opacity-0 overflow-hidden'}`}
          style={{ borderLeft: '1px solid var(--color-border-light)', padding: '20px 16px', background: 'var(--color-bg-sidebar)' }}>
          <SidePanel
            keywords={report?.trending_keywords || []}
            insight={report?.summary_insight || ''}
            topArticles={highArticles}
            onArticleClick={(id) => goToArticle(id)}
            onAskAI={handleAskAI}
            onTagFilter={toggleTag}
            activeTags={tag}
          />
        </div>
      </div>
    </div>
  );
}
