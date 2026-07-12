import { useState, useEffect } from 'react';
import { api } from '../api/client';

// 今日 GitHub 推荐（P3-home）：首页卡片，复用后端 /api/github-agents。
// 设计语言与公开页区块一致：Fraunces 标题 + JetBrains Mono 数字/仓库名 + 暖白卡。

function fmtStars(n) {
  if (typeof n !== 'number') return '0';
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return `${n}`;
}

function fmtDate(s) {
  if (!s) return '';
  const d = new Date(s);
  if (isNaN(d)) return '';
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

export default function GitHubAgentsCard({ range = 'week', minStars = 100, sort = 'stars', limit = 8 }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .getGitHubAgents({ range, min_stars: minStars, sort, limit })
      .then((data) => {
        if (cancelled) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
        setError(false);
      })
      .catch(() => {
        if (cancelled) return;
        setItems([]);
        setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [range, minStars, sort, limit]);

  return (
    <section
      style={{
        background: 'var(--color-bg-off)',
        border: '1px solid var(--color-border-light)',
        borderRadius: '14px',
        padding: '20px 22px',
        marginBottom: '24px',
      }}
    >
      {/* 栏目标题：Fraunces 衬线展示体，品牌墨绿 */}
      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '22px',
          fontWeight: 600,
          color: 'var(--color-text-title)',
          margin: '0 0 2px',
          lineHeight: 1.2,
        }}
      >
        今日 GitHub 推荐
      </h2>
      <p style={{ fontSize: '12px', color: 'var(--color-text-label)', margin: '0 0 14px' }}>
        按 Star 数降序 · ⚡ 为近期创建且日增迅速的新项目
      </p>

      {loading && (
        <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', padding: '8px 0' }}>
          加载中...
        </div>
      )}

      {!loading && error && (
        <div style={{ fontSize: '13px', color: 'var(--color-text-label)', padding: '8px 0' }}>
          暂时无法获取 GitHub 数据，请稍后重试。
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div style={{ fontSize: '13px', color: 'var(--color-text-label)', padding: '8px 0' }}>
          暂无匹配项目，可放宽时间范围或降低最低 Star 后重试。
        </div>
      )}

      {!loading && items.length > 0 && (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {items.map((it) => {
            const name = it.full_name || it.name || '';
            return (
              <li
                key={it.url || name}
                style={{
                  borderTop: '1px solid var(--color-border-light)',
                  paddingTop: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
                  <a
                    href={it.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: 'var(--color-text-title)',
                      textDecoration: 'none',
                    }}
                  >
                    {name}
                  </a>
                  {it.is_rising_star && (
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 600,
                        color: '#B8860B',
                        border: '1px solid rgba(184,134,11,0.4)',
                        borderRadius: '4px',
                        padding: '1px 5px',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      ⚡ 新星
                    </span>
                  )}
                </div>

                {it.description && (
                  <p
                    style={{
                      fontSize: '13px',
                      lineHeight: 1.6,
                      color: 'var(--color-text-muted)',
                      margin: '4px 0 6px',
                    }}
                  >
                    {it.description}
                  </p>
                )}

                <div
                  style={{
                    display: 'flex',
                    gap: '14px',
                    fontSize: '12px',
                    color: 'var(--color-text-label)',
                    flexWrap: 'wrap',
                  }}
                >
                  <span style={{ fontFamily: 'var(--font-mono)' }}>★ {fmtStars(it.stars)}</span>
                  {it.language && <span>{it.language}</span>}
                  <span>更新于 {fmtDate(it.pushed_at)}</span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
