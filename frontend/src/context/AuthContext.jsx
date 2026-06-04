import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

const TOKEN_KEY = 'signal_auth_token';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On mount: restore session from stored token
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      api.getMe()
        .then((profile) => {
          setUser(profile);
        })
        .catch(() => {
          // Token invalid — clear it
          localStorage.removeItem(TOKEN_KEY);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async () => {
    localStorage.setItem(TOKEN_KEY, 'demo-user');
    try {
      const profile = await api.getMe();
      setUser(profile);
    } catch {
      // If API fails, set a fallback so UI still works
      setUser({ id: 'demo-user', nickname: 'Demo User', avatar_url: null });
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoggedIn: !!user, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
