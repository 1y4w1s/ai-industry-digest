export default function SidePanel({ keywords = [], insight = '', topArticles = [], onArticleClick, onAskAI, onTagFilter, activeTags = [] }) {
  const handleTagClick = (k) => {
    if (onTagFilter) onTagFilter(k);
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {keywords.length > 0 && (
        <div style={{ borderRadius: '4px', padding: '16px', background: 'var(--color-bg-off)' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>
            <span style={{ marginRight: '6px' }}>🔥</span> 今日热点
          </h3>
          <div className="flex flex-wrap gap-2">
            {keywords.map((k) => {
              const isActive = activeTags.includes(k);
              return (
                <span
                  key={k}
                  onClick={() => handleTagClick(k)}
                  style={{
                    padding: '4px 12px',
                    fontSize: 'var(--fs-sm)',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    background: isActive ? 'var(--color-border)' : 'var(--color-border-light)',
                    color: isActive ? 'var(--color-text-title)' : 'var(--color-text-body)',
                    border: isActive ? '1px solid var(--color-border-bold)' : '1px solid transparent',
                  }}
                >
                  {k}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {insight && (
        <div style={{ borderRadius: '4px', padding: '16px', background: 'var(--color-bg-off)' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>
            <span style={{ marginRight: '6px' }}>📊</span> 趋势速览
          </h3>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-body)', lineHeight: '1.7' }}>
            {insight.length > 200 ? insight.slice(0, 200) + '...' : insight}
          </p>
        </div>
      )}

      {topArticles.length > 0 && (
        <div style={{ borderRadius: '4px', padding: '16px', background: 'var(--color-bg-off)' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>
            <span style={{ marginRight: '6px' }}>⭐</span> Top {Math.min(5, topArticles.length)}
          </h3>
          <div className="space-y-2.5">
            {topArticles.slice(0, 5).map((a, i) => (
              <div key={a.id || a.url} onClick={() => onArticleClick(a.id)} className="flex items-start gap-2.5 cursor-pointer group transition-all">
                <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-[10px] font-bold rounded" style={{ background: i < 3 ? 'var(--color-border-light)' : 'var(--color-bg-hover)', color: 'var(--color-text-muted)' }}>{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs leading-relaxed group-hover:text-blue-link transition-colors" style={{ color: 'var(--color-text-title)' }}>{a.title}</p>
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--color-text-label)' }}>{a.source_name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {keywords.length > 0 && (
        <div style={{ borderRadius: '4px', padding: '16px', background: 'var(--color-bg-off)' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>
            <span style={{ marginRight: '6px' }}>📡</span> 来源分布
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {['arXiv', '量子位', '36氪', '机器之心'].map((s) => (
              <span key={s} className="px-2 py-1 text-xs rounded" style={{ background: 'var(--color-border-light)', color: 'var(--color-text-muted)' }}>{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
