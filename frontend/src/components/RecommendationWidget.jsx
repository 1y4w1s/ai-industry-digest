import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

const STORAGE_KEY = 'signal_recommend_closed';

export default function RecommendationWidget({ onNavigate }) {
  const { isLoggedIn } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [closed, setClosed] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) === 'true'; } catch { return false; }
  });
  const [reason, setReason] = useState('');

  useEffect(() => {
    if (!isLoggedIn || closed) return;
    // 延迟请求推荐（不阻塞首屏渲染）
    const timer = setTimeout(() => {
      setLoading(true);
      api.getRecommend(5).then((data) => {
        setItems(data.items || []);
        setReason(data.reason || '');
      }).catch(() => {}).finally(() => setLoading(false));
    }, 3000);
    return () => clearTimeout(timer);
  }, [isLoggedIn, closed]);

  const dismiss = () => {
    setClosed(true);
    try { localStorage.setItem(STORAGE_KEY, 'true'); } catch {}
  };

  if (!isLoggedIn || closed || loading) return null;
  if (items.length === 0) return null;

  const importanceColor = (imp) => {
    const map = { high: '#D4322E', medium: '#C8960A', low: '#8C9096' };
    return map[imp] || map.low;
  };

  return (
    <div className="animate-fade-in" style={{ marginBottom: '16px' }}>
      <div style={{
        background: 'var(--color-bg-off)',
        borderRadius: '4px',
        border: '1px solid var(--color-border-light)',
        padding: '12px 16px',
      }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-title)' }}>为你推荐</span>
            {reason && (
              <span style={{ fontSize: '10px', color: 'var(--color-text-label)' }}>{reason}</span>
            )}
          </div>
          <button onClick={dismiss}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', fontSize: '12px', padding: '2px 4px' }}
            title="关闭">×</button>
        </div>

        {/* Items */}
        <div className="space-y-1.5">
          {items.map((article) => (
            <div key={article.id}
              onClick={() => onNavigate?.(article.id)}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: '8px',
                padding: '6px 8px', borderRadius: '3px', cursor: 'pointer',
                transition: 'background 0.1s',
              }}
              className="hover:bg-[var(--color-bg-hover)]"
            >
              {/* 重要性指示器 */}
              <div style={{
                width: '3px', flexShrink: 0, alignSelf: 'stretch',
                background: importanceColor(article.importance),
                borderRadius: '2px',
              }} />
              <div className="flex-1 min-w-0">
                <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-text-title)', lineHeight: 1.4, marginBottom: '2px' }}>{article.title}</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', lineHeight: 1.3 }}>
                  {article.source_name}
                  {article.tags?.length > 0 && ` · ${article.tags.slice(0, 2).join(' / ')}`}
                </div>
                {article.reason && (
                  <div style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '2px', fontStyle: 'italic' }}>{article.reason}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
