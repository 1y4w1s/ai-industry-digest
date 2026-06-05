import { useState, useRef, useEffect } from 'react';

export default function Select({ value, onChange, options, placeholder, multi }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handle = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [open]);

  const selectedLabel = multi
    ? (value && value.length > 0 ? `${value.length} 个` : placeholder)
    : (value ? options.find(o => o.value === value)?.label : placeholder);

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          padding: '4px 10px',
          fontSize: 'var(--fs-sm)',
          background: 'var(--color-bg-white)',
          border: '1px solid var(--color-border)',
          borderRadius: '4px',
          color: 'var(--color-text-body)',
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          whiteSpace: 'nowrap',
        }}
      >
        {options.find(o => o.value === value)?.dotColor && (
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: options.find(o => o.value === value).dotColor, display: 'inline-block' }} />
        )}
        {selectedLabel || placeholder}
        <svg width="8" height="5" viewBox="0 0 8 5" style={{ transform: open ? 'rotate(180deg)' : 'none' }}>
          <path d="M1 1l3 3 3-3" stroke="var(--color-text-label)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </svg>
      </button>

      {open && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: '0',
            marginTop: '2px',
            background: 'var(--color-bg-white)',
            border: '1px solid var(--color-border)',
            borderRadius: '4px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
            zIndex: 1000,
            minWidth: '140px',
            maxHeight: '200px',
            overflowY: 'auto',
            padding: '4px 0',
          }}
        >
          {options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => {
                if (multi) {
                  const arr = value || [];
                  const next = arr.includes(opt.value) ? arr.filter(v => v !== opt.value) : [...arr, opt.value];
                  onChange(next);
                } else {
                  onChange(opt.value);
                  setOpen(false);
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                width: '100%',
                textAlign: 'left',
                padding: '6px 12px',
                fontSize: 'var(--fs-sm)',
                color: (multi ? (value || []).includes(opt.value) : value === opt.value) ? 'var(--color-text-title)' : 'var(--color-text-body)',
                background: (multi ? (value || []).includes(opt.value) : value === opt.value) ? 'var(--color-bg-hover)' : 'transparent',
                border: 'none',
                cursor: 'pointer',
                transition: 'background 0.1s',
              }}
              onMouseEnter={(e) => e.target.style.background = 'var(--color-bg-off)'}
              onMouseLeave={(e) => e.target.style.background = (multi ? (value || []).includes(opt.value) : value === opt.value) ? 'var(--color-bg-hover)' : 'transparent'}
            >
              {opt.dotColor && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: opt.dotColor, display: 'inline-block' }} />}
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
