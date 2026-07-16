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
      role="alert"
      aria-label="首次使用引导"
      style={{
        position: 'relative',
        zIndex: 100,
        background: 'var(--color-bg-off)',
        borderBottom: '1px solid var(--color-border-light)',
        display: 'flex',
        justifyContent: 'center',
        animation: 'slideDown 0.3s var(--ease-spring)',
        userSelect: 'none',
      }}
    >
      <div style={{
        width: '100%', maxWidth: 1200,
        height: 40,
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '0 20px',
        fontSize: 13, lineHeight: 1,
      }}>
        {/* 左侧品牌色竖条 */}
        <div style={{
          width: 3, height: 24, borderRadius: 2, flexShrink: 0,
          background: 'var(--color-brand-ink)',
        }} />

        {/* 🧠 Signal */}
        <span style={{
          fontWeight: 600, color: 'var(--color-text-title)',
          whiteSpace: 'nowrap', flexShrink: 0,
        }}>
          🧠 Signal
        </span>

        {/* 描述文字 */}
        <span style={{
          color: 'var(--color-text-muted)',
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          flex: '0 1 auto', minWidth: 0,
        }}>
          每天 5 分钟的 AI 行业脉搏 — 编辑部精选 + 一句话观点
        </span>

        {/* ⌘K 标签 */}
        <kbd style={{
          fontFamily: 'var(--font-mono)', fontSize: 10,
          padding: '2px 6px', borderRadius: 4,
          background: 'var(--color-bg-white)',
          border: '1px solid var(--color-border-light)',
          color: 'var(--color-text-label)',
          flexShrink: 0,
        }}>⌘K 搜索</kbd>

        {/* 操作按钮 — 紧跟内容 */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 4,
          flexShrink: 0,
        }}>
          <button
            onClick={dismiss}
            style={{
              height: 26, padding: '0 12px',
              background: 'var(--color-brand-ink)',
              color: '#fff',
              border: 'none', borderRadius: 6,
              fontSize: 12, fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s',
              lineHeight: 1,
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-brand-ink-2)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-brand-ink)'; }}
          >
            知道了
          </button>

          <button
            onClick={dismiss}
            aria-label="关闭"
            style={{
              width: 26, height: 26,
              display: 'grid', placeItems: 'center',
              background: 'none', border: 'none', borderRadius: 6,
              color: 'var(--color-text-label)',
              cursor: 'pointer',
              fontSize: 15,
              transition: 'all 0.15s',
              lineHeight: 1,
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-bg-hover)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}
