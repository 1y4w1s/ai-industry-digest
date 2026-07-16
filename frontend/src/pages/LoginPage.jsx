import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LaoQianLogo from '../components/LaoQianLogo';

const inputStyle = {
  width: '100%',
  padding: '12px 14px',
  fontSize: '14px',
  background: 'rgba(245,240,232,0.6)',
  border: '1px solid var(--glass-border)',
  borderRadius: '10px',
  color: 'var(--color-text-body)',
  outline: 'none',
  transition: 'border-color 0.15s, box-shadow 0.15s',
  boxSizing: 'border-box',
};

export default function LoginPage() {
  const [mode, setMode] = useState('login');
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
        if (password !== confirmPassword) throw new Error('两次输入的密码不一致');
        const result = await signup(email, password);
        setSuccess(result.message);
        setMode('login');
      } else {
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

  const t = mode === 'login' ? '登录' : mode === 'signup' ? '注册' : '重置密码';
  const s = mode === 'login' ? '欢迎回来' : mode === 'signup' ? '创建新账户' : '输入您的邮箱';

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{
      background: 'linear-gradient(135deg, var(--color-bg-sidebar) 0%, var(--color-bg-off) 30%, var(--color-bg-hover) 60%, var(--color-bg-off) 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* 环境光晕 */}
      <div style={{
        position: 'absolute', top: '-20%', right: '-10%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(200,146,42,0.10) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '-10%', left: '-5%',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(212,101,32,0.06) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* 毛玻璃卡片 */}
      <div className="glass" style={{
        width: '100%', maxWidth: '420px',
        borderRadius: '16px',
        padding: '40px 36px 32px',
        animation: 'revealUp 0.5s var(--ease-spring)',
      }}>
        <div className="text-center mb-8">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
            <LaoQianLogo size={36} color="var(--color-brass)" />
          </div>
          <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            AI 行业资讯聚合平台
          </p>
        </div>

        <div className="text-center mb-6">
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)' }}>{t}</h1>
          <p style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginTop: '4px' }}>{s}</p>
        </div>

        {success && (
          <div style={{ padding: '12px 14px', background: 'rgba(91,140,110,0.10)', borderRadius: '8px', marginBottom: '16px' }}>
            <p style={{ fontSize: '13px', color: 'var(--color-success)' }}>{success}</p>
          </div>
        )}
        {error && (
          <div style={{ padding: '12px 14px', background: 'rgba(194,74,58,0.08)', borderRadius: '8px', marginBottom: '16px' }}>
            <p style={{ fontSize: '13px', color: 'var(--color-high)' }}>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="login-email" style={{ display: 'block', fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '6px' }}>邮箱</label>
            <input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com" required style={inputStyle} disabled={loading}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-brass)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(200,146,42,0.12)'; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--glass-border)'; e.currentTarget.style.boxShadow = 'none'; }} />
          </div>

          {mode !== 'reset' && (
            <>
              <div className="mb-4">
                <label htmlFor="login-password" style={{ display: 'block', fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '6px' }}>密码</label>
                <input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="至少8个字符" required style={inputStyle} disabled={loading}
                  onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-brass)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(200,146,42,0.12)'; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--glass-border)'; e.currentTarget.style.boxShadow = 'none'; }} />
              </div>
              {mode === 'signup' && (
                <div className="mb-6">
                  <label htmlFor="login-confirm" style={{ display: 'block', fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '6px' }}>确认密码</label>
                  <input id="login-confirm" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="再次输入密码" required style={inputStyle} disabled={loading}
                    onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-brass)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(200,146,42,0.12)'; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--glass-border)'; e.currentTarget.style.boxShadow = 'none'; }} />
                </div>
              )}
            </>
          )}

          <button type="submit" disabled={loading}
            style={{
              width: '100%', padding: '12px', fontSize: '14px', fontWeight: 600,
              background: 'linear-gradient(135deg, var(--color-brass) 0%, var(--color-brass-hover) 100%)',
              color: '#fff', border: 'none', borderRadius: '10px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s',
              boxShadow: '0 2px 8px rgba(200,146,42,0.3)',
            }}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.boxShadow = '0 4px 16px rgba(200,146,42,0.4)'; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.boxShadow = '0 2px 8px rgba(200,146,42,0.3)'; }}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                加载中...
              </span>
            ) : t}
          </button>
        </form>

        {mode !== 'reset' && (
          <>
            <div className="flex items-center gap-3 my-6">
              <div style={{ flex: 1, height: '1px', background: 'var(--color-border-light)' }} />
              <span style={{ fontSize: '12px', color: 'var(--color-text-label)', flexShrink: 0 }}>或</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--color-border-light)' }} />
            </div>
          </>
        )}

        <div className="mt-6 text-center space-y-2">
          {mode === 'login' && (
            <>
              <button onClick={() => setMode('reset')} style={{ fontSize: '13px', color: 'var(--color-brass)', background: 'none', border: 'none', cursor: 'pointer', transition: 'opacity 0.15s' }}
                onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
                onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}>忘记密码？</button>
              <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>还没有账户？ <button onClick={() => setMode('signup')} style={{ fontSize: '13px', color: 'var(--color-brass)', background: 'none', border: 'none', cursor: 'pointer' }}>注册</button></p>
            </>
          )}
          {mode === 'signup' && <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>已有账户？ <button onClick={() => setMode('login')} style={{ fontSize: '13px', color: 'var(--color-brass)', background: 'none', border: 'none', cursor: 'pointer' }}>登录</button></p>}
          {mode === 'reset' && <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>返回 <button onClick={() => setMode('login')} style={{ fontSize: '13px', color: 'var(--color-brass)', background: 'none', border: 'none', cursor: 'pointer' }}>登录</button></p>}
        </div>

        <div className="mt-8 pt-6 text-center" style={{ borderTop: '1px solid var(--color-border-light)' }}>
          <p style={{ fontSize: '11px', color: 'var(--color-text-label)' }}>© 2026 捞乾. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
