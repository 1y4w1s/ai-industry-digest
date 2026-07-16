/**
 * SkeletonCard — 骨架屏卡片
 * 用于文章列表加载时显示灰色占位块
 */
export default function SkeletonCard() {
  return (
    <div style={{
      padding: '16px 0',
      borderBottom: '1px solid var(--color-border-light)',
      animation: 'pulse 1.5s ease-in-out infinite',
    }}>
      <div style={{ height: 14, width: '35%', background: 'var(--color-border-light)', borderRadius: 4, marginBottom: 10 }} />
      <div style={{ height: 18, width: '75%', background: 'var(--color-border-light)', borderRadius: 4, marginBottom: 8 }} />
      <div style={{ height: 13, width: '60%', background: 'var(--color-border-light)', borderRadius: 4, marginBottom: 6 }} />
      <div style={{ height: 13, width: '45%', background: 'var(--color-border-light)', borderRadius: 4 }} />
    </div>
  );
}
