import { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import DailyReports from './pages/DailyReports';
import Search from './pages/Search';
import Bookmarks from './pages/Bookmarks';
import History from './pages/History';
import Stats from './pages/Stats';

function ProtectedRoute({ children }) {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? children : <Navigate to="/" />;
}

export default function App() {
  const [drawerArticleId, setDrawerArticleId] = useState(null);

  return (
    <Routes>
      <Route
        element={
          <Layout
            drawerArticleId={drawerArticleId}
            onCloseDrawer={() => setDrawerArticleId(null)}
          />
        }
      >
        <Route index element={<DailyReports onArticleClick={setDrawerArticleId} />} />
        <Route path="search" element={<Search onArticleClick={setDrawerArticleId} />} />
        <Route
          path="bookmarks"
          element={
            <ProtectedRoute>
              <Bookmarks onArticleClick={setDrawerArticleId} />
            </ProtectedRoute>
          }
        />
        <Route
          path="history"
          element={
            <ProtectedRoute>
              <History onArticleClick={setDrawerArticleId} />
            </ProtectedRoute>
          }
        />
        <Route path="stats" element={<Stats onArticleClick={setDrawerArticleId} />} />
      </Route>
    </Routes>
  );
}
