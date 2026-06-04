export default function Pagination({ page, total, onChange }) {
  if (!total || total <= 1) return null;
  const pages = Array.from({ length: total }, (_, i) => i + 1);
  return (
    <div className="flex items-center justify-center gap-1 mt-6" style={{ fontSize: 'var(--fs-sm)' }}>
      {page > 1 && (
        <button onClick={() => onChange(page - 1)}
          style={{ padding: '4px 10px', background: 'none', border: '1px solid var(--color-border)', borderRadius: '4px', color: 'var(--color-text-body)', cursor: 'pointer' }}>
          上一页
        </button>
      )}
      {pages.map(p => (
        <button key={p} onClick={() => onChange(p)}
          style={{
            padding: '4px 10px',
            background: p === page ? 'var(--color-border-light)' : 'none',
            border: p === page ? '1px solid var(--color-border)' : '1px solid transparent',
            borderRadius: '4px',
            color: p === page ? 'var(--color-text-title)' : 'var(--color-text-body)',
            cursor: 'pointer',
            fontWeight: p === page ? 600 : 400,
          }}>
          {p}
        </button>
      ))}
      {page < total && (
        <button onClick={() => onChange(page + 1)}
          style={{ padding: '4px 10px', background: 'none', border: '1px solid var(--color-border)', borderRadius: '4px', color: 'var(--color-text-body)', cursor: 'pointer' }}>
          下一页
        </button>
      )}
    </div>
  );
}
