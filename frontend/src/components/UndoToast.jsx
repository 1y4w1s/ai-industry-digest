import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { createPortal } from 'react-dom';

/**
 * UndoToast · 可撤销操作提示（impeccable P1-4）
 * 用法：在 useUndoToast() 拿到 showUndoToast(message, onUndo)；
 * 显示 5s 内可撤销；进度条倒计时；hover 暂停倒计时。
 */
const Ctx = createContext(null);

export function UndoToastProvider({ children }) {
  const [toast, setToast] = useState(null);
  // toast: { id, message, onUndo, expiresAt, durationMs, paused }

  const dismiss = useCallback(() => setToast(null), []);

  const showUndoToast = useCallback((message, onUndo, durationMs = 5000) => {
    const id = Date.now() + Math.random();
    setToast({ id, message, onUndo, durationMs, expiresAt: Date.now() + durationMs, paused: false });
  }, []);

  // 倒计时
  useEffect(() => {
    if (!toast) return undefined;
    let raf = null;
    let last = Date.now();
    const tick = () => {
      if (!toast || toast.paused) { raf = requestAnimationFrame(tick); return; }
      const now = Date.now();
      if (now >= toast.expiresAt) {
        dismiss();
        return;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { if (raf) cancelAnimationFrame(raf); };
  }, [toast, dismiss]);

  const handleUndo = () => {
    if (toast?.onUndo) toast.onUndo();
    dismiss();
  };

  return (
    <Ctx.Provider value={showUndoToast}>
      {children}
      {toast && createPortal(
        <div
          role="status"
          aria-live="polite"
          onMouseEnter={() => setToast((t) => t ? { ...t, paused: true } : t)}
          onMouseLeave={() => setToast((t) => t ? { ...t, paused: false, expiresAt: Date.now() + Math.max(0, t.expiresAt - Date.now()) } : t)}
          style={{
            position: 'fixed', left: '50%', bottom: 80,
            transform: 'translateX(-50%)',
            zIndex: 180,
            background: 'var(--color-text-title)',
            color: '#fff',
            padding: '12px 16px',
            borderRadius: 10,
            boxShadow: '0 12px 32px rgba(0,0,0,0.20), 0 4px 12px rgba(0,0,0,0.10)',
            display: 'flex', alignItems: 'center', gap: 12,
            minWidth: 280, maxWidth: 480,
            fontSize: 13, fontWeight: 500,
            animation: 'slideInUp 0.25s var(--ease-spring)',
          }}
        >
          <span style={{ flex: 1 }}>{toast.message}</span>
          <button
            onClick={handleUndo}
            style={{
              background: 'none', border: 'none',
              color: 'var(--color-brass)',
              fontSize: 13, fontWeight: 700,
              cursor: 'pointer', padding: '4px 8px',
              borderRadius: 4,
              transition: 'background 0.15s var(--ease)',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
          >
            撤销
          </button>
          <button
            onClick={dismiss}
            aria-label="关闭"
            style={{
              background: 'none', border: 'none',
              color: 'rgba(255,255,255,0.6)',
              fontSize: 18, lineHeight: 1,
              cursor: 'pointer', padding: 0,
              width: 20, height: 20,
              display: 'grid', placeItems: 'center',
            }}
          >×</button>
          {/* 进度条 */}
          <div
            aria-hidden="true"
            style={{
              position: 'absolute', left: 0, bottom: 0,
              height: 2, borderRadius: '0 0 10px 10px',
              background: 'var(--color-brass)',
              width: '100%',
              transformOrigin: 'left',
              animation: `undo-progress ${toast.durationMs}ms linear forwards`,
              animationPlayState: toast.paused ? 'paused' : 'running',
            }}
          />
          <style>{`
            @keyframes undo-progress {
              from { transform: scaleX(1); }
              to   { transform: scaleX(0); }
            }
          `}</style>
        </div>,
        document.body,
      )}
    </Ctx.Provider>
  );
}

export function useUndoToast() {
  return useContext(Ctx);
}
