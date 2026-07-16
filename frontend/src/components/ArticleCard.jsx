import { memo, useMemo } from 'react';
import DOMPurify from 'dompurify';

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
  const impColor = imp === 'high' ? 'var(--color-accent-coral)'
    : imp === 'medium' ? 'var(--color-brass)' : 'var(--color-text-label)';

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
    <button
      type="button"
      onClick={() => onSelect(article.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(article.id);
        }
      }}
      style={{
        width: '100%',
        textAlign: 'left',
        background: 'transparent',
        border: 'none',
        borderBottom: '1px solid var(--color-border)',
        cursor: 'pointer',
        padding: '12px 0',
        font: 'inherit',
        color: 'inherit',
        transition: 'background 0.15s',
        borderRadius: 4,
      }}
      aria-label={article.title}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-bg-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      {/* 重要性指示点 */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{
          width: 5, height: 5, borderRadius: '50%',
          background: impColor,
          flexShrink: 0, alignSelf: 'flex-start', marginTop: 6,
        }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <span style={{
            fontSize: '14px',
            color: 'var(--color-text-title)',
            fontWeight: imp === 'high' ? 500 : 400,
            lineHeight: 1.5,
            display: 'block',
          }} dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(titleHtml) }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2, fontSize: '12px', color: 'var(--color-text-label)' }}>
            <span>{article.source_name}</span>
            {article.published_at && <span>· {article.published_at.slice(0, 10)}</span>}
          </div>
        </div>
      </div>
    </button>
  );
}

export default memo(ArticleCard);
