import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// 侧栏底部"最近浏览"模块
// 数据源：localStorage 'signal.recent.v1'（由 ArticleReader/Home 阅读时写入）
// 形态：4 条最近文章标题，点击直达；失败/空 静默不渲染
const STORAGE_KEY = 'signal.recent.v1';
const MAX_ITEMS = 4;

export default function RecentItems({ onItemClick }) {
  const [items, setItems] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const arr = JSON.parse(raw);
      if (Array.isArray(arr) && arr.length > 0) {
        setItems(arr.slice(0, MAX_ITEMS));
      }
    } catch {}
  }, []);

  if (items.length === 0) return null;

  const handleClick = (item) => {
    if (onItemClick) onItemClick();
    navigate(`/?article=${encodeURIComponent(item.id)}`);
  };

  return (
    <div style={{ borderTop: '1px solid var(--color-border-light)', padding: '12px 12px 16px' }}>
      <div
        style={{
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: 'var(--color-text-label)',
          padding: '0 8px 8px',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
        最近浏览
      </div>
      <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {items.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => handleClick(item)}
              title={item.title}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: '8px 10px',
                fontSize: 12,
                lineHeight: 1.4,
                color: 'var(--color-text-body)',
                background: 'transparent',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
                transition: 'background 0.12s',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 6,
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-border-light)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
            >
              <span style={{ flexShrink: 0, color: 'var(--color-text-label)', fontSize: 10, fontWeight: 600, lineHeight: 1.5, marginTop: 1 }}>•</span>
              <span style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}>{item.title || `文章 ${item.id.slice(0, 12)}…`}</span>
            </button>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() => { if (onItemClick) onItemClick(); navigate('/history'); }}
        style={{
          width: '100%',
          marginTop: 8,
          padding: '6px 8px',
          fontSize: 11,
          color: 'var(--color-blue-link)',
          background: 'transparent',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer',
          textAlign: 'center',
        }}
      >
        查看全部历史 →
      </button>
    </div>
  );
}
