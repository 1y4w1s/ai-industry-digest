import { useState, useRef, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AIChatBubble from './AIChatBubble';

const NAV_ITEMS = [
  { path: '/', label: '今日日报' },
];

export default function Layout({ isReading }) {
  const { isLoggedIn, user, login, logout } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchRef = useRef(null);
  const navigate = useNavigate();

  // Auto-focus search input when opened
  useEffect(() => {
    if (searchOpen) {
      setTimeout(() => searchRef.current?.focus(), 100);
    }
  }, [searchOpen]);

  // Close search on Esc
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
      navigate(`/?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
      setSearchOpen(false);
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
          <span className="logo logo-lg">Signal</span>
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

        {/* Footer — status + user */}
        <div className="flex-shrink-0 px-3 pb-3 space-y-1">
          {/* Status line */}
          <div className="flex items-center gap-2 px-2 py-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#1E8E4A' }} />
            <span style={{ fontSize: '11px', color: '#8C9096' }}>v2.0 · Signal</span>
          </div>

          {/* User / Login */}
          {isLoggedIn ? (
            <div className="flex items-center gap-2 px-2 py-1.5 rounded transition-all hover:bg-[#F0F1F2]" style={{ cursor: 'pointer' }}>
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0" style={{ background: '#E8EAED', color: '#686C72' }}>
                {(user?.nickname || 'U')[0].toUpperCase()}
              </div>
              <span style={{ fontSize: '12px', color: '#1A1C1E', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.nickname}</span>
              <button onClick={logout} style={{ fontSize: '10px', color: '#8C9096', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>退出</button>
            </div>
          ) : (
            <button onClick={handleLogin} className="flex items-center gap-2 w-full px-2 py-1.5 rounded transition-all hover:bg-[#F0F1F2]" style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0" style={{ background: '#E8EAED', color: '#686C72' }}>
                ?
              </div>
              <span style={{ fontSize: '12px', color: '#686C72' }}>登录</span>
            </button>
          )}
        </div>
      </aside>

      {/* ── Main area ─────────────── */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header (48px) — clean: logo + search icon */}
        <header className="h-12 flex items-center gap-4 px-4 lg:px-6 border-b border-[#E8EAED] bg-white flex-shrink-0">
          {/* Mobile hamburger */}
          <button onClick={() => setMobileSidebarOpen(true)} className="lg:hidden p-1.5 -ml-1" style={{ color: '#686C72' }} aria-label="打开菜单">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          {/* Desktop logo (visible on lg+) */}
          <span className="hidden lg:block logo logo-sm" style={{ marginRight: 'auto' }}>Signal</span>

          {/* Mobile logo (visible below lg) */}
          <span className="lg:hidden" style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '17px', fontWeight: 700, color: '#1A1C1E', letterSpacing: '-0.3px' }}>
            Signal
          </span>

          {/* Spacer */}
          <div className="flex-1 lg:flex-initial" />

          {/* Search icon → expandable input */}
          <div className="flex items-center justify-end">
            {searchOpen ? (
              <form onSubmit={handleSearch} className="flex items-center gap-2">
                <div className="relative">
                  <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none" style={{ color: '#8C9096' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
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
                      background: '#F0F1F2',
                      border: '1px solid #B0B4B8',
                      borderRadius: '4px',
                      color: '#2C2E32',
                      outline: 'none',
                    }}
                    onBlur={(e) => {
                      // Small delay to allow click on the input itself
                      setTimeout(() => {
                        if (!searchQuery) setSearchOpen(false);
                      }, 200);
                    }}
                  />
                </div>
                <button type="button" onClick={() => { setSearchOpen(false); setSearchQuery(''); }} style={{ fontSize: '11px', color: '#8C9096', background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}>
                  Esc
                </button>
              </form>
            ) : (
              <button onClick={() => setSearchOpen(true)} style={{ padding: '6px', background: 'none', border: 'none', cursor: 'pointer', color: '#686C72', borderRadius: '4px' }}>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
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
