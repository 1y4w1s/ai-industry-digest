import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import Home from './pages/Home';

export default function App() {
  const [readerArticle, setReaderArticle] = useState(null);

  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route
            index
            element={<Home onReadArticle={setReaderArticle} readerArticle={readerArticle} />}
          />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
