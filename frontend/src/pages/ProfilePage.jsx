import { useAuth } from '../context/AuthContext';

export default function ProfilePage({ onReadArticle }) {
  const { user, logout } = useAuth();

  return (
    <div className="h-full flex flex-col" style={{ background: '#FBFCFD' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '32px', paddingBottom: '32px', maxWidth: '480px', margin: '0 auto' }}>
          {/* Avatar + Name */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-semibold mx-auto mb-3" style={{ background: '#E8EAED', color: '#686C72' }}>
              {(user?.nickname || 'U')[0].toUpperCase()}
            </div>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '20px', fontWeight: 700, color: '#1A1C1E' }}>
              {user?.nickname || '用户'}
            </h1>
            {user?.created_at && (
              <p style={{ fontSize: '12px', color: '#686C72', marginTop: '4px' }}>
                加入时间: {user.created_at.slice(0, 10)}
              </p>
            )}
          </div>

          {/* Stats links */}
          <div className="space-y-1 mb-6">
            <a href="/bookmarks"
              style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: '#1A1C1E', fontSize: '13px', transition: 'background 0.1s' }}
              className="hover:bg-[#F0F1F2]">
              <span style={{ marginRight: '10px' }}>📑</span>
              <span style={{ flex: 1 }}>收藏的文章</span>
              <span style={{ fontSize: '12px', color: '#8C9096' }}>→</span>
            </a>
            <a href="/history"
              style={{ display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '4px', textDecoration: 'none', color: '#1A1C1E', fontSize: '13px', transition: 'background 0.1s' }}
              className="hover:bg-[#F0F1F2]">
              <span style={{ marginRight: '10px' }}>📖</span>
              <span style={{ flex: 1 }}>浏览历史</span>
              <span style={{ fontSize: '12px', color: '#8C9096' }}>→</span>
            </a>
          </div>

          {/* Actions */}
          <div style={{ borderTop: '1px solid #E8EAED', paddingTop: '16px' }}>
            <button onClick={logout}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '12px 16px', borderRadius: '4px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '13px', color: '#D4322E', transition: 'background 0.1s' }}
              className="hover:bg-[#F0F1F2]">
              <span>🚪</span>
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
