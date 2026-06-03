import { useMemo } from 'react';
import { api } from '../api/client';

export default function SidePanel({ keywords = [], insight = '', topArticles = [], allArticles = [], sources = [], onArticleClick, onAskAI }) {
  // Build keyword frequency map for size variation
  const keywordFreq = useMemo(() => {
    const freq = {};
    // Count keyword occurrences across all article summaries
    if (allArticles.length > 0) {
      for (const a of allArticles) {
        for (const t of (a.tags || [])) {
          freq[t] = (freq[t] || 0) + 1;
        }
      }
    }
    // Also give base frequency to trending keywords
    for (const k of keywords) {
      if (!freq[k]) freq[k] = 1;
    }
    return freq;
  }, [keywords, allArticles]);

  const maxFreq = Math.max(...Object.values(keywordFreq), 1);

  const getKeywordSize = (word) => {
    const f = keywordFreq[word] || 1;
    const ratio = f / maxFreq;
    if (ratio > 0.6) return { fontSize: '15px', fontWeight: 700, padding: '6px 14px' };
    if (ratio > 0.3) return { fontSize: '13px', fontWeight: 600, padding: '5px 12px' };
    return { fontSize: '11px', fontWeight: 500, padding: '4px 10px' };
  };

  const getKeywordOpacity = (word) => {
    const f = keywordFreq[word] || 1;
    const ratio = f / maxFreq;
    return Math.max(0.5, Math.min(1, ratio + 0.3));
  };

  const handleQuickAsk = (question) => {
    if (onAskAI) onAskAI(question);
  };

  return (
    <div className="animate-fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* 🔥 热点词云 — 核心区域 */}
      <div className="rounded-xl" style={{ background: '#1A1B33', border: '1px solid #2E2F4F', padding: '20px 18px' }}>
        <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-4 flex items-center gap-2" style={{ color: '#9197C2' }}>
          <span className="text-base">🔥</span> 今日热点词云
        </h3>
        <div className="flex flex-wrap gap-2 items-center justify-center" style={{ minHeight: '120px' }}>
          {keywords.length > 0 ? keywords.map((k) => (
            <span
              key={k}
              onClick={() => handleQuickAsk(`聊聊 "${k}" 相关的新闻`)}
              className="rounded-full transition-all cursor-pointer hover:brightness-125 text-center leading-tight"
              style={{
                background: `rgba(99,149,255,${0.06 + getKeywordOpacity(k) * 0.1})`,
                color: `rgba(99,149,255,${0.5 + getKeywordOpacity(k) * 0.5})`,
                border: `1px solid rgba(99,149,255,${0.1 + getKeywordOpacity(k) * 0.15})`,
                ...getKeywordSize(k),
              }}
            >
              {k}
            </span>
          )) : (
            <span className="text-xs" style={{ color: '#6E739C' }}>暂无热点数据</span>
          )}
        </div>
      </div>

      {/* 📊 趋势速览 */}
      {insight ? (
        <div className="rounded-xl flex-1" style={{ background: '#1A1B33', border: '1px solid #2E2F4F', padding: '20px 18px', display: 'flex', flexDirection: 'column' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3 flex items-center gap-2" style={{ color: '#9197C2' }}>
            <span className="text-base">📊</span> 趋势速览
          </h3>
          <div className="flex-1 overflow-y-auto">
            <p className="text-xs leading-relaxed" style={{ color: '#9197C2', lineHeight: '1.8' }}>
              {insight.length > 300 ? insight.slice(0, 300) + '...' : insight}
            </p>
            {insight.length > 300 && (
              <button onClick={() => handleQuickAsk('详细分析今天的趋势')} className="text-xs mt-2 transition-all hover:brightness-110" style={{ color: '#6395FF' }}>
                完整分析 →
              </button>
            )}
          </div>
        </div>
      ) : null}

      {/* ⭐ 热门文章 Top 5 */}
      {topArticles.length > 0 ? (
        <div className="rounded-xl" style={{ background: '#1A1B33', border: '1px solid #2E2F4F', padding: '20px 18px' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3 flex items-center gap-2" style={{ color: '#9197C2' }}>
            <span className="text-base">⭐</span> 热门文章 Top {Math.min(5, topArticles.length)}
          </h3>
          <div className="space-y-3">
            {topArticles.slice(0, 5).map((a, i) => (
              <div key={a.id || a.url} onClick={() => onArticleClick(a.id)} className="flex items-start gap-3 cursor-pointer group transition-all">
                <span className="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold" style={{ background: i < 3 ? 'rgba(99,149,255,0.15)' : 'rgba(99,149,255,0.06)', color: '#6395FF' }}>
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs leading-relaxed transition-colors group-hover:text-accent line-clamp-2" style={{ color: '#E2E6F9' }}>
                    {a.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px]" style={{ color: '#6E739C' }}>{a.source_name}</span>
                    {a.published_at ? <span className="text-[10px]" style={{ color: '#6E739C' }}>· {a.published_at.slice(0, 10)}</span> : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* 📡 来源分布 */}
      {sources.length > 0 ? (
        <div className="rounded-xl" style={{ background: '#1A1B33', border: '1px solid #2E2F4F', padding: '20px 18px' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3 flex items-center gap-2" style={{ color: '#9197C2' }}>
            <span className="text-base">📡</span> 来源分布
          </h3>
          <div className="flex flex-wrap gap-2">
            {sources.map((s) => (
              <span key={s} className="px-3 py-1.5 text-xs rounded-lg transition-all" style={{ background: 'rgba(57,196,136,0.08)', color: '#39C488', border: '1px solid rgba(57,196,136,0.2)' }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
