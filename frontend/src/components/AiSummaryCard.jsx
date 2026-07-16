/**
 * AiSummaryCard — AI 精读摘要卡片
 * 在文章阅读页展示 AI 总结、重要性理由、标签
 */
export default function AiSummaryCard({ summary, importanceReason, tags }) {
  if (!summary) return null;

  return (
    <div className="no-print" style={{ background: 'var(--color-bg-off)', borderRadius: '4px', padding: '16px', marginBottom: '24px' }}>
      <h3 className="font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>AI 精读</h3>
      <div className="text-sm leading-relaxed" style={{ color: 'var(--color-text-body)' }}>{summary}</div>
      {importanceReason && (
        <div className="mt-2 text-xs italic" style={{ color: 'var(--color-text-label)' }}>{importanceReason}</div>
      )}
      {tags?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {tags.map((t) => (
            <span key={t} className="px-2 py-0.5 text-xs rounded" style={{ background: 'var(--color-border-light)', color: 'var(--color-text-muted)' }}>{t}</span>
          ))}
        </div>
      )}
    </div>
  );
}
