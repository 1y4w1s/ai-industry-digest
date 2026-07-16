import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import CalendarHeatmap from '../components/CalendarHeatmap';
import ReadingTrends from '../components/ReadingTrends';


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
export default function ProfilePage() {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [trends, setTrends] = useState(null);
  const [editing, setEditing] = useState(false);
  const [nickInput, setNickInput] = useState('');
  const [saving, setSaving] = useState(false);

  const nickname = user?.user_metadata?.nickname || user?.email?.split('@')[0] || '用户';
  const initial = nickname[0].toUpperCase();

  useEffect(() => {
    const cached = localStorage.getItem('signal_stats');
    if (cached) { try { setStats(JSON.parse(cached)); setStatsLoading(false); } catch {} }
    api.getStats()
      .then((data) => { setStats(data); setStatsLoading(false); localStorage.setItem('signal_stats', JSON.stringify(data)); })
      .catch(() => { if (!cached) setStats(null); setStatsLoading(false); });
    api.getReadingTrends()
      .then((data) => setTrends(data))
      .catch(() => {});
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
    <div className="flex-1 flex flex-col min-h-0" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '28px', paddingBottom: '32px', maxWidth: '800px', margin: '0 auto' }}>
          {/* Avatar + Name */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-semibold mx-auto mb-3" style={{ background: 'var(--color-brass-bg)', color: 'var(--color-brass)' }}>
              {initial}
            </div>
            <div className="flex items-center justify-center gap-2">
              {editing ? (
                <div className="flex items-center gap-2">
                  <input value={nickInput} onChange={(e) => setNickInput(e.target.value)}
                    style={{ padding: '6px 10px', fontSize: '14px', borderRadius: '6px', border: '1px solid var(--color-border)', color: 'var(--color-text-body)', background: 'var(--color-bg-white)', outline: 'none', width: '160px' }}
                    autoFocus onKeyDown={(e) => { if (e.key === 'Enter') handleSaveNickname(); if (e.key === 'Escape') setEditing(false); }} />
                  <button onClick={handleSaveNickname} disabled={saving}
                    style={{ padding: '6px 8px', background: 'var(--color-brass)', border: 'none', borderRadius: '6px', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                    {saving ? '...' : <IconCheck />}
                  </button>
                  <button onClick={() => setEditing(false)}
                    style={{ padding: '6px 8px', background: 'none', border: '1px solid var(--color-border)', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', color: 'var(--color-text-muted)' }}>
                    <IconClose />
                  </button>
                </div>
              ) : (
                <>
                  <h1 style={{ fontFamily: "var(--font-display)", fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>
                    {nickname}
                  </h1>
                  <button onClick={handleStartEdit} style={{ padding: '4px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-label)', display: 'flex', alignItems: 'center' }}>
                    <IconEdit />
                  </button>
                </>
              )}
            </div>
            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px' }}>{user?.email}</p>
          </div>

          {/* Stats cards */}
          {statsLoading ? (
            <div className="flex gap-2 sm:gap-3 mb-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex-1 rounded p-4" style={{ background: 'var(--color-bg-off)' }}>
                  <div style={{ height: '12px', width: '60%', background: 'var(--color-border-light)', borderRadius: '2px', marginBottom: '8px' }} />
                  <div style={{ height: '24px', width: '40%', background: 'var(--color-border-light)', borderRadius: '2px' }} />
                </div>
              ))}
            </div>
          ) : stats ? (
            <div className="flex gap-2 sm:gap-3 mb-6">
              <div className="flex-1 rounded-lg p-3 sm:p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-brass)' }}><IconRead /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_read}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>已读文章</div>
              </div>
              <div className="flex-1 rounded-lg p-3 sm:p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div className="flex justify-center mb-2" style={{ color: 'var(--color-brass)' }}><IconStar /></div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_bookmarks}</div>
                 <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>收藏</div>
               </div>
               <div className="flex-1 rounded-lg p-3 sm:p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                 <div className="flex justify-center mb-2" style={{ color: 'var(--color-brass)' }}><IconStreak /></div>
                 <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.streak_days}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px' }}>连续天数</div>
              </div>
            </div>
          ) : null}

          {/* Calendar Heatmap */}
          {stats?.heatmap && <CalendarHeatmap heatmap={stats.heatmap} />}

          {/* Reading Trends */}
          {trends && <ReadingTrends trends={trends} />}

          {/* Source distribution */}
          {sourceEntries.length > 0 && (
            <div className="mb-6">
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 10 }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-title)' }}>
                常读来源
              </span>
              <span style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, var(--color-brass) 0%, var(--color-border-light) 100%)' }} />
            </div>
              <div className="space-y-2">
                {sourceEntries.map(([src, count]) => (
                  <div key={src} className="flex items-center gap-3">
                    <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-body)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{src}</span>
                    <div style={{ flex: 2, height: '6px', borderRadius: '3px', background: 'var(--color-border-light)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${(count / sourceTotal) * 100}%`, borderRadius: '3px', background: 'var(--color-brass)', transition: 'width 0.3s' }} />
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
              <svg width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><path d='M9 5l7 7-7 7' /></svg>
            </a>
            <a href="/history" style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }} className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconHistory /></span>
              <span style={{ flex: 1 }}>浏览历史</span>
              <svg width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><path d='M9 5l7 7-7 7' /></svg>
            </a>
            <a href="/settings" style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }} className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px', color: 'var(--color-text-muted)', display: 'flex' }}><IconSettings /></span>
              <span style={{ flex: 1 }}>设置</span>
              <svg width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><path d='M9 5l7 7-7 7' /></svg>
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
