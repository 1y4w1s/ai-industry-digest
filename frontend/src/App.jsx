import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import SearchPage from './pages/SearchPage';
import BookmarksPage from './pages/BookmarksPage';
import HistoryPage from './pages/HistoryPage';
import ProfilePage from './pages/ProfilePage';

export default function App() {
  const [readerArticle, setReaderArticle] = useState(null);

  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout isReading={!!readerArticle} />}>
          <Route
            index
            element={<Home onReadArticle={setReaderArticle} readerArticle={readerArticle} />}
          />
          <Route
            path="search"
            element={<SearchPage onReadArticle={setReaderArticle} />}
          />
          <Route
            path="bookmarks"
            element={<BookmarksPage onReadArticle={setReaderArticle} />}
          />
          <Route
            path="history"
            element={<HistoryPage onReadArticle={setReaderArticle} />}
          />
          <Route
            path="profile"
            element={<ProfilePage onReadArticle={setReaderArticle} />}
          />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
