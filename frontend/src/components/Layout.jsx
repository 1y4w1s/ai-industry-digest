import { useState, useRef, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AIChatBubble from './AIChatBubble';

const NAV_ITEMS = [
  { path: '/', label: '今日日报' },
  { path: '/bookmarks', label: '收藏' },
  { path: '/history', label: '浏览历史' },
  { path: '/settings', label: '设置' },
];

export default function Layout({ isReading }) {
  const { isLoggedIn, user, login, logout } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchRef = useRef(null);
  const navigate = useNavigate();

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
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, [searchOpen]);

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

  return (
    <div className="h-screen flex overflow-hidden" style={{ background: 'var(--color-bg-white)' }}>
      <div className={`sidebar-overlay no-print ${mobileSidebarOpen ? 'open' : ''}`} onClick={() => setMobileSidebarOpen(false)} />

      <aside className={`fixed lg:static z-50 inset-y-0 left-0 flex flex-col flex-shrink-0 transition-all duration-300 no-print ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
        style={{ width: '200px', background: 'var(--color-bg-sidebar)', borderRight: '1px solid var(--color-border-light)' }}>
        <div className="h-12 flex items-center px-5 border-b border-[var(--color-border-light)] flex-shrink-0">
          <span className="logo logo-lg">Signal</span>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const isActive = window.location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => { navigate(item.path); setMobileSidebarOpen(false); }}
                className={`sidebar-link w-full flex items-center gap-3 h-9 text-sm transition-all ${isActive ? 'active' : ''}`}
                style={{
                  paddingLeft: '16px',
                  color: isActive ? 'var(--color-text-title)' : 'var(--color-text-muted)',
                  fontWeight: isActive ? 600 : 400,
                }}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="flex-shrink-0 px-3 pb-3 space-y-1">
          <div className="flex items-center gap-2 px-2 py-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--color-success)' }} />
            <span style={{ fontSize: '11px', color: 'var(--color-text-label)' }}>v2.0 · Signal</span>
          </div>

          {isLoggedIn ? (
            <div onClick={() => navigate('/profile')} className="flex items-center gap-2 px-2 py-1.5 rounded transition-all" style={{ cursor: 'pointer', background: 'transparent' }}>
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0" style={{ background: 'var(--color-border-light)', color: 'var(--color-text-muted)' }}>
                {(user?.nickname || 'U')[0].toUpperCase()}
              </div>
              <span style={{ fontSize: '12px', color: 'var(--color-text-title)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.nickname}</span>
              <button onClick={logout} style={{ fontSize: '10px', color: 'var(--color-text-label)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>退出</button>
            </div>
          ) : (
            <button onClick={handleLogin} className="flex items-center gap-2 w-full px-2 py-1.5 rounded transition-all" style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0" style={{ background: 'var(--color-border-light)', color: 'var(--color-text-muted)' }}>
                ?
              </div>
              <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>登录</span>
            </button>
          )}
        </div>
      </aside>

      <div className="flex flex-col flex-1 min-w-0">
        <header className="h-12 flex items-center gap-4 px-4 lg:px-6 border-b border-[var(--color-border-light)] flex-shrink-0 no-print" style={{ background: 'var(--color-bg-white)' }}>
          <button onClick={() => setMobileSidebarOpen(true)} className="lg:hidden p-1.5 -ml-1" style={{ color: 'var(--color-text-muted)' }} aria-label="打开菜单">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          <span className="lg:hidden" style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '17px', fontWeight: 700, color: 'var(--color-text-title)', letterSpacing: '-0.3px' }}>
            Signal
          </span>

          <div className="flex-1 lg:flex-initial" />

          <div className="flex items-center justify-end">
            {searchOpen ? (
              <form onSubmit={handleSearch} className="flex items-center gap-2">
                <div className="relative">
                  <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none" style={{ color: 'var(--color-text-label)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    ref={searchRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="搜索文章..."
                    style={{
                      width: '240px',
                      padding: '6px 10px 6px 32px',
                      fontSize: '13px',
                      background: 'var(--color-bg-off)',
                      border: '1px solid var(--color-border-bold)',
                      borderRadius: '4px',
                      color: 'var(--color-text-body)',
                      outline: 'none',
                    }}
                    onBlur={(e) => {
                      setTimeout(() => {
                        if (!searchQuery) setSearchOpen(false);
                      }, 200);
                    }}
                  />
                </div>
                <button type="button" onClick={() => { setSearchOpen(false); setSearchQuery(''); }} style={{ fontSize: '11px', color: 'var(--color-text-label)', background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}>
                  Esc
                </button>
              </form>
            ) : (
              <button onClick={() => setSearchOpen(true)} style={{ padding: '6px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', borderRadius: '4px' }}>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>

      <div className="no-print">
        <AIChatBubble visible={!isReading} />
      </div>
    </div>
  );
}
