import { useState, useRef, useEffect } from 'react';
import { Outlet, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AIChatBubble from './AIChatBubble';
import ErrorBoundary from './ErrorBoundary';
import RecentItems from './RecentItems';
import ScrollProgress from './ScrollProgress';
import Onboarding from './Onboarding';
import KeyboardShortcuts from './KeyboardShortcuts';

const ADMIN_USER = '1y4w1s';

function useNavItems(user) {
  const base = [
    { path: '/', label: '今日日报', icon: 'home' },
    { path: '/archive', label: '日报归档', icon: 'archive' },
    { path: '/bookmarks', label: '我的收藏', icon: 'bookmark' },
    { path: '/history', label: '浏览历史', icon: 'history' },
    { path: '/search', label: '搜索', icon: 'search' },
    { path: '/settings', label: '设置', icon: 'settings' },
  ];
  const isAdmin = user?.user_metadata?.nickname === ADMIN_USER || user?.email?.startsWith(ADMIN_USER);
  if (isAdmin) {
    base.splice(4, 0, { path: '/admin', label: '管理后台', icon: 'shield' });
  }
  return base;
}

const ICONS = {
  home: 'M3 12l9-9 9 9M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10',
  archive: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  bookmark: 'M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z',
  history: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  settings: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
  shield: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  menu: 'M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5',
  close: 'M6 18L18 6M6 6l12 12',
  chevronRight: 'M9 5l7 7-7 7',
  plus: 'M12 4v16m8-8H4',
  logout: 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1',
};

function NavIcon({ name }) {
  return (
    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.6" width="18" height="18" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d={ICONS[name] || ICONS.home} />
    </svg>
  );
}

export default function Layout() {
  const { isLoggedIn, user, login, logout } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const isReading = !!searchParams.get('article');
  const NAV_ITEMS = useNavItems(user);

  useEffect(() => {
    if (searchOpen) {
      setTimeout(() => searchRef.current?.focus(), 100);
    }
  }, [searchOpen]);

  useEffect(() => {
    const handle = (e) => {
      if (e.key === 'Escape' && searchOpen) {
        setSearchOpen(false);
        setSearchQuery('');
      }
      if (e.key === 'Escape' && mobileSidebarOpen) {
        setMobileSidebarOpen(false);
      }
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, [searchOpen, mobileSidebarOpen]);

  // 全局 ⌘K / Ctrl+K 唤起搜索
  useEffect(() => {
    const handle = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
      setSearchOpen(false);
    }
  };

  const handleLogin = () => {
    navigate('/login');
  };

  const closeSidebar = () => setMobileSidebarOpen(false);

  return (
    <div className="h-screen flex overflow-hidden" style={{ background: 'var(--color-bg-white)' }}>
      <a href="#main-content" className="skip-link" style={{
        position: 'absolute', left: '-9999px', top: 'auto',
        width: '1px', height: '1px', overflow: 'hidden',
      }} onFocus={(e) => { e.currentTarget.style.cssText = 'position:fixed;top:16px;left:16px;width:auto;height:auto;padding:8px 14px;background:var(--color-text-title);color:#fff;border-radius:6px;z-index:100;'; }}>
        跳到主内容
      </a>

      <div className={`sidebar-overlay no-print ${mobileSidebarOpen ? 'open' : ''}`} onClick={closeSidebar} />

      <aside
        className={`fixed lg:static z-50 inset-y-0 left-0 flex flex-col flex-shrink-0 transition-all duration-300 no-print ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
        style={{
          width: '240px',
          background: 'var(--color-bg-sidebar)',
          borderRight: '1px solid var(--color-border-light)',
        }}
      >
        <div className="h-14 flex items-center px-5 border-b flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
          <div className="flex items-center gap-2">
            <div style={{
              width: 28, height: 28, borderRadius: 6,
              background: 'var(--color-brand-ink)',
              color: '#fff',
              display: 'grid', placeItems: 'center',
              fontFamily: 'var(--font-display)',
              fontWeight: 700, fontSize: 15,
            }}>S</div>
            <span className="logo logo-lg" style={{ fontSize: 18 }}>Signal</span>
          </div>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto" aria-label="主导航">
          {NAV_ITEMS.map((item) => {
            const isActive = window.location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => { navigate(item.path); setMobileSidebarOpen(false); }}
                className={`sidebar-link w-full flex items-center gap-2.5 h-9 text-sm ${isActive ? 'active' : ''}`}
                style={{
                  paddingLeft: '12px',
                  paddingRight: '12px',
                  color: isActive ? 'var(--color-brand-ink)' : 'var(--color-text-muted)',
                  fontWeight: isActive ? 600 : 500,
                }}
                aria-current={isActive ? 'page' : undefined}
              >
                <NavIcon name={item.icon} />
                <span style={{ flex: 1, textAlign: 'left' }}>{item.label}</span>
                {item.path === '/' && (
                  <span style={{
                    fontSize: 10, fontWeight: 600, padding: '1px 6px',
                    borderRadius: 999, background: 'var(--color-accent-amber-bg)',
                    color: 'var(--color-accent-amber)',
                  }}>+12</span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="flex-shrink-0 px-3 pb-3 space-y-1 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
          <div className="flex items-center gap-2 px-2 py-2 mt-2">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--color-success)' }} />
            <span style={{ fontSize: 11, color: 'var(--color-text-label)' }}>v2.1 · Signal</span>
          </div>

          {isLoggedIn ? (
            <button
              type="button"
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2 px-2 py-1.5 rounded transition-all w-full"
              style={{ cursor: 'pointer', background: 'transparent', border: 'none', textAlign: 'left', color: 'inherit' }}
              aria-label="个人主页"
            >
              <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold flex-shrink-0" style={{ background: 'var(--color-brand-ink-bg)', color: 'var(--color-brand-ink)' }}>
                {(user?.nickname || 'U')[0].toUpperCase()}
              </div>
              <span style={{ fontSize: 12, color: 'var(--color-text-title)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.nickname}</span>
              <button onClick={(e) => { e.stopPropagation(); logout(); }} className="hover:text-current" style={{ fontSize: 10, color: 'var(--color-text-label)', background: 'none', border: 'none', cursor: 'pointer', padding: 4 }} aria-label="退出登录">
                <NavIcon name="logout" />
              </button>
            </button>
          ) : (
            <button onClick={handleLogin} className="flex items-center gap-2 w-full px-2 py-1.5 rounded transition-all" style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
              <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold flex-shrink-0" style={{ background: 'var(--color-bg-off)', color: 'var(--color-text-muted)' }}>
                ?
              </div>
              <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>登录</span>
            </button>
          )}

          <RecentItems onItemClick={closeSidebar} />
        </div>
      </aside>

      <div className="flex flex-col flex-1 min-w-0">
        <header className="h-14 flex items-center gap-3 px-4 lg:px-6 border-b flex-shrink-0 no-print relative" style={{ background: 'var(--color-bg-white)', borderColor: 'var(--color-border-light)' }}>
          <ScrollProgress />
          <button onClick={() => setMobileSidebarOpen(true)} className="lg:hidden p-2 -ml-1 rounded" style={{ color: 'var(--color-text-muted)' }} aria-label="打开菜单">
            <NavIcon name="menu" />
          </button>

          <div className="lg:hidden flex items-center gap-2">
            <div style={{
              width: 24, height: 24, borderRadius: 5,
              background: 'var(--color-brand-ink)', color: '#fff',
              display: 'grid', placeItems: 'center',
              fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 13,
            }}>S</div>
            <span className="font-display" style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-title)', letterSpacing: '-0.3px' }}>Signal</span>
          </div>

          <div className="flex-1" />

          <div className="flex items-center gap-2">
            {searchOpen ? (
              <form onSubmit={handleSearch} className="flex items-center gap-2">
                <div className="relative">
                  <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none" style={{ color: 'var(--color-text-label)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d={ICONS.search} />
                  </svg>
                  <input
                    ref={searchRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="搜索文章、来源、标签…"
                    aria-label="搜索"
                    style={{
                      width: '300px',
                      height: 36,
                      padding: '0 12px 0 32px',
                      fontSize: 13,
                      background: 'var(--color-bg-off)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 8,
                      color: 'var(--color-text-body)',
                      outline: 'none',
                      transition: 'all 0.15s var(--ease)',
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-brand-ink)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(15,76,58,0.12)'; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.boxShadow = 'none'; }}
                  />
                </div>
                <button type="button" onClick={() => { setSearchOpen(false); setSearchQuery(''); }} style={{ fontSize: 11, color: 'var(--color-text-label)', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px', borderRadius: 4 }} aria-label="关闭搜索">
                  Esc
                </button>
              </form>
            ) : (
              <button
                onClick={() => setSearchOpen(true)}
                className="hidden lg:flex items-center gap-2"
                style={{
                  height: 36, padding: '0 10px 0 12px',
                  background: 'var(--color-bg-off)',
                  border: '1px solid var(--color-border-light)',
                  borderRadius: 8,
                  color: 'var(--color-text-label)',
                  fontSize: 13,
                  transition: 'all 0.15s var(--ease)',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border-light)'; }}
                aria-label="打开搜索 (Ctrl+K)"
              >
                <NavIcon name="search" />
                <span>搜索…</span>
                <kbd style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10,
                  padding: '1px 5px', borderRadius: 4,
                  background: 'var(--color-bg-white)', border: '1px solid var(--color-border-light)',
                  color: 'var(--color-text-label)',
                }}>⌘K</kbd>
              </button>
            )}
          </div>
        </header>

        <main id="main-content" className="flex-1 flex flex-col min-h-0 overflow-auto">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
          <div style={{
            flexShrink: 0,
            textAlign: 'center',
            fontSize: 10,
            color: 'var(--color-text-label)',
            opacity: 0.5,
            lineHeight: '24px',
            height: 24,
            letterSpacing: '0.3px',
          }}>
            闽ICP备2026020386号-1
          </div>
        </main>
      </div>

      <div className="no-print">
        <AIChatBubble visible={!isReading} />
      </div>

      <KeyboardShortcuts />
      {location.pathname === '/' && <Onboarding />}
    </div>
  );
}
