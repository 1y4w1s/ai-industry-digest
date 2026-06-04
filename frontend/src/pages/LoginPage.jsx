import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';

export default function LoginPage() {
  const [mode, setMode] = useState('login'); // 'login' | 'signup' | 'reset'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { login, signup, resetPassword } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectTo = location.state?.from || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (mode === 'login') {
        await login(email, password);
        navigate(redirectTo);
      } else if (mode === 'signup') {
        if (password !== confirmPassword) {
          throw new Error('两次输入的密码不一致');
        }
        const result = await signup(email, password);
        setSuccess(result.message);
        setMode('login');
      } else if (mode === 'reset') {
        await resetPassword(email);
        setError('重置链接已发送到您的邮箱');
        setMode('login');
      }
    } catch (err) {
      setError(err.message || '操作失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const getTitle = () => {
    if (mode === 'login') return '登录';
    if (mode === 'signup') return '注册';
    return '重置密码';
  };

  const getSubtitle = () => {
    if (mode === 'login') return '欢迎回来';
    if (mode === 'signup') return '创建新账户';
    return '输入您的邮箱';
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'var(--color-bg-white)' }}>
      <div style={{ width: '100%', maxWidth: '400px', background: 'var(--color-bg-white)', borderRadius: '12px', boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)', padding: '32px' }}>
        {/* Logo */}
        <div className="text-center mb-8">
          <span style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '24px', fontWeight: 700, color: 'var(--color-text-title)' }}>Signal</span>
          <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginTop: '4px' }}>AI行业资讯聚合平台</p>
        </div>

        {/* Title */}
        <div className="text-center mb-6">
          <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '24px', fontWeight: 700, color: 'var(--color-text-title)' }}>
            {getTitle()}
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginTop: '4px' }}>{getSubtitle()}</p>
        </div>

        {/* Success message */}
        {success && (
          <div style={{ padding: '12px 14px', background: '#F0FDF4', borderRadius: '6px', marginBottom: '16px' }}>
            <p style={{ fontSize: '13px', color: '#16A34A' }}>{success}</p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div style={{ padding: '12px 14px', background: '#FEF2F2', borderRadius: '6px', marginBottom: '16px' }}>
            <p style={{ fontSize: '13px', color: '#D4322E' }}>{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {/* Email */}
          <div className="mb-4">
            <label style={{ display: 'block', fontSize: '12px', color: '#686C72', marginBottom: '6px' }}>
              邮箱
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              style={{
                width: '100%',
                padding: '12px 14px',
                fontSize: '14px',
                background: '#F8F9FA',
                border: '1px solid #E8EAED',
                borderRadius: '6px',
                color: '#1A1C1E',
                outline: 'none',
                transition: 'border-color 0.15s',
              }}
              className="focus:border-[#2864A8]"
              disabled={loading}
            />
          </div>

          {/* Password */}
          {mode !== 'reset' && (
            <>
              <div className="mb-4">
                <label style={{ display: 'block', fontSize: '12px', color: '#686C72', marginBottom: '6px' }}>
                  密码
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="至少8个字符"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    fontSize: '14px',
                    background: '#F8F9FA',
                    border: '1px solid #E8EAED',
                    borderRadius: '6px',
                    color: '#1A1C1E',
                    outline: 'none',
                    transition: 'border-color 0.15s',
                  }}
                  className="focus:border-[#2864A8]"
                  disabled={loading}
                />
              </div>

              {/* Confirm Password */}
              {mode === 'signup' && (
                <div className="mb-6">
                  <label style={{ display: 'block', fontSize: '12px', color: '#686C72', marginBottom: '6px' }}>
                    确认密码
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="再次输入密码"
                    required
                    style={{
                      width: '100%',
                      padding: '12px 14px',
                      fontSize: '14px',
                      background: '#F8F9FA',
                      border: '1px solid #E8EAED',
                      borderRadius: '6px',
                      color: '#1A1C1E',
                      outline: 'none',
                      transition: 'border-color 0.15s',
                    }}
                    className="focus:border-[#2864A8]"
                    disabled={loading}
                  />
                </div>
              )}
            </>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              fontWeight: 600,
              background: '#2864A8',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background 0.15s',
            }}
            className="hover:bg-[#1F4E82]"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                加载中...
              </span>
            ) : (
              getTitle()
            )}
          </button>
        </form>

        {/* Divider */}
        {mode !== 'reset' && (
          <div className="flex items-center gap-3 my-6">
            <div style={{ flex: 1, height: '1px', background: '#E8EAED' }} />
            <span style={{ fontSize: '12px', color: '#8C9096', flexShrink: 0 }}>或</span>
            <div style={{ flex: 1, height: '1px', background: '#E8EAED' }} />
          </div>
        )}

        {/* GitHub OAuth */}
        {mode !== 'reset' && (
          <button
            onClick={() => supabase.auth.signInWithOAuth({
              provider: 'github',
              options: { redirectTo: window.location.origin }
            })}
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              fontWeight: 500,
              background: '#1A1C1E',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background 0.15s',
            }}
            className="hover:bg-[#2C2E32]"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            使用 GitHub 登录
          </button>
        )}

        {/* Links */}
        <div className="mt-6 text-center space-y-2">
          {mode === 'login' && (
            <>
              <button
                onClick={() => setMode('reset')}
                style={{ fontSize: '13px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                忘记密码？
              </button>
              <p style={{ fontSize: '13px', color: '#686C72' }}>
                还没有账户？{' '}
                <button
                  onClick={() => setMode('signup')}
                  style={{ fontSize: '13px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  注册
                </button>
              </p>
            </>
          )}
          {mode === 'signup' && (
            <p style={{ fontSize: '13px', color: '#686C72' }}>
              已有账户？{' '}
              <button
                onClick={() => setMode('login')}
                style={{ fontSize: '13px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                登录
              </button>
            </p>
          )}
          {mode === 'reset' && (
            <p style={{ fontSize: '13px', color: '#686C72' }}>
              返回{' '}
              <button
                onClick={() => setMode('login')}
                style={{ fontSize: '13px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                登录
              </button>
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-[#E8EAED] text-center">
          <p style={{ fontSize: '11px', color: '#8C9096' }}>
            © 2026 Signal. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
