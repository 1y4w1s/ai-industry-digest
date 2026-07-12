import { useState, useEffect } from 'react';
import { api } from '../api/client';

/**
 * 今日速览（每日速览首屏改造 · P0）
 * 在首页主内容列最顶部渲染「今日速览」hero，复用 /api/main-thread 的同一份
 * cluster_stories + so_what 数据（与侧栏 MainThreadPanel、公开页 DigestPage 同源）。
 * 纯前端组装，零新采集、零新接口、零新表。
 *
 * 降级策略（与 MainThreadPanel 一致）：
 *  - 加载中：返回 null，不占版面、不闪烁。
 *  - 空数据（stories.length === 0）：返回 null，首页照常显示文章列表。
 *  - 接口异常：catch 后视作空数据，静默隐藏。
 */
export default function DailyBriefing({ date }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
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
  // 加载中或无聚类结果时不占版面
  if (!loading && stories.length === 0) return null;

  const top = stories.slice(0, 3);
  const total = data?.total_stories || stories.length;

  const share = () => {
    const link = `${window.location.origin}/digest/${date}`;
    const ok = () => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(link).then(ok).catch(() => fallbackCopy(link, ok));
    } else {
      fallbackCopy(link, ok);
    }
  };

  const fallbackCopy = (text, ok) => {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      ok();
    } catch {
      /* 复制失败静默忽略，不影响其他功能 */
    }
  };

  return (
    <section
      style={{
        borderRadius: '8px',
        padding: '16px 20px',
        background: 'var(--color-bg-off)',
        border: '1px solid var(--color-border-light)',
        marginBottom: '20px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h2
          style={{
            fontFamily: "'Source Serif 4', Georgia, serif",
            fontSize: '16px',
            fontWeight: 700,
            color: 'var(--color-text-title)',
            margin: 0,
          }}
        >
          🧭 今日速览
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--color-text-label)' }}>
          事件聚类自动生成 · {date}
        </span>
      </div>

      <div className="space-y-4">
        {top.map((s, i) => {
          const lead = s.articles?.[0];
          const soWhat = lead?.so_what || null;
          const shown = expanded ? s.articles : (s.articles || []).slice(0, 3);
          return (
            <div key={s.title || i}>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-title)', lineHeight: 1.4 }}>
                {s.entity && (
                  <span
                    style={{
                      fontSize: '11px',
                      padding: '1px 8px',
                      borderRadius: '999px',
                      background: '#eef2ff',
                      color: '#4338ca',
                      marginRight: '6px',
                    }}
                  >
                    {s.entity}
                  </span>
                )}
                {s.title}
              </div>
              {s.summary && (
                <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', margin: '2px 0 0', lineHeight: 1.5 }}>
                  {s.summary}
                </p>
              )}
              {soWhat && (
                <div
                  style={{
                    fontSize: '12px',
                    lineHeight: 1.6,
                    color: '#92400e',
                    marginTop: '6px',
                    padding: '6px 10px',
                    background: 'rgba(146,64,14,0.06)',
                    borderRadius: '4px',
                  }}
                >
                  💡 编辑部观点：{soWhat}
                </div>
              )}
              <ul style={{ listStyle: 'none', margin: '6px 0 0', paddingLeft: 0 }} className="space-y-1">
                {shown.map((a, j) => (
                  <li key={a.url || j}>
                    <a
                      href={a.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontSize: '12px', color: 'var(--color-blue-link)', textDecoration: 'none' }}
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
              {(s.articles?.length || 0) > 3 && (
                <button
                  onClick={() => setExpanded((v) => !v)}
                  style={{
                    fontSize: '11px',
                    color: 'var(--color-text-muted)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '4px 0',
                  }}
                >
                  {expanded ? '收起' : `展开全部 ${(s.articles || []).length} 篇`}
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: '12px', marginTop: '14px', fontSize: '12px' }}>
        <button
          onClick={share}
          style={{
            color: 'var(--color-text-muted)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          {copied ? '已复制链接 ✓' : '分享今日速览'}
        </button>
        {total > 3 && (
          <a
            href={`/digest/${date}`}
            target="_blank"
            rel="noreferrer"
            style={{ color: 'var(--color-blue-link)', textDecoration: 'none' }}
          >
            查看完整简报 ↗
          </a>
        )}
      </div>
    </section>
  );
}
