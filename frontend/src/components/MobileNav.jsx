import { useLocation, useNavigate } from 'react-router-dom';

const TABS = [
  { path: '/', label: '首页', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { path: '/search', label: '搜索', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
  { path: '/history', label: '历史', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { path: '/profile', label: '我的', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
];

export default function MobileNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50"
      style={{
        background: 'var(--color-bg-sidebar)',
        borderTop: '1px solid var(--color-border-light)',
        paddingBottom: 'env(safe-area-inset-bottom, 0)',
      }}>
      <div style={{ display: 'flex', alignItems: 'center', height: 56 }}>
        {TABS.map((tab) => {
          const isActive = location.pathname === tab.path;
          return (
            <button key={tab.path}
              onClick={() => navigate(tab.path)}
              style={{
                flex: 1, height: '100%',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                gap: 2,
                background: 'none', border: 'none', cursor: 'pointer',
                color: isActive ? 'var(--color-brass)' : 'var(--color-text-label)',
                transition: 'color 0.15s',
              }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={isActive ? 2.2 : 1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d={tab.icon} />
              </svg>
              <span style={{ fontSize: 10, fontWeight: isActive ? 600 : 500, lineHeight: 1 }}>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
