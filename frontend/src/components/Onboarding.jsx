import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Onboarding · 首次访问引导（impeccable P1-1）
 * 展示 ⌘K 搜索、侧栏导航、DailyBriefing 编辑部速览含义。
 * 通过 localStorage 'signal.onboarded.v1' 标记。
 * "不再显示" 选项 = 永久跳过。
 */
const STORAGE_KEY = 'signal.onboarded.v1';

function getOnboarded() {
  try { return localStorage.getItem(STORAGE_KEY) === '1'; } catch { return true; }
}
function setOnboarded() {
  try { localStorage.setItem(STORAGE_KEY, '1'); } catch { /* quota / private */ }
}

function ShortcutKey({ children }) {
  return (
    <kbd style={{
      fontFamily: 'var(--font-mono)', fontSize: 11,
      padding: '2px 7px',
      background: 'var(--color-bg-white)',
      border: '1px solid var(--color-border)',
      borderRadius: 4,
      color: 'var(--color-text-muted)',
      boxShadow: '0 1px 0 var(--color-border-light)',
      display: 'inline-block',
      lineHeight: 1.4,
    }}>{children}</kbd>
  );
}

export default function Onboarding() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    if (!getOnboarded()) {
      // 短暂延迟确保页面稳定
      const t = setTimeout(() => setOpen(true), 600);
      return () => clearTimeout(t);
    }
  }, []);

  const finish = () => { setOnboarded(); setOpen(false); };
  const skip = () => { setOnboarded(); setOpen(false); };

  if (!open) return null;

  const steps = [
    {
      eyebrow: '欢迎使用 Signal',
      title: '每天 5 分钟的 AI 行业脉搏',
      body: 'Signal 由「编辑部」从全球 AI 新闻里挑出最值得读的，配上一句话观点。',
      cta: '开始',
    },
    {
      eyebrow: '🧭 今日速览',
      title: '首页最上面是今天的「主线」',
      body: '我们用事件聚类引擎把 100+ 条新闻归成 3~4 条主线，每条都有编辑部的看法（so-what）。',
      cta: '看懂了',
    },
    {
      eyebrow: '⌘ 全键盘',
      title: '试试这些快捷键',
      body: (
        <div style={{ display: 'grid', gap: 10, marginTop: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: 'var(--color-text-body)' }}>打开搜索</span>
            <ShortcutKey>⌘ K</ShortcutKey>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: 'var(--color-text-body)' }}>显示所有快捷键</span>
            <ShortcutKey>?</ShortcutKey>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: 'var(--color-text-body)' }}>关闭弹窗</span>
            <ShortcutKey>Esc</ShortcutKey>
          </div>
        </div>
      ),
      cta: '好的',
    },
  ];

  const s = steps[step];
  const isLast = step === steps.length - 1;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="onb-title"
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(26, 26, 26, 0.55)',
        backdropFilter: 'blur(4px)',
        display: 'grid', placeItems: 'center',
        padding: 16,
        animation: 'fadeIn 0.2s var(--ease)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) skip(); }}
      onKeyDown={(e) => { if (e.key === 'Escape') skip(); }}
    >
      <div style={{
        width: '100%', maxWidth: 480,
        background: 'var(--color-bg-white)',
        borderRadius: 16,
        boxShadow: '0 20px 60px rgba(0,0,0,0.20), 0 4px 16px rgba(0,0,0,0.08)',
        padding: '32px 32px 24px',
        animation: 'slideInUp 0.3s var(--ease-spring)',
      }}>
        {/* Step indicator */}
        <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
          {steps.map((_, i) => (
            <span
              key={i}
              aria-hidden="true"
              style={{
                width: i === step ? 20 : 6, height: 6, borderRadius: 3,
                background: i === step ? 'var(--color-brand-ink)' : 'var(--color-border-light)',
                transition: 'all 0.3s var(--ease)',
              }}
            />
          ))}
        </div>

        <div style={{
          fontSize: 11, fontWeight: 600, letterSpacing: '0.14em',
          textTransform: 'uppercase',
          color: 'var(--color-brand-ink)',
          marginBottom: 8,
        }}>{s.eyebrow}</div>

        <h2 id="onb-title" style={{
          fontFamily: 'var(--font-display)',
          fontSize: 22, fontWeight: 600,
          lineHeight: 1.25, letterSpacing: '-0.015em',
          color: 'var(--color-text-title)',
          margin: '0 0 12px',
        }}>{s.title}</h2>

        <div style={{
          fontSize: 14, lineHeight: 1.6,
          color: 'var(--color-text-body)',
          marginBottom: 24,
        }}>{s.body}</div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <button
            onClick={skip}
            style={{
              fontSize: 13, color: 'var(--color-text-muted)',
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '8px 12px',
            }}
          >
            不再显示
          </button>
          <div style={{ display: 'flex', gap: 8 }}>
            {step > 0 && (
              <button
                onClick={() => setStep(step - 1)}
                style={{
                  height: 36, padding: '0 16px',
                  background: 'var(--color-bg-off)',
                  border: '1px solid var(--color-border-light)',
                  borderRadius: 8,
                  fontSize: 13, fontWeight: 500,
                  color: 'var(--color-text-body)',
                  cursor: 'pointer',
                }}
              >
                上一步
              </button>
            )}
            <button
              onClick={isLast ? finish : () => setStep(step + 1)}
              style={{
                height: 36, padding: '0 18px',
                background: 'var(--color-brand-ink)',
                color: '#fff',
                border: 'none', borderRadius: 8,
                fontSize: 13, fontWeight: 600,
                cursor: 'pointer',
                boxShadow: '0 1px 2px rgba(15,76,58,0.3), 0 2px 8px rgba(15,76,58,0.15)',
                transition: 'all 0.15s var(--ease)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-brand-ink-2)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-brand-ink)'; }}
            >
              {s.cta} {isLast ? '→' : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
