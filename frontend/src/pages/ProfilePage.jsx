import { useAuth } from '../context/AuthContext';

export default function ProfilePage({ onReadArticle }) {
  const { user, logout } = useAuth();

  const nickname = user?.user_metadata?.nickname || user?.email?.split('@')[0] || '用户';
  const initial = nickname[0].toUpperCase();

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '32px', paddingBottom: '32px', maxWidth: '480px', margin: '0 auto' }}>
          {/* Avatar + Name */}
          <div className="text-center mb-8">
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

          {/* Stats links */}
          <div className="space-y-1 mb-6">
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
          </div>

          {/* Actions */}
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
