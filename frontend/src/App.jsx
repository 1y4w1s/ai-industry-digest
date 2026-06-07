import { Routes, Route } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout';
import { ToastProvider } from './components/Toast';
import Home from './pages/Home';

// 代码分割：非首屏页面按需加载
const SearchPage = lazy(() => import('./pages/SearchPage'));
const BookmarksPage = lazy(() => import('./pages/BookmarksPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const ArchivePage = lazy(() => import('./pages/ArchivePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const KnowledgeBasePage = lazy(() => import('./pages/KnowledgeBasePage'));
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

function PrivateRoute({ children }) {
  const { isLoggedIn, loading } = useAuth();
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
  return isLoggedIn ? children : <LoginPage />;
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
         <Route path="knowledge" element={<Suspense fallback={<SuspenseFallback />}><KnowledgeBasePage /></Suspense>} />
         <Route path="admin" element={<Suspense fallback={<SuspenseFallback />}><PrivateRoute><AdminDashboard /></PrivateRoute></Suspense>} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
