import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * KeyboardShortcuts · 快捷键 cheatsheet（impeccable P1-2）
 * 按 ? 唤起（输入框内除外）。
 * 列出所有全局快捷键 + 导航键 1-6 跳转主要页面。
 */
const SHORTCUTS = [
  { keys: ['⌘', 'K'], label: '打开搜索', section: '全局' },
  { keys: ['?'], label: '显示本帮助', section: '全局' },
  { keys: ['Esc'], label: '关闭弹窗 / 退出搜索', section: '全局' },
  { keys: ['G', 'H'], label: '回首页（今日日报）', section: '导航' },
  { keys: ['G', 'A'], label: '日报归档', section: '导航' },
  { keys: ['G', 'B'], label: '我的收藏', section: '导航' },
  { keys: ['G', 'S'], label: '搜索页', section: '导航' },
  { keys: ['G', 'P'], label: '设置', section: '导航' },
  { keys: ['J'], label: '下一篇文章', section: '阅读' },
  { keys: ['K'], label: '上一篇文章', section: '阅读' },
  { keys: ['T'], label: '回到顶部', section: '阅读' },
];

function KeyBadge({ children }) {
  return (
    <kbd style={{
      fontFamily: 'var(--font-mono)', fontSize: 11,
      minWidth: 22, height: 22,
      padding: '0 6px',
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--color-bg-white)',
      border: '1px solid var(--color-border)',
      borderRadius: 5,
      color: 'var(--color-text-muted)',
      boxShadow: '0 1px 0 var(--color-border-light)',
    }}>{children}</kbd>
  );
}

function KeyCombo({ keys }) {
  return (
    <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
      {keys.map((k, i) => (
        <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <KeyBadge>{k}</KeyBadge>
          {i < keys.length - 1 && <span style={{ fontSize: 10, color: 'var(--color-text-label)' }}>+</span>}
        </span>
      ))}
    </span>
  );
}

export default function KeyboardShortcuts() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    let lastKey = null;
    let lastTime = 0;

    const isInput = () => {
      const el = document.activeElement;
      if (!el) return false;
      const tag = el.tagName;
      return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable;
    };

    const handler = (e) => {
      // ? 唤起（不在输入框时）
      if (e.key === '?' && !isInput()) {
        e.preventDefault();
        setOpen(true);
        return;
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
        return;
      }

      // 导航快捷键：G + X
      const now = Date.now();
      if (lastKey === 'g' && now - lastTime < 1000 && !isInput()) {
        const map = { h: '/', a: '/archive', b: '/bookmarks', s: '/search', p: '/settings' };
        const target = map[e.key.toLowerCase()];
        if (target) {
          e.preventDefault();
          navigate(target);
          lastKey = null;
          return;
        }
      }
      if (e.key.toLowerCase() === 'g' && !isInput()) {
        lastKey = 'g';
        lastTime = now;
      } else if (!isInput()) {
        lastKey = null;
      }
    };

    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, navigate]);

  if (!open) return null;

  // 按 section 分组
  const sections = ['全局', '导航', '阅读'];
  const bySection = Object.fromEntries(sections.map((s) => [s, []]));
  SHORTCUTS.forEach((sc) => { bySection[sc.section]?.push(sc); });

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="kbd-title"
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(26, 26, 26, 0.55)',
        backdropFilter: 'blur(4px)',
        display: 'grid', placeItems: 'center',
        padding: 16,
        animation: 'fadeIn 0.2s var(--ease)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}
    >
      <div style={{
        width: '100%', maxWidth: 560,
        maxHeight: '85vh', overflowY: 'auto',
        background: 'var(--color-bg-white)',
        borderRadius: 16,
        boxShadow: '0 20px 60px rgba(0,0,0,0.20), 0 4px 16px rgba(0,0,0,0.08)',
        padding: '28px 32px',
        animation: 'slideInUp 0.3s var(--ease-spring)',
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 4 }}>
          <h2 id="kbd-title" style={{
            fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 600,
            color: 'var(--color-text-title)', margin: 0,
            letterSpacing: '-0.01em',
          }}>键盘快捷键</h2>
          <button
            onClick={() => setOpen(false)}
            aria-label="关闭"
            style={{
              fontSize: 12, color: 'var(--color-text-muted)',
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '4px 8px', borderRadius: 4,
            }}
          >Esc 关闭</button>
        </div>
        <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: '4px 0 20px' }}>
          在 Signal 里用键盘就能完成大部分操作。试试看？
        </p>

        {sections.map((sec) => bySection[sec].length > 0 && (
          <div key={sec} style={{ marginBottom: 18 }}>
            <div style={{
              fontSize: 10, fontWeight: 600, letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--color-text-label)',
              marginBottom: 8, paddingBottom: 4,
              borderBottom: '1px solid var(--color-border-light)',
            }}>{sec}</div>
            <div style={{ display: 'grid', gap: 8 }}>
              {bySection[sec].map((sc, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '6px 0',
                }}>
                  <span style={{ fontSize: 13, color: 'var(--color-text-body)' }}>{sc.label}</span>
                  <KeyCombo keys={sc.keys} />
                </div>
              ))}
            </div>
          </div>
        ))}

        <div style={{
          marginTop: 16, paddingTop: 12,
          borderTop: '1px solid var(--color-border-light)',
          fontSize: 11, color: 'var(--color-text-label)',
        }}>
          提示：快捷键在输入框内自动失效，避免误触。
        </div>
      </div>
    </div>
  );
}
