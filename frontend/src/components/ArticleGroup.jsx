import ArticleCard from './ArticleCard';

export default function ArticleGroup({ sourceName, articles, onSelectArticle, customOrder = null }) {
  if (!articles || articles.length === 0) return null;

  const orderIndex = customOrder
    ? new Map(customOrder.map((id, idx) => [id, idx]))
    : null;

  const sorted = [...articles].sort((a, b) => {
    if (orderIndex) {
      const ai = orderIndex.has(a.id) ? orderIndex.get(a.id) : Infinity;
      const bi = orderIndex.has(b.id) ? orderIndex.get(b.id) : Infinity;
      if (ai !== bi) return ai - bi;
    }
    const imp = { high: 0, medium: 1, low: 2 };
    return (imp[a._imp] ?? 2) - (imp[b._imp] ?? 2);
  });

  return (
    <div style={{ marginTop: '20px' }}>
      {/* 源名称 + 金色左边框 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ width: 3, height: 14, borderRadius: 2, background: 'var(--color-brass)', flexShrink: 0 }} />
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-title)', minWidth: 0 }}>{sourceName}</span>
        <span style={{ fontSize: '11px', color: 'var(--color-text-label)', flexShrink: 0 }}>{articles.length} 篇</span>
      </div>
      {sorted.map((a) => (
        <ArticleCard key={a.id || a.url} article={a} onSelect={onSelectArticle} variant="compact" />
      ))}
    </div>
  );
}
