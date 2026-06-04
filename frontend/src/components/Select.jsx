import { useState, useRef, useEffect } from 'react';

export default function Select({ value, onChange, options, placeholder }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handle = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [open]);

  const selected = options.find((o) => o.value === value);

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      {/* Trigger */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          height: '30px',
          padding: '0 10px',
          background: '#EDEEF0',
          border: '1px solid #E8EAED',
          borderRadius: '4px',
          fontSize: '11px',
          color: value ? '#1A1C1E' : '#8C9096',
          cursor: 'pointer',
          transition: 'background 0.15s',
          whiteSpace: 'nowrap',
        }}
        onMouseEnter={(e) => { if (!open) e.target.style.background = '#E4E5E8'; }}
        onMouseLeave={(e) => { if (!open) e.target.style.background = '#EDEEF0'; }}
      >
        {selected?.dotColor && (
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: selected.dotColor, flexShrink: 0 }} />
        )}
        <span>{selected ? selected.label : placeholder}</span>
        <svg width="10" height="6" viewBox="0 0 10 6" style={{ flexShrink: 0, marginLeft: '2px', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
          <path d="M1 1.5l4 4 4-4" stroke="#8C9096" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </svg>
      </button>

      {/* Dropdown */}
      {open && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: '0',
            marginTop: '4px',
            minWidth: '160px',
            background: '#FFFFFF',
            border: '1px solid #D8DCE0',
            borderRadius: '6px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            zIndex: 30,
            padding: '4px',
          }}
        >
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <button
                key={opt.value}
                onClick={() => { onChange(opt.value); setOpen(false); }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  width: '100%',
                  padding: '7px 10px',
                  fontSize: '12px',
                  color: isSelected ? '#1A1C1E' : '#2C2E32',
                  background: isSelected ? '#F0F1F2' : 'transparent',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.1s',
                }}
                onMouseEnter={(e) => { if (!isSelected) e.target.style.background = '#F6F7F8'; }}
                onMouseLeave={(e) => { if (!isSelected) e.target.style.background = 'transparent'; }}
              >
                {opt.dotColor && (
                  <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: opt.dotColor, flexShrink: 0 }} />
                )}
                {opt.dotColor ? (
                  <span>{opt.label}</span>
                ) : (
                  <span>{opt.label}</span>
                )}
                {isSelected && (
                  <svg width="12" height="12" viewBox="0 0 12 12" style={{ marginLeft: 'auto', flexShrink: 0 }}>
                    <path d="M2.5 6l2.5 3 4.5-5" stroke="#1A1C1E" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
