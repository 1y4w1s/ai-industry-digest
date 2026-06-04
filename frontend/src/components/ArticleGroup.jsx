import ArticleCard from './ArticleCard';

export default function ArticleGroup({ sourceName, articles, onSelectArticle }) {
  if (!articles || articles.length === 0) return null;

  const sorted = [...articles].sort(
    (a, b) => ({high:0,medium:1,low:2}[a._imp]||2) - ({high:0,medium:1,low:2}[b._imp]||2)
  );

  return (
    <div style={{ marginTop: '24px' }}>
      <div className="flex items-center pb-1.5 mb-1" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
        <span style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--color-text-title)' }}>{sourceName}</span>
        <span className="text-xs ml-auto" style={{ color: 'var(--color-text-label)' }}>{articles.length} 篇</span>
      </div>
      {sorted.map((a) => (
        <ArticleCard key={a.id || a.url} article={a} onSelect={onSelectArticle} variant="compact" />
      ))}
    </div>
  );
}
