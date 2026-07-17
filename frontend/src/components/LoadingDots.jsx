export default function LoadingDots({ width = 2, height = 2, gap = 1.5, minHeight = '60vh' }) {
  const size = { width: `${width*4}px`, height: `${height*4}px` };
  return (
    <div className="flex items-center justify-center" style={{ minHeight }}>
      <div className="flex" style={{ gap: `${gap*4}px` }}>
        <span className="rounded-full animate-bounce" style={{ ...size, background: 'var(--color-text-label)', animationDelay: '0ms' }} />
        <span className="rounded-full animate-bounce" style={{ ...size, background: 'var(--color-text-label)', animationDelay: '150ms' }} />
        <span className="rounded-full animate-bounce" style={{ ...size, background: 'var(--color-text-label)', animationDelay: '300ms' }} />
      </div>
    </div>
  );
}
