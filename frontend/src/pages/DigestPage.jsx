import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';

/**
 * 公开简报页（改造计划 §2.3）
 * 路由：/digest/:date
 * 纯静态只读，无需登录。数据同源：今日主线经 /api/main-thread（cluster_stories），
 * 文章经 /api/reports/:date（含 so_what 观点层）——与邮件简报同口径。
 *
 * 说明：直接以 URL 访问 /digest/YYYY-MM-DD 时，由后端 public_digest 路由返回
 * 带完整 SEO meta 的服务器渲染 HTML（利于搜索引擎索引）；本站内点击进入时，
 * 由本组件做客户端只读渲染（同源数据 + 同排版思路）。
 */
export default function DigestPage() {
  const { date } = useParams();
  const navigate = useNavigate();
  const [mainThread, setMainThread] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.allSettled([
      api.getMainThread(date).catch(() => null),
      api.getReport(date).catch(() => null),
    ]).then(([mt, rep]) => {
      if (cancelled) return;
      setMainThread(mt.status === 'fulfilled' ? mt.value : null);
      setReport(rep.status === 'fulfilled' ? rep.value : null);
      setLoading(false);
    });

    return () => { cancelled = true; };
  }, [date]);

  const ranked = (() => {
    const arts = report?.articles || {};
    return [...(arts.high || []), ...(arts.medium || []), ...(arts.low || [])].slice(0, 8);
  })();

  const stories = mainThread?.stories || [];

  return (
    <div className="flex-1 flex flex-col min-h-0" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-8 py-6" style={{ maxWidth: '720px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <button onClick={() => navigate('/')} style={{ fontSize: '12px', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>
              ← 返回首页
            </button>
            <a href={`/digest/${date}`} target="_blank" rel="noopener noreferrer" style={{ fontSize: '12px', color: 'var(--color-text-muted)', textDecoration: 'none' }}>
              在独立公开页打开 ↗
            </a>
          </div>

          <h1 style={{ fontFamily: "var(--font-display)", fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)', marginBottom: '4px' }}>
            Signal · 每日 AI 情报简报
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '24px' }}>
            {date} · 公开归档页（无需订阅即可阅读）
          </p>

          {loading ? (
            <div className="text-center py-12">
              <div className="flex gap-1.5 justify-center mb-3">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
              </div>
              <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>加载中...</span>
            </div>
          ) : error ? (
            <div style={{ padding: '24px', borderRadius: '8px', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', fontSize: '14px' }}>
              内容暂时无法加载，请稍后重试。
            </div>
          ) : (
            <>
              {/* 概览 */}
              <p style={{ fontSize: '14px', lineHeight: 1.7, color: 'var(--color-text-body)', margin: '0 0 20px' }}>
                {report?.summary_insight || mainThread?.summary_insight || '今日暂无概览。'}
              </p>

              {/* 今日主线（事件聚类，与邮件同源） */}
              <section style={{ marginBottom: '28px' }}>
                <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-text-title)', margin: '0 0 4px' }}>🧭 今日主线</h2>
                <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', margin: '0 0 10px' }}>
                  {stories.length ? '事件聚类自动生成 · 同一事件的多篇报道已合并' : '（暂无可聚类信号，显示热度 Top 候选）'}
                </p>
                {stories.length ? (
                  <div>
                    {stories.map((s, i) => (
                      <div key={i} style={{ marginBottom: '14px' }}>
                        <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-title)', marginBottom: '2px' }}>
                          {s.entity && (
                            <span style={{ fontSize: '11px', padding: '1px 8px', borderRadius: '999px', background: '#eef2ff', color: '#4338ca', marginRight: '6px' }}>
                              {s.entity}
                            </span>
                          )}
                          {s.title}
                        </div>
                        <ul style={{ margin: '2px 0 0', paddingLeft: '18px' }}>
                          {(s.articles || []).slice(0, 6).map((a, j) => (
                            <li key={j} style={{ fontSize: '13px', lineHeight: 1.6, color: 'var(--color-text-body)', marginBottom: '3px' }}>
                              <a href={a.url || '#'} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-blue-link)', textDecoration: 'none' }}>
                                {a.title || '（无标题）'}
                              </a>
                              <span style={{ color: 'var(--color-text-muted)' }}> · {a.source_name || ''}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                ) : (
                  <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--color-text-body)' }}>
                    {(mainThread?.main_thread || report?.main_thread || []).map((b, i) => (
                      <li key={i} style={{ fontSize: '13px', lineHeight: 1.6, marginBottom: '4px' }}>{b}</li>
                    ))}
                  </ul>
                )}
              </section>

              {/* 今日精选 Top N（含 so_what 观点层） */}
              <section>
                <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-text-title)', margin: '12px 0' }}>
                  📌 今日精选（Top {ranked.length}）
                </h2>
                {ranked.length ? (
                  ranked.map((a, i) => {
                    const imp = (a.importance || 'low').toLowerCase();
                    const badge = { high: ['#dc2626', '高'], medium: ['#d97706', '中'] }[imp] || ['#6b7280', '低'];
                    return (
                      <div key={a.id || a.url || i} style={{ border: '1px solid var(--color-border-light)', borderRadius: '10px', padding: '16px', marginBottom: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', color: '#fff', background: badge[0] }}>{badge[1]}</span>
                          <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{a.source_name || '未知来源'}{a.published_at ? ` · ${a.published_at.slice(5, 16).replace('T', ' ')}` : ''}</span>
                        </div>
                        <a href={a.url || '#'} target="_blank" rel="noopener noreferrer" style={{ fontSize: '15px', fontWeight: 600, color: '#111827', textDecoration: 'none' }}>
                          {a.title || '（无标题）'}
                        </a>
                        {a.summary && <p style={{ fontSize: '13px', lineHeight: 1.6, color: 'var(--color-text-body)', margin: '8px 0 0' }}>{a.summary}</p>}
                        {a.so_what ? (
                          <div style={{ marginTop: '10px', padding: '10px 12px', background: '#fffbeb', borderLeft: '3px solid #f59e0b', borderRadius: '4px' }}>
                            <div style={{ fontSize: '12px', fontWeight: 600, color: '#b45309', marginBottom: '2px' }}>💡 So What / 对你意味着什么</div>
                            <div style={{ fontSize: '13px', lineHeight: 1.6, color: '#92400e' }}>{a.so_what}</div>
                          </div>
                        ) : (
                          <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--color-text-muted)' }}>（暂无观点层）</div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: 0 }}>今日暂无收录内容。</p>
                )}
              </section>

              <div style={{ borderTop: '1px solid var(--color-border-light)', marginTop: '24px', paddingTop: '16px', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                本页内容来自已公开的每日简报，可自由阅读、分享。
                {' '}<Link to="/archive" style={{ color: 'var(--color-blue-link)', textDecoration: 'none' }}>往期归档</Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
