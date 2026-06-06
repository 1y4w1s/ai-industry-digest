import { useEffect, useRef } from 'react';
import { api } from '../api/client';

export default function KnowledgePreviewDrawer({ open, onClose, doc, data, loading }) {
  const contentRef = useRef(null);

  // 自动滚动到顶部
  useEffect(() => {
    if (open && contentRef.current) {
      contentRef.current.scrollTop = 0;
    }
  }, [open, data]);

  return (
    <>
      {/* 遮罩 */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)',
          zIndex: 90, opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none',
          transition: 'opacity 0.3s ease',
        }}
      />

      {/* 抽屉 */}
      <div
        style={{
          position: 'fixed', top: 0, right: 0, bottom: 0,
          width: 'min(640px, 90vw)',
          background: 'var(--color-bg-white)',
          borderLeft: '1px solid var(--color-border-light)',
          zIndex: 100, display: 'flex', flexDirection: 'column',
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.3s cubic-bezier(0.4,0,0.2,1)',
        }}
      >
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={onClose}
              style={{ padding: '4px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', borderRadius: '4px', flexShrink: 0 }}
              className="hover:bg-[var(--color-bg-hover)]"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="min-w-0">
              <h2 className="text-base font-semibold truncate" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: 'var(--color-text-title)' }}>
                {doc?.name || ''}
              </h2>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                {data?.file_type ? data.file_type.toUpperCase() : ''}
                {data?.content ? ` · ${data.content.length} 字` : ''}
              </p>
            </div>
          </div>
          {doc && (
            <button
              onClick={() => api.kb.download(doc.id)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '6px 14px', fontSize: 'var(--fs-sm)',
                background: 'transparent', border: '1px solid var(--color-border)',
                borderRadius: '4px', cursor: 'pointer', color: 'var(--color-text-muted)',
                flexShrink: 0, transition: 'all 0.12s',
              }}
              className="hover:bg-[var(--color-bg-hover)]"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              <span>下载</span>
            </button>
          )}
        </div>

        {/* 内容 */}
        <div
          ref={contentRef}
          className="flex-1 overflow-auto"
          style={{ padding: '24px 32px', fontSize: '14px', lineHeight: '1.8', color: 'var(--color-text-body)' }}
        >
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
              </div>
            </div>
          ) : data?.content ? (
            <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {data.content}
            </div>
          ) : (
            <div className="flex items-center justify-center py-20">
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>无法加载文档内容</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
