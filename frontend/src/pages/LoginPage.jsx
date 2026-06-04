import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

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
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: '#FBFCFD' }}>
      <div style={{ width: '100%', maxWidth: '400px', background: 'white', borderRadius: '12px', boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)', padding: '32px' }}>
        {/* Logo */}
        <div className="text-center mb-8">
          <span style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '24px', fontWeight: 700, color: '#1A1C1E' }}>Signal</span>
          <p style={{ fontSize: '13px', color: '#686C72', marginTop: '4px' }}>AI行业资讯聚合平台</p>
        </div>

        {/* Title */}
        <div className="text-center mb-6">
          <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '24px', fontWeight: 700, color: '#1A1C1E' }}>
            {getTitle()}
          </h1>
          <p style={{ fontSize: '14px', color: '#686C72', marginTop: '4px' }}>{getSubtitle()}</p>
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
