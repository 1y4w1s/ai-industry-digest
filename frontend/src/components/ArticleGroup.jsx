import ArticleCard from './ArticleCard';

export default function ArticleGroup({ sourceName, articles, onSelectArticle, customOrder = null }) {
  if (!articles || articles.length === 0) return null;

  // customOrder: Array<article.id> — 按该顺序排（命中排前，不命中保持相对原序）
  const orderIndex = customOrder
    ? new Map(customOrder.map((id, idx) => [id, idx]))
    : null;

  const sorted = [...articles].sort((a, b) => {
    // 1. customOrder 优先（推荐排序）
    if (orderIndex) {
      const ai = orderIndex.has(a.id) ? orderIndex.get(a.id) : Infinity;
      const bi = orderIndex.has(b.id) ? orderIndex.get(b.id) : Infinity;
      if (ai !== bi) return ai - bi;
    }
    // 2. fallback: importance
    const imp = { high: 0, medium: 1, low: 2 };
    return (imp[a._imp] ?? 2) - (imp[b._imp] ?? 2);
  });

  return (
    <div style={{ marginTop: '24px' }}>
      <div className="flex items-center pb-1.5 mb-1" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
        <span style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--color-text-title)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, minWidth: 0 }}>{sourceName}</span>
        <span className="text-xs flex-shrink-0 ml-2" style={{ color: 'var(--color-text-label)' }}>{articles.length} 篇</span>
      </div>
      {sorted.map((a) => (
        <ArticleCard key={a.id || a.url} article={a} onSelect={onSelectArticle} variant="compact" />
      ))}
    </div>
  );
}
