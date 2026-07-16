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
      borderLeft: '3px solid var(--color-brass)',
      padding: '0 0 0 14px',
      marginBottom: 24,
    }}>
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: '13px', fontWeight: 600,
        color: 'var(--color-text-title)',
        marginBottom: 12,
      }}>
        今日主线
      </h3>
      {loading ? (
        <div style={{ height: 60, background: 'var(--color-bg-hover)', borderRadius: 6, opacity: 0.5 }} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {stories.map((s, i) => (
            <div key={i}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                {s.entity && (
                  <span style={{
                    fontSize: '10px', fontWeight: 600, padding: '1px 7px',
                    borderRadius: 999, background: 'var(--color-brass-bg)',
                    color: 'var(--color-brass)',
                  }}>{s.entity}</span>
                )}
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-title)', lineHeight: 1.4 }}>
                  {s.title}
                </span>
              </div>
              {(s.articles || []).slice(0, 4).map((a, j) => (
                <div key={j} style={{ fontSize: '12px', color: 'var(--color-text-muted)', lineHeight: 1.5, paddingLeft: 2 }}>
                  <a href={a.url} target="_blank" rel="noreferrer"
                    style={{ color: 'var(--color-text-body)', textDecoration: 'none', transition: 'color 0.15s' }}
                    onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-brass)'}
                    onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-body)'}
                  >{a.title}</a>
                  {a.source_name && <span style={{ color: 'var(--color-text-label)' }}> · {a.source_name}</span>}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
