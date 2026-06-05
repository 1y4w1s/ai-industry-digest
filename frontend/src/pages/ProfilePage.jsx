import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';

function Heatmap({ heatmap }) {
  if (!heatmap || Object.keys(heatmap).length === 0) return null;

  // Convert to array sorted by date, take last ~364 days
  const days = Object.entries(heatmap)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-364);

  // Group into weeks (each week is an array of 7 days)
  const weeks = [];
  let week = [];
  // Fill leading empty cells to align to Monday
  const first = new Date(days[0][0]);
  const startPad = (first.getDay() + 6) % 7; // Monday=0
  for (let i = 0; i < startPad; i++) week.push(null);

  for (const [, count] of days) {
    week.push(count);
    if (week.length === 7) { weeks.push(week); week = []; }
  }
  if (week.length > 0) weeks.push(week);

  const maxVal = Math.max(...days.map(([, c]) => c), 1);

  const getColor = (count) => {
    if (count === null || count === undefined) return 'transparent';
    if (count === 0) return 'var(--color-bg-hover)';
    const intensity = Math.min(count / maxVal, 1);
    if (intensity <= 0.25) return 'var(--color-success)';
    if (intensity <= 0.5) return '#27ae60';
    if (intensity <= 0.75) return '#1e8449';
    return '#145a32';
  };

  return (
    <div className="mb-6">
      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
        阅读热力图
      </div>
      <div className="flex gap-0.5 overflow-x-auto pb-2" style={{ minHeight: '80px' }}>
        {weeks.map((w, wi) => (
          <div key={wi} className="flex flex-col gap-0.5">
            {w.map((v, di) => (
              <div key={di} style={{
                width: '8px', height: '8px', borderRadius: '1px',
                background: getColor(v),
              }} title={v !== null ? `${v} 次阅读` : ''} />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-1 mt-1" style={{ fontSize: '9px', color: 'var(--color-text-label)' }}>
        <span>少</span>
        <div style={{ width: '8px', height: '8px', borderRadius: '1px', background: 'var(--color-bg-hover)' }} />
        <div style={{ width: '8px', height: '8px', borderRadius: '1px', background: 'var(--color-bg-hover)' }} />
        <div style={{ width: '8px', height: '8px', borderRadius: '1px', background: '#27ae60' }} />
        <div style={{ width: '8px', height: '8px', borderRadius: '1px', background: '#1e8449' }} />
        <div style={{ width: '8px', height: '8px', borderRadius: '1px', background: '#145a32' }} />
        <span>多</span>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [editingNickname, setEditingNickname] = useState(false);
  const [nicknameInput, setNicknameInput] = useState('');

  const nickname = user?.user_metadata?.nickname || user?.email?.split('@')[0] || '用户';
  const initial = nickname[0].toUpperCase();

  useEffect(() => {
    api.getStats()
      .then((data) => {
        setStats(data);
        setStatsLoading(false);
      })
      .catch(() => {
        setStats(null);
        setStatsLoading(false);
      });
  }, []);

  // Source distribution sorted by count
  const sourceEntries = stats?.source_distribution
    ? Object.entries(stats.source_distribution).sort((a, b) => b[1] - a[1]).slice(0, 6)
    : [];
  const sourceTotal = sourceEntries.reduce((s, [, c]) => s + c, 0);

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '28px', paddingBottom: '32px', maxWidth: '520px', margin: '0 auto' }}>
          {/* Avatar + Name */}
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-semibold mx-auto mb-3" style={{ background: 'var(--color-border-light)', color: 'var(--color-text-muted)' }}>
              {initial}
            </div>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: 'var(--fs-xl)', fontWeight: 700, color: 'var(--color-text-title)' }}>
              {nickname}
            </h1>
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
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>已读文章</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_read}</div>
              </div>
              <div className="flex-1 rounded p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>收藏</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.total_bookmarks}</div>
              </div>
              <div className="flex-1 rounded p-4 text-center" style={{ background: 'var(--color-bg-off)' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>连续天数</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-text-title)' }}>{stats.streak_days}</div>
              </div>
            </div>
          ) : null}

          {/* Heatmap */}
          {stats?.heatmap && <Heatmap heatmap={stats.heatmap} />}

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
              <span style={{ marginRight: '10px' }}>📑</span>
              <span style={{ flex: 1 }}>收藏的文章</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
            <a href="/history"
              style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }}
              className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px' }}>📖</span>
              <span style={{ flex: 1 }}>浏览历史</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
            <a href="/settings"
              style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: 'var(--color-text-title)', fontSize: 'var(--fs-sm)', transition: 'background 0.1s' }}
              className="hover:bg-[var(--color-bg-hover)]">
              <span style={{ marginRight: '10px' }}>⚙️</span>
              <span style={{ flex: 1 }}>设置</span>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)' }}>→</span>
            </a>
          </div>

          {/* Logout */}
          <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: '16px' }}>
            <button onClick={logout}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '12px 16px', borderRadius: '4px', border: 'none', background: 'none', cursor: 'pointer', fontSize: 'var(--fs-sm)', color: 'var(--color-high)', transition: 'background 0.1s' }}
              className="hover:bg-[var(--color-bg-hover)]">
              <span>🚪</span>
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
