export default function ScrollToTopButton({ visible, onClick }) {
  if (!visible) return null;

  return (
    <button onClick={onClick}
      style={{
        position: 'fixed', bottom: '24px', right: '24px', zIndex: 50,
        width: '36px', height: '36px', borderRadius: '50%',
        background: 'var(--color-bg-white)', border: '1px solid var(--color-border)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.10)', cursor: 'pointer',
        display: 'grid', placeItems: 'center',
        color: 'var(--color-text-muted)', fontSize: '16px',
        transition: 'all 0.15s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.10)'; }}
      aria-label="回到顶部"
    >
      ↑
    </button>
  );
}
