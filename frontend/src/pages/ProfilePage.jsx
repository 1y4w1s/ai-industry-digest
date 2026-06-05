import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';

/* ── SVG Icons ───────────── */
const IconBookmark = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" />
  </svg>
);
const IconHistory = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
  </svg>
);
const IconSettings = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" /><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
  </svg>
);
const IconLogout = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
  </svg>
);
const IconArticle = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
  </svg>
);
const IconStar = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);
const IconFire = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 23c-3.866 0-7-3.134-7-7 0-3.866 3-9 7-13 4 4 7 9.134 7 13 0 3.866-3.134 7-7 7z" />
  </svg>
);
const IconEdit = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);
const IconCheck = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const IconClose = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

/* ── Monthly Calendar Heatmap ───────────── */
function MonthlyHeatmap({ heatmap }) {
  if (!heatmap || Object.keys(heatmap).length === 0) return null;

  // Group heatmap data by month
  const byMonth = {};
  for (const [dateStr, count] of Object.entries(heatmap)) {
    const monthKey = dateStr.slice(0, 7); // "2026-06"
    if (!byMonth[monthKey]) byMonth[monthKey] = {};
    byMonth[monthKey][parseInt(dateStr.slice(8))] = count;
  }

  const maxVal = Math.max(...Object.values(heatmap).map(Number), 1);
  const dayNames = ['一', '二', '三', '四', '五', '六', '日'];

  const getColor = (count) => {
    if (count === undefined || count === null) return 'transparent';
    if (count === 0) return 'var(--color-bg-hover)';
    const intensity = Math.min(count / maxVal, 1);
    if (intensity <= 0.25) return '#d4edda';
    if (intensity <= 0.5) return '#a3d9a5';
    if (intensity <= 0.75) return '#5cb85c';
    return '#2d7d2d';
  };

  // Only show current month
  const now = new Date();
  const currentMonthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const sortedMonths = byMonth[currentMonthKey] ? [currentMonthKey] : [];

  return (
    <div className="mb-6">
      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
        阅读热力图
      </div>
      <div className="flex flex-col gap-5">
        {sortedMonths.map((monthKey) => {
          const [year, month] = monthKey.split('-').map(Number);
          const daysInMonth = new Date(year, month, 0).getDate();
          const firstDay = (new Date(year, month - 1, 1).getDay() + 6) % 7; // Monday=0

          return (
            <div key={monthKey}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-title)', marginBottom: '6px' }}>
                {year} 年 {month} 月
              </div>
              <div>
                {/* Day of week headers */}
                <div className="flex gap-1 mb-1" style={{ fontSize: '9px', color: 'var(--color-text-label)' }}>
                  {dayNames.map((n) => (
                    <div key={n} style={{ width: '14px', textAlign: 'center' }}>{n}</div>
                  ))}
                </div>
                {/* Grid */}
                <div className="flex gap-1 flex-wrap" style={{ maxWidth: '14px * 7 + 6px * 6' }}>
                  {/* Leading empty cells */}
                  {Array.from({ length: firstDay }).map((_, i) => (
                    <div key={`empty-${i}`} style={{ width: '14px', height: '14px' }} />
                  ))}
                  {/* Day cells */}
                  {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
                    const count = byMonth[monthKey]?.[day];
                    return (
                      <div key={day}
                        style={{ width: '14px', height: '14px', borderRadius: '2px', background: getColor(count) }}
                        title={`${monthKey}-${String(day).padStart(2, '0')}: ${count ?? 0} 次阅读`}
                      />
                    );
                  })}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {/* Legend */}
      <div className="flex items-center gap-1 mt-3" style={{ fontSize: '9px', color: 'var(--color-text-label)' }}>
        <span>少</span>
        <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: 'var(--color-bg-hover)' }} />
        <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#d4edda' }} />
        <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#a3d9a5' }} />
        <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#5cb85c' }} />
        <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#2d7d2d' }} />
        <span>多</span>
      </div>
    </div>
  );
}

