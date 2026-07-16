import { useState } from 'react';
import { api } from '../api/client';

// 网页自助订阅简报（网站优化）：零成本增长入口
export default function SubscribeBox() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | done | error
  const [msg, setMsg] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    const v = email.trim();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)) {
      setStatus('error');
      setMsg('请输入有效的邮箱地址');
      return;
    }
    setStatus('loading');
    setMsg('');
    try {
      const res = await api.subscribe(v);
      setStatus('done');
      setMsg(res.message || '订阅成功');
      setEmail('');
    } catch (err) {
      setStatus('error');
      setMsg(err.message || '订阅失败，请稍后重试');
    }
  };

  return (
    <div className="no-print" style={{ borderTop: '1px solid var(--color-border-light)', marginTop: '32px', paddingTop: '24px' }}>
      <div style={{ maxWidth: '480px', margin: '0 auto', textAlign: 'center' }}>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: '18px', fontWeight: 700, color: 'var(--color-text-title)', marginBottom: '6px' }}>
          订阅 æä¹¾ 每日 AI 情报
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '16px', lineHeight: 1.6 }}>
          编辑部每天为你挑选值得关注的 AI 信号。留下邮箱，简报自动送达，随时可退订。
        </p>

        {status === 'done' ? (
          <div style={{ fontSize: '13px', color: 'var(--color-success)', padding: '12px', background: 'var(--color-bg-off)', borderRadius: '6px' }}>
            ✓ {msg}
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: 'flex', gap: '8px', maxWidth: '380px', margin: '0 auto' }}>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              disabled={status === 'loading'}
              style={{ flex: 1, padding: '10px 12px', fontSize: '13px', border: '1px solid var(--color-border-bold)', borderRadius: '6px', background: 'var(--color-bg-white)', color: 'var(--color-text-body)', outline: 'none' }}
            />
            <button type="submit" disabled={status === 'loading'}
              style={{ padding: '10px 18px', fontSize: '13px', fontWeight: 600, color: 'var(--color-bg-white)', background: 'var(--color-brass)', border: 'none', borderRadius: '6px', cursor: 'pointer', opacity: status === 'loading' ? 0.6 : 1, whiteSpace: 'nowrap' }}>
              {status === 'loading' ? '提交中' : '订阅'}
            </button>
          </form>
        )}

        {status === 'error' && <p style={{ fontSize: '12px', color: '#dc2626', marginTop: '8px' }}>{msg}</p>}
        <p style={{ fontSize: '11px', color: 'var(--color-text-label)', marginTop: '12px' }}>我们不会滥用你的邮箱 · 退订一键完成</p>
      </div>
    </div>
  );
}
