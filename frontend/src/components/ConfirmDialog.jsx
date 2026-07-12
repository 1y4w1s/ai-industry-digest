import { useEffect, useRef } from 'react';

/**
 * ConfirmDialog · 删除/危险操作二次确认（impeccable P1-3）
 * 替代 window.confirm / alert — 支持自定义文案、危险按钮变体、自动聚焦、Esc 取消。
 */
export default function ConfirmDialog({
  open,
  title,
  description,
  confirmText = '确认删除',
  cancelText = '取消',
  danger = true,
  onConfirm,
  onCancel,
}) {
  const cancelRef = useRef(null);
  const confirmRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    // 默认聚焦在取消按钮（防误触危险操作）
    cancelRef.current?.focus();

    const handler = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); onCancel?.(); }
      if (e.key === 'Enter' && document.activeElement === confirmRef.current) {
        e.preventDefault();
        onConfirm?.();
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onCancel, onConfirm]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
      aria-describedby="confirm-desc"
      style={{
        position: 'fixed', inset: 0, zIndex: 150,
        background: 'rgba(26, 26, 26, 0.45)',
        backdropFilter: 'blur(3px)',
        display: 'grid', placeItems: 'center',
        padding: 16,
        animation: 'fadeIn 0.18s var(--ease)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onCancel?.(); }}
    >
      <div style={{
        width: '100%', maxWidth: 400,
        background: 'var(--color-bg-white)',
        borderRadius: 12,
        boxShadow: '0 16px 48px rgba(0,0,0,0.18), 0 4px 12px rgba(0,0,0,0.06)',
        padding: '24px 24px 20px',
        animation: 'slideInUp 0.25s var(--ease-spring)',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, marginBottom: 16 }}>
          <div aria-hidden="true" style={{
            width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
            background: danger ? 'var(--status-err-bg)' : 'var(--color-accent-amber-bg)',
            display: 'grid', placeItems: 'center',
          }}>
            {danger ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--status-err)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6M10 11v6M14 11v6" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-amber)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <circle cx="12" cy="16" r="0.5" fill="currentColor" />
              </svg>
            )}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 id="confirm-title" style={{
              fontSize: 15, fontWeight: 600,
              color: 'var(--color-text-title)',
              margin: 0, marginBottom: 6,
              lineHeight: 1.4,
            }}>{title}</h3>
            {description && (
              <p id="confirm-desc" style={{
                fontSize: 13, lineHeight: 1.55,
                color: 'var(--color-text-muted)',
                margin: 0,
              }}>{description}</p>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button
            ref={cancelRef}
            onClick={onCancel}
            style={{
              height: 34, padding: '0 14px',
              background: 'var(--color-bg-off)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 7,
              fontSize: 13, fontWeight: 500,
              color: 'var(--color-text-body)',
              cursor: 'pointer',
            }}
          >
            {cancelText}
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            style={{
              height: 34, padding: '0 14px',
              background: danger ? 'var(--status-err)' : 'var(--color-brand-ink)',
              color: '#fff',
              border: 'none', borderRadius: 7,
              fontSize: 13, fontWeight: 600,
              cursor: 'pointer',
              boxShadow: danger
                ? '0 1px 2px rgba(178,58,44,0.3), 0 2px 8px rgba(178,58,44,0.15)'
                : '0 1px 2px rgba(15,76,58,0.3), 0 2px 8px rgba(15,76,58,0.15)',
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
