import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout';
import { ToastProvider } from './components/Toast';
import { UndoToastProvider } from './components/UndoToast';
import Home from './pages/Home';

// 代码分割：非首屏页面按需加载
const SearchPage = lazy(() => import('./pages/SearchPage'));
const BookmarksPage = lazy(() => import('./pages/BookmarksPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const ArchivePage = lazy(() => import('./pages/ArchivePage'));
const DigestPage = lazy(() => import('./pages/DigestPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));

function SuspenseFallback() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex gap-1.5">
        <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
        <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
        <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
      </div>
    </div>
  );
}

function PrivateRoute({ children, requireAdmin = false }) {
  const { isLoggedIn, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex gap-1.5">
          <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
          <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
          <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    // 重定向到登录页，记录来源路径以便登录后回跳
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (requireAdmin) {
    // admin 路由由后端验证（Layout.jsx 通过 api.getMe 获取角色），
    // 前端仅做快速过滤，后端仍有完整校验
    const isAdmin = user?.role === 'admin';
    if (!isAdmin) {
      return <Navigate to="/" replace />;
    }
  }

  return children;
}

function AppContent() {
  return (
    <Routes>
      <Route path="/login" element={<Suspense fallback={<SuspenseFallback />}><LoginPage /></Suspense>} />
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="search" element={<Suspense fallback={<SuspenseFallback />}><SearchPage /></Suspense>} />
        <Route path="bookmarks" element={<Suspense fallback={<SuspenseFallback />}><PrivateRoute><BookmarksPage /></PrivateRoute></Suspense>} />
        <Route path="history" element={<Suspense fallback={<SuspenseFallback />}><PrivateRoute><HistoryPage /></PrivateRoute></Suspense>} />
        <Route path="profile" element={<Suspense fallback={<SuspenseFallback />}><PrivateRoute><ProfilePage /></PrivateRoute></Suspense>} />
        <Route path="settings" element={<Suspense fallback={<SuspenseFallback />}><SettingsPage /></Suspense>} />
         <Route path="archive" element={<Suspense fallback={<SuspenseFallback />}><ArchivePage /></Suspense>} />
         <Route path="digest/:date" element={<Suspense fallback={<SuspenseFallback />}><DigestPage /></Suspense>} />
         <Route path="admin" element={<Suspense fallback={<SuspenseFallback />}><PrivateRoute requireAdmin><AdminDashboard /></PrivateRoute></Suspense>} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <UndoToastProvider>
            <AppContent />
          </UndoToastProvider>
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
