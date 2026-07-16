import { useState, useEffect } from 'react';

const STORAGE_KEY = 'signal.onboarded.v1';

function getOnboarded() {
  try { return localStorage.getItem(STORAGE_KEY) === '1'; } catch { return true; }
}
function setOnboarded() {
  try { localStorage.setItem(STORAGE_KEY, '1'); } catch { /* quota / private */ }
}

export default function Onboarding() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!getOnboarded()) {
      const t = setTimeout(() => setOpen(true), 600);
      return () => clearTimeout(t);
    }
  }, []);

  const dismiss = () => { setOnboarded(); setOpen(false); };

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="首次使用引导"
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(26, 26, 26, 0.55)',
        backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
        display: 'grid', placeItems: 'center',
        padding: 16,
        animation: 'fadeIn 0.25s var(--ease)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) dismiss(); }}
      onKeyDown={(e) => { if (e.key === 'Escape') dismiss(); }}
    >
      <div style={{
        width: '100%', maxWidth: 400,
        background: 'var(--color-bg-white)',
        borderRadius: 16,
        boxShadow: '0 20px 60px rgba(0,0,0,0.20), 0 4px 16px rgba(0,0,0,0.08)',
        padding: '28px 28px 24px',
        animation: 'slideInUp 0.3s var(--ease-spring)',
        textAlign: 'center',
      }}>
        {/* 🧠 图标 */}
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: 'var(--color-brass)',
          color: '#fff',
          display: 'grid', placeItems: 'center',
          fontSize: 20,
          margin: '0 auto 16px',
        }}>
          🧠
        </div>

        {/* 标题 */}
        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 18, fontWeight: 600,
          lineHeight: 1.3, letterSpacing: '-0.01em',
          color: 'var(--color-text-title)',
          margin: '0 0 8px',
        }}>
          æä¹¾
        </h2>

        {/* 一句话介绍 */}
        <p style={{
          fontSize: 14, lineHeight: 1.6,
          color: 'var(--color-text-body)',
          margin: '0 0 20px',
        }}>
          每天 5 分钟的 AI 行业脉搏 — 编辑部精选 + 一句话观点
        </p>

        {/* 知道了按钮 */}
        <button
          onClick={dismiss}
          style={{
            height: 38, padding: '0 24px',
            background: 'var(--color-brass)',
            color: '#fff',
            border: 'none', borderRadius: 10,
            fontSize: 14, fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s var(--ease)',
            boxShadow: '0 1px 2px rgba(15,76,58,0.3), 0 2px 8px rgba(15,76,58,0.15)',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-brand-ink-2)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-brass)'; }}
        >
          知道了
        </button>
      </div>
    </div>
  );
}
