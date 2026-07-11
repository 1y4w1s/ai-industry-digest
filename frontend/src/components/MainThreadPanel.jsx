import { useState, useEffect } from 'react';
import { api } from '../api/client';

/**
 * 今日主线（改造计划 §2.1）
 * 复用 /api/main-thread 的同一份 cluster 数据，在侧边栏展示聚类主线 + 挂文。
 * 与邮件简报同口径；接口不可达时静默隐藏（优雅降级）。
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
  // 加载中或无聚类结果时不占版面
  if (!loading && stories.length === 0) return null;

  return (
    <div style={{ borderRadius: '4px', padding: '16px', background: 'var(--color-bg-off)' }}>
      <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>
        <span style={{ marginRight: '6px' }}>🧭</span> 今日主线
      </h3>
      <div className="space-y-3">
        {stories.map((s, i) => (
          <div key={s.title || i}>
            <div className="flex items-center gap-2 flex-wrap">
              {s.entity && (
                <span
                  style={{
                    fontSize: '10px',
                    padding: '1px 7px',
                    borderRadius: '999px',
                    background: 'var(--color-border-light)',
                    color: 'var(--color-text-muted)',
                  }}
                >
                  {s.entity}
                </span>
              )}
              <span className="text-xs font-semibold" style={{ color: 'var(--color-text-title)' }}>
                {s.title}
              </span>
            </div>
            <ul style={{ listStyle: 'none', margin: '4px 0 0', paddingLeft: 0 }} className="space-y-1">
              {(s.articles || []).slice(0, 5).map((a, j) => (
                <li key={a.url || j}>
                  <a
                    href={a.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs leading-relaxed hover:text-blue-link transition-colors"
                    style={{ color: 'var(--color-text-body)', textDecoration: 'none' }}
                  >
                    {a.title}
                  </a>
                  {a.source_name && (
                    <span style={{ fontSize: '10px', color: 'var(--color-text-label)', marginLeft: '4px' }}>
                      · {a.source_name}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
