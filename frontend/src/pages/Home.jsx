import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import { useReport } from '../hooks/useReport';
import { useFilter } from '../hooks/useFilter';
import ArticleReader from '../components/ArticleReader';
import SidePanel from '../components/SidePanel';
import DateNav from '../components/DateNav';
import FilterBar from '../components/FilterBar';
import ArticleCard from '../components/ArticleCard';
import ArticleGroup from '../components/ArticleGroup';
import HeroArticle from '../components/HeroArticle';
import DataStats from '../components/DataStats';
import Pagination from '../components/Pagination';

export default function Home({ onReadArticle, readerArticle }) {
  const [searchParams] = useSearchParams();
  const [sidePanelOpen, setSidePanelOpen] = useState(true);
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  const {
    reports, selectedDate, setSelectedDate,
    report, loading, detailLoading,
    page, setPage, sources, tags,
    articles, highArticles,
  } = useReport();

  const {
    importance, setImportance,
    source, setSource,
    tag, setTag,
    filteredArticles, filteredGroups,
    activeFilterCount, clearFilters, toggleTag,
  } = useFilter(articles);

  const doSearch = async (kw, imp, src, tg, pg) => {
    setSearching(true);
    try {
      const data = await api.getArticles({
        page: pg, page_size: 50,
        keyword: kw || undefined,
        importance: imp || undefined,
        source: src || undefined,
        tag: tg || undefined,
      });
      setSearchResults(data);
      setPage(pg);
    } catch {
      setSearchResults({ items: [], total: 0, pages: 0 });
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    clearFilters();
    setSearching(false);
    setSearchResults(null);
  };

  const handleAskAI = (question) => {
    window.dispatchEvent(new CustomEvent('ai-ask', { detail: { question } }));
  };

  if (readerArticle) return <ArticleReader articleId={readerArticle} onBack={() => onReadArticle(null)} />;

  const heroArticle = highArticles[0];
  const displayReporting = !searching && report;

  return (
    <div className="h-full flex flex-col overflow-hidden" style={{ background: '#FBFCFD' }}>
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
        onClear={handleClearSearch}
      />

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 min-w-0 overflow-y-auto">
          <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px' }}>
            {!searching && reports.length > 0 && (
              <DateNav
                reports={reports}
                selectedDate={selectedDate}
                onSelect={(date) => { setSelectedDate(date); setPage(1); }}
              />
            )}
            {displayReporting && (
              <DataStats
                totalArticles={articles.length}
                sourceCount={Object.keys(filteredGroups).length}
                highCount={highArticles.length}
              />
            )}

            {searching && (
              <div className="text-xs mb-4" style={{ color: '#686C72' }}>
                {searchResults ? `搜索到 ${searchResults.total} 条结果` : '搜索中...'}
                <span className="mx-2">·</span>
                <button onClick={handleClearSearch} style={{ color: '#2864A8' }}>返回日报</button>
              </div>
            )}

            {detailLoading ? (
              <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>加载中...</div>
            ) : displayReporting ? (
              <>
                {heroArticle && <HeroArticle article={heroArticle} onSelect={onReadArticle} />}
                {Object.entries(filteredGroups)
                  .sort(([, a], [, b]) => b.filter((x) => x._imp === 'high').length - a.filter((x) => x._imp === 'high').length)
                  .map(([src, arts]) => (
                    <ArticleGroup key={src} sourceName={src} articles={arts} onSelectArticle={onReadArticle} />
                  ))}
                {articles.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>暂无内容</div>}
              </>
            ) : searching && searchResults ? (
              <div className="space-y-1">
                {searchResults.items.map((a) => (
                  <ArticleCard key={a.id || a.url} article={{ ...a, _imp: a.importance }} onSelect={onReadArticle} variant="detailed" />
                ))}
                {searchResults.items.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>未找到相关文章</div>}
              </div>
            ) : (
              <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>暂无数据</div>
            )}

            {searching && searchResults?.pages > 1 && (
              <Pagination
                page={page}
                totalPages={searchResults.pages}
                onPageChange={(pg) => doSearch('', importance, source, tag, pg)}
              />
            )}
          </div>
        </div>

        <div className={`flex-shrink-0 overflow-y-auto transition-all duration-300 ${sidePanelOpen ? 'w-[280px] opacity-100' : 'w-0 opacity-0 overflow-hidden'} ${searching ? 'hidden' : ''}`}
          style={{ borderLeft: '1px solid #E8EAED', padding: '20px 16px', background: '#FBFCFD' }}>
          <SidePanel
            keywords={report?.trending_keywords || []}
            insight={report?.summary_insight || ''}
            topArticles={highArticles}
            onArticleClick={(id) => onReadArticle(id)}
            onAskAI={handleAskAI}
            onTagFilter={toggleTag}
            activeTags={tag}
          />
        </div>
      </div>
    </div>
  );
}
