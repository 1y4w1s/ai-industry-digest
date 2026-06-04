export default function Pagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  const pages = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, start + 4);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex justify-center gap-1 mt-6">
      <button
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        style={{
          padding: '6px 10px',
          fontSize: '12px',
          borderRadius: '4px',
          background: '#F0F1F2',
          color: '#686C72',
          border: 'none',
          cursor: page <= 1 ? 'not-allowed' : 'pointer',
          opacity: page <= 1 ? 0.4 : 1,
        }}
      >
        ←
      </button>
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          style={{
            padding: '6px 10px',
            fontSize: '12px',
            borderRadius: '4px',
            background: p === page ? '#1A1C1E' : '#F0F1F2',
            color: p === page ? '#fff' : '#686C72',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          {p}
        </button>
      ))}
      <button
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        style={{
          padding: '6px 10px',
          fontSize: '12px',
          borderRadius: '4px',
          background: '#F0F1F2',
          color: '#686C72',
          border: 'none',
          cursor: page >= totalPages ? 'not-allowed' : 'pointer',
          opacity: page >= totalPages ? 0.4 : 1,
        }}
      >
        →
      </button>
    </div>
  );
}
