import { Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import SearchPage from './pages/SearchPage';
import BookmarksPage from './pages/BookmarksPage';
import HistoryPage from './pages/HistoryPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';

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
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="bookmarks" element={<PrivateRoute><BookmarksPage /></PrivateRoute>} />
        <Route path="history" element={<PrivateRoute><HistoryPage /></PrivateRoute>} />
        <Route path="profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </AuthProvider>
  );
}
