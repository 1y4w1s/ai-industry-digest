import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import SearchPage from './pages/SearchPage';

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
        </Route>
      </Routes>
    </AuthProvider>
  );
}