/* ── ProfilePage ───────────── */
export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [nickInput, setNickInput] = useState('');
  const [saving, setSaving] = useState(false);

  const nickname = user?.user_metadata?.nickname || user?.email?.split('@')[0] || '用户';
  const initial = nickname[0].toUpperCase();

  useEffect(() => {
    api.getStats()
      .then((data) => { setStats(data); setStatsLoading(false); })
      .catch(() => { setStats(null); setStatsLoading(false); });
  }, []);

  const sourceEntries = stats?.source_distribution
    ? Object.entries(stats.source_distribution).sort((a, b) => b[1] - a[1]).slice(0, 6)
    : [];
  const sourceTotal = sourceEntries.reduce((s, [, c]) => s + c, 0);

  const handleStartEdit = () => {
    setNickInput(nickname);
    setEditing(true);
  };

  const handleSaveNickname = async () => {
    if (!nickInput.trim() || nickInput === nickname) { setEditing(false); return; }
    setSaving(true);
    try {
      const { supabase } = await import('../lib/supabase');
      const { error } = await supabase.auth.updateUser({ data: { nickname: nickInput.trim() } });
      if (error) throw error;
      setEditing(false);
      window.location.reload();
    } catch (err) {
      alert('更新失败: ' + (err.message || '未知错误'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '28px', paddingBottom: '32px', maxWidth: '520px', margin: '0 auto' }}>
          {/* Avatar + Name */}
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-semibold mx-auto mb-3" style={{ background: 'var(--color-border-light)', color: 'var(--color-text-muted)' }}>
              {initial}
            </div>
            <div className="flex items-center justify-center gap-2">
              {editing ? (
                <div className="flex items-center gap-2">
                  <input
                    value={nickInput}
                    onChange={(e) => setNickInput(e.target.value)}
                    style={{
                      padding: '6px 10px', fontSize: 'var(--fs-base)', borderRadius: '4px',
                      border: '1px solid var(--color-border)', color: 'var(--color-text-body)',
                      background: 'var(--color-bg-white)', outline: 'none', width: '160px',
                    }}
                    autoFocus
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSaveNickname(); if (e.key === 'Escape') setEditing(false); }}
                  />
                  <button onClick={handleSaveNickname} disabled={saving}
                    style={{ padding: '6px 8px', background: 'var(--color-text-title)', border: 'none', borderRadius: '4px', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                    {saving ? '...' : <IconCheck />}
                  </button>
                  <button onClick={() => setEditing(false)}
                    style={{ padding: '6px 8px', background: 'none', border: '1px solid var(--color-border)', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', color: 'var(--color-text-muted)' }}>
                    <IconClose />
                  </button>
                </div>
              ) : (
                <>
                  <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: 'var(--fs-xl)', fontWeight: 700, color: 'var(--color-text-title)' }}>
                    {nickname}
                  </h1>
                  <button onClick={handleStartEdit}
                    style={{ padding: '4px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-label)', display: 'flex', alignItems: 'center' }}>
                    <IconEdit />
                  </button>
                </>
              )}
            </div>
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)', marginTop: '4px' }}>
              {user?.email}
            </p>
          </div>

          {/* Stats cards */}
          {statsLoading ? (
            <div className="flex gap-3 mb-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex-1 rounded p-4" style={{ background: 'var(--color-bg-off)' }}>
                  <div style={{ height: '12px', width: '60%', background: 'var(--color-border-light)', borderRadius: '2px', marginBottom: '8px' }} />
                  <div style={{ height: '24px', width: '40%', background: 'var(--color-border-light)', borderRadius: '2px' }} />
                </div>
              ))}
            </div>
          ) : stats ? (
            <div className="flex gap-3 mb-6">
              <div className="flex-1 rounded p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-text-muted)' }}><IconArticle /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_read}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>已读文章</div>
              </div>
              <div className="flex-1 rounded p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-text-muted)' }}><IconStar /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_bookmarks}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>收藏</div>
              </div>
              <div className="flex-1 rounded p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-text-muted)' }}><IconFire /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.streak_days}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>连续天数</div>
              </div>
            </div>
          ) : null}

          {/* Monthly Calendar Heatmap */}
          {stats?.heatmap && <MonthlyHeatmap heatmap={stats.heatmap} />}

          {/* Source distribution */}
          {sourceEntries.length > 0 && (
            <div className="mb-6">
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                常读来源
              </div>
              <div className="space-y-2">
                {sourceEntries.map(([src, count]) => (
                  <div key={src} className="flex items-center gap-3">
                    <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-body)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{src}</span>
                    <div style={{ flex: 2, height: '6px', borderRadius: '3px', background: 'var(--color-border-light)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${(count / sourceTotal) * 100}%`, borderRadius: '3px', background: 'var(--color-blue-link)', transition: 'width 0.3s' }} />
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-label)', flexShrink: 0, width: '24px', textAlign: 'right' }}>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick links */}
          <div className="space-y-1 mb-6" style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: '16px' }}>
            <a href="/bookmarks"
              style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }}
              className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconBookmark /></span>
              <span style={{ flex: 1 }}>收藏的文章</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
            <a href="/history"
              style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }}
              className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconHistory /></span>
              <span style={{ flex: 1 }}>浏览历史</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
            <a href="/settings"
              style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }}
              className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconSettings /></span>
              <span style={{ flex: 1 }}>设置</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
          </div>

          {/* Logout */}
          <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: '16px' }}>
            <button onClick={logout}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '12px 16px', borderRadius: '4px', border: 'none', background: 'none', cursor: 'pointer', fontSize: 'var(--fs-sm)', color: 'var(--color-high)', transition: 'background 0.1s' }}
              className="hover:bg-[var(--color-bg-hover)]">
              <IconLogout />
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
