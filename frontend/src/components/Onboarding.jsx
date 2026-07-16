import { useState, useEffect } from 'react';

/**
 * Onboarding · 首次访问引导（轻量级横幅版）
 * 页面顶部 banner，不遮挡主内容，一句话讲清 Signal 是什么。
 * 通过 localStorage 'signal.onboarded.v1' 标记。
 */
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
        background: 'linear-gradient(135deg, var(--color-brand-ink) 0%, #1a5a48 100%)',
        color: '#fff',
        padding: '12px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        flexWrap: 'wrap',
        animation: 'slideDown 0.3s var(--ease-spring)',
        fontSize: 14,
        lineHeight: 1.5,
      }}
    >
      <span style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
        🧠 Signal
      </span>
      <span style={{ opacity: 0.9 }}>
        每天 5 分钟的 AI 行业脉搏 — 编辑部精选 + 一句话观点
      </span>
      <kbd style={{
        fontFamily: 'var(--font-mono)', fontSize: 11,
        padding: '2px 7px', borderRadius: 4,
        background: 'rgba(255,255,255,0.15)',
        color: 'rgba(255,255,255,0.8)',
      }}>⌘K 搜索</kbd>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button
          onClick={dismiss}
          aria-label="不再显示引导"
          style={{
            fontSize: 12, color: 'rgba(255,255,255,0.7)',
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 6,
            padding: '4px 12px',
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.2)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
        >
          不再显示
        </button>
        <button
          onClick={dismiss}
          aria-label="关闭引导"
          style={{
            fontSize: 12, color: 'var(--color-brand-ink)',
            background: '#fff',
            border: 'none',
            borderRadius: 6,
            padding: '4px 14px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = '#e8f0ec'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; }}
        >
          知道了
        </button>
      </div>
    </div>
  );
}
