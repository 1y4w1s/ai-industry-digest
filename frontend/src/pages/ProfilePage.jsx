import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';

/* ── SVG Icons (outline style) ───────────── */
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
    <circle cx="12" cy="12" r="3" /><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);
const IconLogout = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
  </svg>
);
const IconRead = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 19.5A2.5 2.5 0 016.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" /><line x1="8" y1="7" x2="16" y2="7" /><line x1="8" y1="11" x2="14" y2="11" />
  </svg>
);
const IconStar = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);
const IconStreak = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
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

/* ── Calendar-style Heatmap ───────────── */
function CalendarHeatmap({ heatmap }) {
  if (!heatmap || Object.keys(heatmap).length === 0) return null;

  const byMonth = {};
  for (const [dateStr, count] of Object.entries(heatmap)) {
    const monthKey = dateStr.slice(0, 7);
    if (!byMonth[monthKey]) byMonth[monthKey] = {};
    byMonth[monthKey][parseInt(dateStr.slice(8))] = count;
  }

  const maxVal = Math.max(...Object.values(heatmap).map(Number), 1);
  const dayHeaders = ['一', '二', '三', '四', '五', '六', '日'];
  const cellSize = 28;

  const bg = (count) => {
    if (!count) return 'var(--color-bg-hover)';
    const i = Math.min(count / maxVal, 1);
    if (i <= 0.25) return '#d4edda';
    if (i <= 0.5) return '#a3d9a5';
    if (i <= 0.75) return '#5cb85c';
    return '#2d7d2d';
  };

  const now = new Date();
  const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  if (!byMonth[monthKey]) return null;

  const [year, month] = monthKey.split('-').map(Number);
  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDay = (new Date(year, month - 1, 1).getDay() + 6) % 7;
  const today = now.getDate();

  // Build calendar rows
  const rows = [];
  let row = new Array(firstDay).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    if (d > today) { row.push(null); } else { row.push(byMonth[monthKey]?.[d] ?? 0); }
    if (row.length === 7) { rows.push(row); row = []; }
  }
  if (row.length > 0) { while (row.length < 7) row.push(null); rows.push(row); }

  return (
    <div className="mb-6">
      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
        阅读热力图
      </div>
      <div style={{ border: '1px solid var(--color-border-light)', borderRadius: '6px', padding: '12px', background: 'var(--color-bg-white)' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-title)', marginBottom: '8px' }}>
          {year} 年 {month} 月
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {dayHeaders.map((h) => (
                <th key={h} style={{ width: `${100 / 7}%`, padding: '4px 0', fontSize: '10px', fontWeight: 400, color: 'var(--color-text-label)', textAlign: 'center' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((week, wi) => (
              <tr key={wi}>
                {week.map((val, di) => {
                  const dayNum = wi * 7 + di - firstDay + 1;
                  const cellIsToday = dayNum === today && dayNum > 0 && dayNum <= daysInMonth;
                  return (
                    <td key={di} style={{ padding: '2px', textAlign: 'center' }}>
                      {val !== null ? (
                        <div style={{
                          width: `${cellSize}px`, height: `${cellSize}px`, margin: '0 auto',
                          borderRadius: '4px', background: bg(val),
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '11px', fontWeight: cellIsToday ? 700 : 400,
                          color: val > 0 ? 'white' : 'var(--color-text-body)',
                          border: cellIsToday ? '2px solid var(--color-text-title)' : 'none',
                        }}>
                          {dayNum}
                        </div>
                      ) : null}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex items-center gap-1 mt-2 justify-end" style={{ fontSize: '9px', color: 'var(--color-text-label)' }}>
          <span>少</span>
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: 'var(--color-bg-hover)' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#d4edda' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#a3d9a5' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#5cb85c' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#2d7d2d' }} />
          <span>多</span>
        </div>
      </div>
    </div>
  );
}

/* ── ProfilePage ───────────── */
export default function ProfilePage() {
  const { user, logout } = useAuth();
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
                  <input value={nickInput} onChange={(e) => setNickInput(e.target.value)}
                    style={{ padding: '6px 10px', fontSize: 'var(--fs-base)', borderRadius: '4px', border: '1px solid var(--color-border)', color: 'var(--color-text-body)', background: 'var(--color-bg-white)', outline: 'none', width: '160px' }}
                    autoFocus onKeyDown={(e) => { if (e.key === 'Enter') handleSaveNickname(); if (e.key === 'Escape') setEditing(false); }} />
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
                  <button onClick={handleStartEdit} style={{ padding: '4px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-label)', display: 'flex', alignItems: 'center' }}>
                    <IconEdit />
                  </button>
                </>
              )}
            </div>
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)', marginTop: '4px' }}>{user?.email}</p>
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
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-text-muted)' }}><IconRead /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_read}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>已读文章</div>
              </div>
              <div className="flex-1 rounded p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-text-muted)' }}><IconStar /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_bookmarks}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>收藏</div>
              </div>
              <div className="flex-1 rounded p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-text-muted)' }}><IconStreak /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.streak_days}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>连续天数</div>
              </div>
            </div>
          ) : null}

          {/* Calendar Heatmap */}
          {stats?.heatmap && <CalendarHeatmap heatmap={stats.heatmap} />}

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
            <a href="/bookmarks" style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }} className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconBookmark /></span>
              <span style={{ flex: 1 }}>收藏的文章</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
            <a href="/history" style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }} className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconHistory /></span>
              <span style={{ flex: 1 }}>浏览历史</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
            <a href="/settings" style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }} className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconSettings /></span>
              <span style={{ flex: 1 }}>设置</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
          </div>

          {/* Logout */}
          <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: '16px' }}>
            <button onClick={logout} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '12px 16px', borderRadius: '4px', border: 'none', background: 'none', cursor: 'pointer', fontSize: 'var(--fs-sm)', color: 'var(--color-high)', transition: 'background 0.1s' }} className="hover:bg-[var(--color-bg-hover)]">
              <IconLogout />
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
