import { useState, useRef, useEffect } from 'react';
import { getDateLabel } from '../utils/date';

const VISIBLE_DEFAULT = 3;
const VISIBLE_EXPANDED = 7;

export default function DateNav({ reports, selectedDate, onSelect }) {
  const [showAll, setShowAll] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (!showDropdown) return;
    const handleClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [showDropdown]);

  if (!reports || reports.length === 0) return null;

  const visibleCount = showAll ? VISIBLE_EXPANDED : VISIBLE_DEFAULT;
  const visibleReports = reports.slice(0, visibleCount);
  const hiddenReports = reports.slice(VISIBLE_EXPANDED);

  const handleSelect = (date) => {
    onSelect(date);
    setShowAll(false);
    setShowDropdown(false);
  };

  return (
    <div className="mb-5">
      <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: 'var(--fs-xl)', fontWeight: 700, color: 'var(--color-text-title)', marginBottom: '12px' }}>
        每日简报
      </h1>
      <div className="flex items-center gap-1 overflow-x-auto whitespace-nowrap pb-1 scrollbar-none lg:flex-wrap lg:overflow-visible">
        {visibleReports.map((r) => {
          const label = getDateLabel(r.report_date);
          const isSelected = selectedDate === r.report_date;
          return (
            <button
              key={r.report_date}
              onClick={() => handleSelect(r.report_date)}
              style={{
                padding: '6px 14px',
                background: isSelected ? 'var(--color-border-light)' : 'transparent',
                borderRadius: '4px',
                color: isSelected ? 'var(--color-text-title)' : 'var(--color-text-muted)',
                fontWeight: isSelected ? 500 : 400,
                fontSize: 'var(--fs-sm)',
                transition: 'all 0.15s ease',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              <span>{label}</span>
              {(label === '今天' || label === '昨天' || label === '前天') && (
                <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--color-text-label)', marginLeft: '4px' }}>{r.report_date.slice(5)}</span>
              )}
            </button>
          );
        })}

        {reports.length > VISIBLE_DEFAULT && !showAll && (
          <button
            onClick={() => setShowAll(true)}
            style={{
              padding: '6px 8px',
              fontSize: 'var(--fs-sm)',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              background: 'none',
              border: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '2px',
            }}
          >
            展开
            <svg width="10" height="6" viewBox="0 0 10 6" style={{ marginTop: '1px' }}>
              <path d="M1 1l4 4 4-4" stroke="var(--color-text-muted)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            </svg>
          </button>
        )}

        {reports.length > VISIBLE_EXPANDED && showAll && hiddenReports.length > 0 && (
          <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-block' }}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              style={{
                padding: '6px 8px',
                fontSize: 'var(--fs-sm)',
                color: 'var(--color-text-muted)',
                cursor: 'pointer',
                background: showDropdown ? 'var(--color-border-light)' : 'transparent',
                border: 'none',
                borderRadius: '4px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '2px',
              }}
            >
              更早
              <svg width="10" height="6" viewBox="0 0 10 6" style={{ marginTop: '1px' }}>
                <path d="M1 1l4 4 4-4" stroke="var(--color-text-muted)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
              </svg>
            </button>

            {showDropdown && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: '0',
                  marginTop: '4px',
                  background: 'var(--color-bg-white)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '6px',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
                  zIndex: 30,
                  minWidth: '200px',
                  maxHeight: '280px',
                  overflowY: 'auto',
                  padding: '6px 0',
                }}
              >
                <div style={{ padding: '6px 14px 4px', fontSize: 'var(--fs-xs)', color: 'var(--color-text-label)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  选择日期
                </div>
                {hiddenReports.map((r) => {
                  const d = new Date(r.report_date);
                  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
                  const display = `${r.report_date} 周${weekdays[d.getDay()]}`;
                  const isSelected = selectedDate === r.report_date;
                  return (
                    <button
                      key={r.report_date}
                      onClick={() => handleSelect(r.report_date)}
                      style={{
                        display: 'block',
                        width: '100%',
                        textAlign: 'left',
                        padding: '7px 14px',
                        fontSize: 'var(--fs-sm)',
                        color: isSelected ? 'var(--color-text-title)' : 'var(--color-text-body)',
                        background: isSelected ? 'var(--color-bg-hover)' : 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        transition: 'background 0.1s',
                      }}
                      onMouseEnter={(e) => { if (!isSelected) e.target.style.background = 'var(--color-bg-off)'; }}
                      onMouseLeave={(e) => { if (!isSelected) e.target.style.background = 'transparent'; }}
                    >
                      {display}
                    </button>
                  );
                })}
                <div style={{ padding: '6px 14px 2px', fontSize: 'var(--fs-xs)', color: 'var(--color-text-label)', borderTop: '1px solid var(--color-border-light)', marginTop: '4px', paddingTop: '6px' }}>
                  共 {reports.length} 期
                </div>
              </div>
            )}
          </div>
        )}

        {showAll && reports.length <= VISIBLE_EXPANDED && (
          <button
            onClick={() => setShowAll(false)}
            style={{
              padding: '6px 8px',
              fontSize: 'var(--fs-sm)',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              background: 'none',
              border: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '2px',
            }}
          >
            收起
            <svg width="10" height="6" viewBox="0 0 10 6" style={{ marginTop: '1px', transform: 'rotate(180deg)' }}>
              <path d="M1 1l4 4 4-4" stroke="var(--color-text-muted)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
