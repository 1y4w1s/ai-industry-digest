export default function ArticleCard({ article, onSelect, variant = 'compact' }) {
  const imp = article._imp || article.importance || '';

  const impClass = imp === 'high' ? 'imp-high'
    : imp === 'medium' ? 'imp-medium' : 'imp-low';

  // Build excerpt from summary or raw_content
  const excerpt = () => {
    if (variant === 'detailed' && article.summary) {
      return article.summary;
    }
    if (article.raw_content && article.raw_content.length > 10) {
      const clean = article.raw_content
        .replace(/<[^>]+>/g, '')
        .replace(/&nbsp;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      return clean.length > 100 ? clean.slice(0, 100) + '...' : clean;
    }
    return article.summary || '';
  };

  const text = excerpt();

  return (
    <div
      className="article-item"
      onClick={() => onSelect(article.id)}
      style={{ padding: variant === 'detailed' ? '8px 0' : '6px 0' }}
    >
      <div className={impClass}>
        <span className="text-sm leading-relaxed" style={{
          color: '#1A1C1E',
          fontWeight: imp === 'high' ? 500 : 400,
          display: 'block',
          lineHeight: '1.4',
        }}>
          {article.title}
        </span>
        <div className="flex items-center gap-2 mt-0.5" style={{ color: '#8C9096', fontSize: '11px' }}>
          <span>{article.source_name}</span>
          {article.published_at && <span>· {article.published_at.slice(0, 10)}</span>}
        </div>
        {text && (
          <p className="text-xs mt-1 leading-relaxed line-clamp-2" style={{ color: '#686C72', lineHeight: '1.6' }}>
            {text}
          </p>
        )}
      </div>
    </div>
  );
}
