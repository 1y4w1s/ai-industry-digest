import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AIChatBubble from './AIChatBubble';

const NAV_ITEMS = [
  { path: '/', label: '今日日报' },
  { path: '/search', label: '全文检索' },
  { path: '/bookmarks', label: '我的收藏' },
  { path: '/history', label: '浏览历史' },
  { path: '/stats', label: '数据统计' },
];

export default function Layout({ isReading }) {
  const { isLoggedIn, user, login, logout } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
    }
  };

  const handleLogin = () => {
    login({ id: 'demo-user', nickname: 'Demo User', avatar_url: null });
  };

  return (
    <div className="h-screen flex overflow-hidden" style={{ background: '#FBFCFD' }}>
      {/* Mobile overlay */}
      <div className={`sidebar-overlay ${mobileSidebarOpen ? 'open' : ''}`} onClick={() => setMobileSidebarOpen(false)} />

      {/* ── Sidebar (200px, fixed, light) ─────────────── */}
      <aside className={`fixed lg:static z-50 inset-y-0 left-0 flex flex-col flex-shrink-0 transition-all duration-300 ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
        style={{ width: '200px', background: '#FAFBFC', borderRight: '1px solid #E8EAED' }}>
        {/* Logo */}
        <div className="h-12 flex items-center px-5 border-b border-[#E8EAED] flex-shrink-0">
          <span style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '20px', fontWeight: 700, color: '#1A1C1E', letterSpacing: '-0.3px' }}>
            Signal
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const isActive = item.path === '/' && window.location.pathname === '/';
            return (
              <button
                key={item.path}
                onClick={() => { navigate(item.path); setMobileSidebarOpen(false); }}
                className={`sidebar-link w-full flex items-center gap-3 h-9 text-sm transition-all ${isActive ? 'active' : ''}`}
                style={{
                  paddingLeft: '16px',
                  color: isActive ? '#1A1C1E' : '#686C72',
                  fontWeight: isActive ? 600 : 400,
                }}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="h-10 flex items-center gap-2 px-5 border-t border-[#E8EAED] flex-shrink-0">
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#1E8E4A' }} />
          <span style={{ fontSize: '11px', color: '#8C9096' }}>v2.0 · Signal</span>
        </div>
      </aside>

      {/* ── Main area ─────────────── */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header (48px) */}
        <header className="h-12 flex items-center gap-4 px-4 lg:px-6 border-b border-[#E8EAED] bg-white flex-shrink-0">
          {/* Mobile hamburger */}
          <button onClick={() => setMobileSidebarOpen(true)} className="lg:hidden p-1.5 -ml-1" style={{ color: '#686C72' }} aria-label="打开菜单">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 max-w-sm">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none" style={{ color: '#8C9096' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索文章..."
                className="search-input w-full pl-9 pr-3 py-[6px] rounded-[4px] text-sm transition-all focus:outline-none"
                style={{ background: '#F0F1F2', border: '1px solid transparent', color: '#2C2E32' }}
                onFocus={(e) => e.target.style.borderColor = '#B0B4B8'}
                onBlur={(e) => e.target.style.borderColor = 'transparent'}
              />
            </div>
          </form>

          {/* User */}
          <div className="flex items-center gap-2">
            {isLoggedIn ? (
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold" style={{ background: '#F0F1F2', color: '#686C72' }}>
                  {(user?.nickname || 'U')[0].toUpperCase()}
                </div>
                <span className="text-sm hidden sm:block" style={{ color: '#686C72' }}>{user?.nickname}</span>
                <button onClick={logout} className="text-xs" style={{ color: '#8C9096' }}>退出</button>
              </div>
            ) : (
              <button onClick={handleLogin} className="flex items-center gap-2 px-3 py-[6px] rounded-[4px] text-sm transition-all" style={{ background: '#F0F1F2', color: '#2C2E32' }}>
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                <span className="text-xs">登录</span>
              </button>
            )}
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>

      <AIChatBubble visible={!isReading} />
    </div>
  );
}
