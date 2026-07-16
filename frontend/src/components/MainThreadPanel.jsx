import { useState, useEffect } from 'react';
import { api } from '../api/client';

/**
 * 今日主线（改造计划 §2.1）
 * 侧边栏展示聚类主线 + 挂文，金色左边框强调。
 */
export default function MainThreadPanel({ date }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!date) return undefined;
    let cancelled = false;
    setLoading(true);
    api.getMainThread(date)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => { if (!cancelled) setData({ stories: [] }); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [date]);

  const stories = (data && data.stories) || [];
  if (!loading && stories.length === 0) return null;

  return (
    <div style={{
      display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap',
      marginBottom: 16, paddingBottom: 12,
      borderBottom: '1px solid var(--color-border-light)',
    }}>
      <span style={{ width: 3, height: 14, borderRadius: 2, background: 'var(--color-brass)', flexShrink: 0 }} />
      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-title)', flexShrink: 0 }}>
        今日主线
      </span>
      {loading ? (
        <span style={{ fontSize: '11px', color: 'var(--color-text-label)' }}>加载中...</span>
      ) : (
        stories.map((s, i) => (
          <span key={i} style={{
            fontSize: '12px', color: 'var(--color-text-body)',
            display: 'inline-flex', alignItems: 'center', gap: 4,
          }}>
            {s.entity && (
              <span style={{
                fontSize: '9px', fontWeight: 600, padding: '1px 6px',
                borderRadius: 999, background: 'var(--color-brass-bg)',
                color: 'var(--color-brass)',
              }}>{s.entity}</span>
            )}
            <span>{s.title}</span>
            {i < stories.length - 1 && <span style={{ color: 'var(--color-border)', marginLeft: 2 }}>/</span>}
          </span>
        ))
      )}
    </div>
  );
}
