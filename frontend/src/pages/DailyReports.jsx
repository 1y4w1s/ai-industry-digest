import { useState, useEffect } from 'react';
import { api } from '../api/client';

const SOURCE_ICONS = {
  'arXiv': '📄', '量子位': '🔬', '36氪': '💡', '36氪 - AI': '💡',
  '机器之心': '🤖', 'GitHub': '⭐',
};

export default function DailyReports({ onArticleClick }) {
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    setLoading(true);
    api.getReports(page).then((data) => {
      setReports(data.items || []);
      setTotal(data.total || 0);
      if (!selectedDate && data.items?.length > 0) {
        setSelectedDate(data.items[0].report_date);
      }
    }).finally(() => setLoading(false));
  }, [page]);

  useEffect(() => {
    if (!selectedDate) return;
    setDetailLoading(true);
    api.getReport(selectedDate).then((data) => {
      setReport(data);
    }).finally(() => setDetailLoading(false));
  }, [selectedDate]);

  // Flatten articles by source
  const articles = [];
  if (report) {
    for (const level of ['high', 'medium', 'low']) {
      for (const a of (report.articles?.[level] || [])) {
        articles.push({ ...a, _imp: level });
      }
    }
  }

  const groups = {};
  for (const a of articles) {
    const src = a.source_name || '其他';
    if (!groups[src]) groups[src] = [];
    groups[src].push(a);
  }

  const impOrder = { high: 0, medium: 1, low: 2 };

  const handleArticleClick = async (a) => {
    onArticleClick(a.id);
  };

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="font-heading text-xl font-bold text-text-primary">首页日报</h1>
        <p className="text-sm text-text-secondary mt-1">每日 AI 行业精选，一键掌握行业动态</p>
      </div>

      {loading ? (
        <div className="text-center text-text-tertiary py-12 text-sm">加载中...</div>
      ) : (
        <>
          {/* Date navigation */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {reports.map((r) => (
              <button
                key={r.report_date}
                onClick={() => setSelectedDate(r.report_date)}
                className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  selectedDate === r.report_date
                    ? 'bg-accent/10 border border-accent/30 text-accent'
                    : 'bg-bg-raised border border-border-primary text-text-secondary hover:text-text-primary hover:border-border-accent/50'
                }`}
              >
                <div className="text-xs opacity-60">{formatDateShort(r.report_date)}</div>
                <div className="font-semibold">{r.report_date}</div>
              </button>
            ))}
          </div>

          {/* Report detail */}
          {detailLoading ? (
            <div className="text-center text-text-tertiary py-12 text-sm">加载日报详情...</div>
          ) : report ? (
            <div className="animate-fade-in">
              {/* Overview */}
              <div className="bg-bg-surface border border-border-primary rounded-2xl p-6 mb-6">
                <div className="flex items-center gap-4 text-sm text-text-secondary mb-4">
                  <span>📰 {articles.length} 篇文章</span>
                  <span>📡 {Object.keys(groups).length} 个来源</span>
                </div>
                {report.summary_insight && (
                  <div className="bg-bg-raised rounded-xl p-4 mb-4 text-sm text-text-primary leading-relaxed border-l-2 border-accent">
                    {report.summary_insight}
                  </div>
                )}
                {report.trending_keywords?.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {report.trending_keywords.map((k) => (
                      <span key={k} className="px-3 py-1 bg-accent/10 text-accent text-xs rounded-full border border-accent/20">
                        {k}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Source groups */}
              {Object.entries(groups).sort(([,a],[,b]) => b.filter(x=>x._imp==='high').length - a.filter(x=>x._imp==='high').length).map(([src, arts]) => {
                const icon = Object.entries(SOURCE_ICONS).find(([k]) => src.includes(k))?.[1] || '📰';
                return (
                  <div key={src} className="mb-6">
                    <div className="flex items-center gap-2 mb-3 pb-2 border-b border-border-primary">
                      <span className="text-lg">{icon}</span>
                      <span className="font-heading font-semibold text-sm text-text-primary">{src}</span>
                      <span className="text-xs text-text-tertiary ml-auto">{arts.length} 篇</span>
                    </div>
                    <div className="space-y-2">
                      {arts.sort((a, b) => impOrder[a._imp] - impOrder[b._imp]).map((a) => (
                        <div
                          key={a.id || a.url}
                          onClick={() => handleArticleClick(a)}
                          className="bg-bg-surface border border-border-primary rounded-xl p-4 cursor-pointer hover:border-accent/30 hover:bg-bg-raised transition-all group"
                        >
                          <div className="flex items-start gap-3">
                            <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${
                              a._imp === 'high' ? 'bg-high-imp' : a._imp === 'medium' ? 'bg-medium-imp' : 'bg-low-imp'
                            }`} />
                            <div className="flex-1 min-w-0">
                              <h3 className="font-medium text-sm text-text-primary group-hover:text-accent transition-colors leading-relaxed">
                                {a.title}
                              </h3>
                              <div className="flex items-center gap-3 mt-1.5 text-xs text-text-tertiary">
                                <span>{a.source_name}</span>
                                {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                                {a.tags?.length > 0 && (
                                  <span>· {a.tags.slice(0, 2).join(', ')}{a.tags.length > 2 ? '...' : ''}</span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}

              {/* Pagination */}
              {report?.total_pages > 1 && (
                <div className="flex justify-center gap-2 mt-6">
                  <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">
                    ← 上一页
                  </button>
                  <span className="px-3 py-1.5 text-xs text-text-tertiary">{page}</span>
                  <button disabled={page >= total} onClick={() => setPage(page + 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">
                    下一页 →
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-text-tertiary py-12 text-sm">暂无内容</div>
          )}
        </>
      )}
    </div>
  );
}

function formatDateShort(dateStr) {
  const d = new Date(dateStr);
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return `${(d.getMonth()+1).toString().padStart(2,'0')}/${d.getDate().toString().padStart(2,'0')} 周${weekdays[d.getDay()]}`;
}
