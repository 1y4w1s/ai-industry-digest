export default function HeroArticle({ article, onSelect }) {
  return (
    <div className="hero-card mb-5" onClick={() => onSelect(article.id)}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#D4322E' }}>头条</span>
        <span className="text-[10px]" style={{ color: '#8C9096' }}>{article.source_name} · {article.published_at?.slice(0, 10)}</span>
      </div>
      <h2 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '18px', fontWeight: 700, color: '#1A1C1E', lineHeight: 1.35, marginBottom: '8px' }}>
        {article.title}
      </h2>
      {article.summary && (
        <p className="text-sm leading-relaxed line-clamp-2" style={{ color: '#2C2E32' }}>{article.summary}</p>
      )}
      {article.tags?.length > 0 && (
        <div className="flex gap-1.5 mt-2">
          {article.tags.map((t) => (
            <span key={t} className="px-2 py-0.5 text-[10px] rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{t}</span>
          ))}
        </div>
      )}
    </div>
  );
}
