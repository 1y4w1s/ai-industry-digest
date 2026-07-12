import { useEffect, useState } from 'react';

// 顶栏下方细线：表示当前页面滚动进度（Nielsen #1 系统状态可见）
// 0% 起点，100% 底部；requestAnimationFrame 节流；reduced-motion 时只显示不动画
export default function ScrollProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let raf = 0;
    const update = () => {
      const doc = document.documentElement;
      const scrollTop = window.scrollY || doc.scrollTop || 0;
      const max = (doc.scrollHeight - window.innerHeight) || 1;
      const p = Math.min(1, Math.max(0, scrollTop / max));
      setProgress(p);
    };
    const onScroll = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => { raf = 0; update(); });
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div
      role="progressbar"
      aria-label="页面阅读进度"
      aria-valuenow={Math.round(progress * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        height: 2,
        background: 'transparent',
        pointerEvents: 'none',
        zIndex: 1,
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${progress * 100}%`,
          background: 'var(--color-brand-ink)',
          transition: 'width 0.08s linear',
          willChange: 'width',
        }}
      />
    </div>
  );
}
