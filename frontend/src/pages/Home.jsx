import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useReport } from '../hooks/useReport';
import { useFilter } from '../hooks/useFilter';
import ArticleReader from '../components/ArticleReader';
import SidePanel from '../components/SidePanel';
import DateNav from '../components/DateNav';
import FilterBar from '../components/FilterBar';
import ArticleGroup from '../components/ArticleGroup';
import HeroArticle from '../components/HeroArticle';
import DataStats from '../components/DataStats';
import RecommendationWidget from '../components/RecommendationWidget';

export default function Home() {
  const [sidePanelOpen, setSidePanelOpen] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const articleId = searchParams.get('article');

  const goToArticle = (id) => navigate(`/?article=${encodeURIComponent(id)}`);

  const {
    reports, selectedDate, setSelectedDate,
    report, loading, detailLoading,
    page, setPage, sources, tags,
    articles, highArticles,
    fromCache, cacheAge,
  } = useReport();

  // Handle ?date= param from Archive navigation
  useEffect(() => {
    const dateParam = searchParams.get('date');
    if (dateParam && reports.some((r) => r.report_date === dateParam)) {
      setSelectedDate(dateParam);
      // Clear the param so it doesn't re-trigger
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, reports, setSelectedDate, setSearchParams]);

  const {
    importance, setImportance,
    source, setSource,
    tag, setTag,
    filteredArticles, filteredGroups,
    activeFilterCount, clearFilters, toggleTag,
  } = useFilter(articles);

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
          <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px' }}>
            {reports.length > 0 && (
              <>
                {fromCache && (
                  <div style={{ fontSize: '11px', color: '#C8960A', marginBottom: '12px', padding: '6px 12px', background: 'rgba(200,150,10,0.06)', borderRadius: '4px', border: '1px solid rgba(200,150,10,0.15)' }}>
                    ⚠ 数据加载失败 · 显示{cacheAge !== null ? `${cacheAge} 分钟前` : ''}的缓存
                  </div>
                )}
                <DateNav
                  reports={reports}
                  selectedDate={selectedDate}
                  onSelect={(date) => { setSelectedDate(date); setPage(1); }}
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
                {heroArticle && <HeroArticle article={heroArticle} onSelect={goToArticle} />}
                {Object.entries(filteredGroups)
                  .sort(([, a], [, b]) => b.filter((x) => x._imp === 'high').length - a.filter((x) => x._imp === 'high').length)
                  .map(([src, arts]) => (
                    <ArticleGroup key={src} sourceName={src} articles={arts} onSelectArticle={goToArticle} />
                  ))}
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
