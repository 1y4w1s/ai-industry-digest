import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ArticleDrawer from './ArticleDrawer';
import AIChatBubble from './AIChatBubble';

const NAV_ITEMS = [
  {
    path: '/',
    label: '首页日报',
    icon: (a) => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={a ? 2 : 1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>,
  },
  {
    path: '/search',
    label: '全文检索',
    icon: (a) => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={a ? 2 : 1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>,
  },
  {
    path: '/bookmarks',
    label: '我的收藏',
    icon: (a) => <svg className="w-5 h-5" fill={a ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={a ? 0 : 1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg>,
  },
  {
    path: '/history',
    label: '浏览历史',
    icon: (a) => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={a ? 2 : 1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  },
  {
    path: '/stats',
    label: '数据统计',
    icon: (a) => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={a ? 2 : 1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
  },
];

export default function Layout({ drawerArticleId, onCloseDrawer }) {
  const { isLoggedIn, user, login, logout } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
    }
  };

  const handleLogin = () => {
    login({ id: 'demo-user', nickname: 'Demo User', avatar_url: null });
  };

  return (
    <div className="h-screen flex overflow-hidden bg-bg-base">
      {/* Mobile overlay */}
      <div className={`sidebar-overlay ${mobileSidebarOpen ? 'open' : ''}`} onClick={() => setMobileSidebarOpen(false)} />

      {/* ── Sidebar ─────────────── */}
      <aside className={`sidebar fixed z-50 inset-y-0 left-0 flex flex-col bg-bg-surface border-r border-border-subtle transition-all duration-300 ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}>
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-[18px] border-b border-border-subtle flex-shrink-0">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
            AI
          </div>
          <span className="sidebar-logo-text font-heading font-bold text-sm text-text-primary tracking-wide">
            Digest
          </span>
        </div>

        {/* Nav items */}
        <nav className="sidebar-nav flex-1 flex flex-col gap-0.5 py-3 px-3 overflow-y-auto overflow-x-hidden">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              onClick={() => setMobileSidebarOpen(false)}
              className={({ isActive }) =>
                `sidebar-link w-full flex items-center gap-3
                 h-10 rounded-lg text-sm font-medium transition-all duration-150 flex-shrink-0
                 ${isActive
                   ? 'active text-accent bg-accent/8'
                   : 'text-text-tertiary hover:text-text-primary hover:bg-bg-hover'}`
              }
            >
              {({ isActive }) => (
                <>
                  <span className="flex-shrink-0 w-5 flex justify-center">
                    {item.icon(isActive)}
                  </span>
                  <span className="sidebar-label text-xs truncate">
                    {item.label}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer flex items-center gap-3 h-12 px-[18px] border-t border-border-subtle flex-shrink-0">
          <div className="w-1.5 h-1.5 rounded-full bg-success flex-shrink-0" />
          <span className="sidebar-footer-text text-[11px] text-text-tertiary">系统运行中</span>
        </div>
      </aside>

      {/* ── Main area ─────────────── */}
      <div className="flex flex-col flex-1 min-w-0 ml-0 lg:ml-[64px] transition-all duration-250">
        {/* Header */}
        <header className="h-16 flex items-center gap-4 px-4 lg:px-6 border-b border-border-subtle bg-bg-surface/80 backdrop-blur-md flex-shrink-0">
          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="lg:hidden p-2 -ml-2 text-text-secondary hover:text-text-primary transition-colors"
            aria-label="打开菜单"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 max-w-md">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索全站文章..."
                className="search-input w-full pl-9 pr-3.5 py-2 bg-bg-base/60 border border-border-primary rounded-lg text-sm text-text-primary placeholder-text-tertiary/60 focus:outline-none focus:border-accent/50 transition-all"
              />
            </div>
          </form>

          {/* User area */}
          <div className="flex items-center gap-2">
            {isLoggedIn ? (
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-accent/15 flex items-center justify-center text-accent text-xs font-semibold border border-accent/20">
                  {(user?.nickname || 'U')[0].toUpperCase()}
                </div>
                <span className="text-sm text-text-secondary hidden sm:block">{user?.nickname}</span>
                <button onClick={logout} className="text-xs text-text-tertiary hover:text-error transition-colors ml-1">
                  退出
                </button>
              </div>
            ) : (
              <button
                onClick={handleLogin}
                className="flex items-center gap-2 px-3.5 py-2 bg-bg-raised border border-border-primary rounded-lg text-sm text-text-secondary hover:text-text-primary hover:border-border-accent/40 transition-all"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                <span className="hidden sm:inline text-xs">GitHub 登录</span>
              </button>
            )}
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-5 lg:p-8">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Drawer + AI Chat */}
      <ArticleDrawer articleId={drawerArticleId} onClose={onCloseDrawer} />
      <AIChatBubble />
    </div>
  );
}
