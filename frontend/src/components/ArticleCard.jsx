import { memo, useMemo } from 'react';

/* Highlight keyword in text, wrapping matches in <mark> tags */
function highlightText(text, keyword) {
  if (!keyword || !text) return text;
  try {
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === keyword.toLowerCase()
        ? `<mark>${part}</mark>`
        : part
    ).join('');
  } catch {
    return text;
  }
}

function ArticleCard({ article, onSelect, variant = 'compact', keyword }) {
  const imp = article._imp || article.importance || '';

  const impClass = imp === 'high' ? 'imp-high'
    : imp === 'medium' ? 'imp-medium' : 'imp-low';

  const text = useMemo(() => {
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
  }, [article.raw_content, article.summary, variant]);

  const titleHtml = useMemo(() => highlightText(article.title, keyword), [article.title, keyword]);
  const textHtml = useMemo(() => highlightText(text, keyword), [text, keyword]);

  return (
    <div
      className="article-item"
      onClick={() => onSelect(article.id)}
      style={{ padding: variant === 'detailed' ? '8px 0' : '6px 0' }}
    >
      <div className={impClass}>
        <span className="text-sm leading-relaxed" style={{
          color: 'var(--color-text-title)',
          fontWeight: imp === 'high' ? 500 : 400,
          display: 'block',
          lineHeight: '1.4',
        }}
          dangerouslySetInnerHTML={{ __html: titleHtml }}
        />
        <div className="flex items-center gap-2 mt-0.5" style={{ color: 'var(--color-text-label)', fontSize: '11px' }}>
          <span>{article.source_name}</span>
          {article.published_at && <span>· {article.published_at.slice(0, 10)}</span>}
        </div>
        {textHtml && (
          <p className="text-xs mt-1 leading-relaxed line-clamp-2" style={{ color: 'var(--color-text-muted)', lineHeight: '1.6' }}
            dangerouslySetInnerHTML={{ __html: textHtml }}
          />
        )}
      </div>
    </div>
  );
}

export default memo(ArticleCard);
