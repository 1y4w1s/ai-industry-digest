import { useState, useRef, useEffect } from 'react';

export default function Select({ value, onChange, options, placeholder, multi }) {
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

  const isMulti = multi && Array.isArray(value);

  // Build trigger label
  const getTriggerLabel = () => {
    if (!isMulti) {
      const selected = options.find((o) => o.value === value);
      return selected ? selected.label : placeholder;
    }
    // Multi-select mode
    const selectedList = options.filter((o) => o.value && value.includes(o.value));
    if (selectedList.length === 0) return placeholder;
    if (selectedList.length <= 2) {
      return selectedList.map((o) => o.label).join(', ');
    }
    return `${selectedList[0].label} 及另外(${selectedList.length - 1})个`;
  };

  const handleSelect = (optValue) => {
    if (!isMulti) {
      onChange(optValue);
      setOpen(false);
      return;
    }
    // Multi-select
    if (optValue === '') {
      // "全部" clicked — clear all
      onChange([]);
      setOpen(false);
      return;
    }
    const current = [...value];
    const idx = current.indexOf(optValue);
    if (idx >= 0) {
      current.splice(idx, 1);
    } else {
      current.push(optValue);
    }
    onChange(current);
    // Keep dropdown open for multi-select
  };

  const label = getTriggerLabel();

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
          color: (!isMulti && value) || (isMulti && value.length > 0) ? '#1A1C1E' : '#8C9096',
          cursor: 'pointer',
          transition: 'background 0.15s',
          whiteSpace: 'nowrap',
          maxWidth: '200px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
        onMouseEnter={(e) => { if (!open) e.target.style.background = '#E4E5E8'; }}
        onMouseLeave={(e) => { if (!open) e.target.style.background = '#EDEEF0'; }}
      >
        {/* Colored dot for importance */}
        {!isMulti && (() => {
          const sel = options.find((o) => o.value === value);
          return sel?.dotColor ? <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: sel.dotColor, flexShrink: 0 }} /> : null;
        })()}
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</span>
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
            minWidth: '180px',
            background: '#FFFFFF',
            border: '1px solid #D8DCE0',
            borderRadius: '6px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            zIndex: 30,
            padding: '4px',
          }}
        >
          {options.map((opt) => {
            const isSelected = isMulti ? value.includes(opt.value) : opt.value === value;
            return (
              <button
                key={opt.value}
                onClick={() => handleSelect(opt.value)}
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
                <span style={{ flex: 1 }}>{opt.label}</span>
                {isSelected && (
                  <svg width="12" height="12" viewBox="0 0 12 12" style={{ flexShrink: 0 }}>
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
