import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { setToken, clearToken } from '../lib/token';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [supabase, setSupabase] = useState(null);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // 延迟加载 supabase，减少首屏体积
        const { supabase: client } = await import('../lib/supabase');
        setSupabase(client);
        
        const { data: { session } } = await client.auth.getSession();
        if (session?.access_token) {
          setToken(session.access_token);
        }
        setUser(session?.user || null);
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setLoading(false);
      }
    };
    initializeAuth();
  }, []);

  useEffect(() => {
    if (!supabase) return;

    const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.access_token) {
        setToken(session.access_token);
      } else {
        clearToken();
      }
      setUser(session?.user || null);
    });

    return () => {
      authListener?.unsubscribe();
    };
  }, [supabase]);

  const login = useCallback(async (email, password) => {
    if (!supabase) throw new Error('Auth not initialized');
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  }, [supabase]);

  const signup = useCallback(async (email, password, options = {}) => {
    if (!supabase) throw new Error('Auth not initialized');
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          nickname: options.nickname || email.split('@')[0],
        },
        emailRedirectTo: `${window.location.origin}/login`,
      },
    });
    if (error) throw error;
    
    return { message: '注册成功！请检查邮箱完成验证' };
  }, [supabase]);

  const logout = useCallback(async () => {
    if (!supabase) throw new Error('Auth not initialized');
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  }, [supabase]);

  const resetPassword = useCallback(async (email) => {
    if (!supabase) throw new Error('Auth not initialized');
    const { error } = await supabase.auth.resetPasswordForEmail(email);
    if (error) throw error;
  }, [supabase]);

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, resetPassword, isLoggedIn: !!user, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
