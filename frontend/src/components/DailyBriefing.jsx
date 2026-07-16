import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function DailyBriefing({ date }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(Array(3).fill(false));
  const [copied, setCopied] = useState(false);

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

  const top = stories.slice(0, 3);
  const total = data?.total_stories || stories.length;

  const toggleExpand = (i) => {
    setExpanded((prev) => {
      const next = [...prev];
      next[i] = !next[i];
      return next;
    });
  };

  const share = () => {
    const link = `${window.location.origin}/digest/${date}`;
    const ok = () => { setCopied(true); setTimeout(() => setCopied(false), 2000); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(link).then(ok).catch(() => fallbackCopy(link, ok));
    } else {
      fallbackCopy(link, ok);
    }
  };

  const fallbackCopy = (text, ok) => {
    try {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy');
      document.body.removeChild(ta); ok();
    } catch { /* silent */ }
  };

  return (
    <section style={{
      marginBottom: 16,
    }}>
      {top.length > 0 && top[0]?.title && (
        <div style={{
          fontFamily: 'var(--font-display)',
          fontSize: '18px', fontWeight: 600,
          lineHeight: 1.3, letterSpacing: '-0.01em',
          color: 'var(--color-text-title)',
          margin: '0 0 4px',
        }}>
          {top[0].title}
        </div>
      )}

      <div className="space-y-2">
        {top.map((s, i) => {
          const lead = s.articles?.[0];
          const soWhat = lead?.so_what || null;
          const isExpanded = expanded[i];
          const shown = isExpanded ? s.articles : (s.articles || []).slice(0, 2);
          return (
            <div key={s.title || i}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                {s.entity && (
                  <span style={{
                    fontSize: '10px', fontWeight: 600, padding: '1px 7px',
                    borderRadius: 999, background: 'var(--color-brass-bg)',
                    color: 'var(--color-brass)', flexShrink: 0,
                  }}>{s.entity}</span>
                )}
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-title)', lineHeight: 1.4 }}>
                  {s.title}
                </span>
              </div>
              {s.summary && (
                <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', margin: '2px 0 0 0', lineHeight: 1.5 }}>
                  {s.summary}
                </p>
              )}
              {soWhat && (
                <div style={{
                  fontSize: '11px', lineHeight: 1.6, color: 'var(--color-text-muted)',
                  marginTop: 4, padding: '4px 8px',
                  background: 'var(--color-bg-off)', borderRadius: 4,
                }}>
                  编辑部观点：{soWhat}
                </div>
              )}
              {shown.length > 0 && (
                <ul style={{ listStyle: 'none', margin: '4px 0 0', paddingLeft: '14px' }}>
                  {shown.map((a, j) => (
                    <li key={a.url || j} style={{ fontSize: '12px', lineHeight: 1.6 }}>
                      <a href={a.url} target="_blank" rel="noreferrer"
                        style={{ color: 'var(--color-text-body)', textDecoration: 'none' }}
                        onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-brass)'}
                        onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-body)'}
                      >{a.title}</a>
                      {a.source_name && (
                        <span style={{ fontSize: '10px', color: 'var(--color-text-label)', marginLeft: 4 }}> · {a.source_name}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              {(s.articles?.length || 0) > 2 && (
                <button onClick={() => toggleExpand(i)}
                  style={{ fontSize: '11px', color: 'var(--color-brass)', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 0', marginLeft: 14 }}>
                  {isExpanded ? '收起' : `展开全部 ${(s.articles || []).length} 篇`}
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: '13px' }}>
        <button onClick={share}
          style={{ color: 'var(--color-text-body)', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 0', fontWeight: 500 }}>
          {copied ? '已复制链接' : '分享今日速览'}
        </button>
        {total > 3 && (
          <a href={`/digest/${date}`} target="_blank" rel="noreferrer"
            style={{ color: 'var(--color-brass)', textDecoration: 'none', fontWeight: 500 }}>
            查看完整简报
          </a>
        )}
      </div>
    </section>
  );
}
