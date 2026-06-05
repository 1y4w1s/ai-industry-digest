import { useTheme } from '../context/ThemeContext';

const THEME_OPTIONS = [
  {
    value: 'light', label: '浅色模式',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>,
  },
  {
    value: 'dark', label: '深色模式',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>,
  },
];

const FONT_OPTIONS = [
  { value: 'small', label: '小', desc: '12px' },
  { value: 'medium', label: '中', desc: '15px（默认）' },
  { value: 'large', label: '大', desc: '18px' },
];

function RadioGroup({ label, options, value, onChange }) {
  return (
    <div className="mb-6">
      <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
        {label}
      </label>
      <div className="flex gap-2 flex-wrap">
        {options.map((opt) => {
          const isSelected = value === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => {
                console.log(`[SettingsPage] RadioGroup "${label}" | clicked: ${opt.value} | current selected: ${value} | DOM data-font-size before: ${document.documentElement.getAttribute('data-font-size')}`);
                onChange(opt.value);
                console.log(`[SettingsPage] RadioGroup "${label}" | after onChange | DOM data-font-size: ${document.documentElement.getAttribute('data-font-size')}`);
              }}
              style={{
                padding: '10px 16px',
                fontSize: '13px',
                fontWeight: isSelected ? 500 : 400,
                background: isSelected ? 'var(--color-text-title)' : 'transparent',
                color: isSelected ? 'var(--color-bg-white)' : 'var(--color-text-body)',
                border: isSelected ? '1px solid var(--color-text-title)' : '1px solid var(--color-border)',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.15s',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span style={{ width: '16px', height: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: isSelected ? 1 : 0.6 }}>
                {opt.icon}
              </span>
              <span>{opt.label}</span>
              {opt.desc && <span style={{ fontSize: '11px', opacity: 0.7 }}>({opt.desc})</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { themeMode, updateThemeMode, fontSize, updateFontSize } = useTheme();
  console.log(`[SettingsPage] render | themeMode="${themeMode}" fontSize="${fontSize}" | DOM data-font-size="${document.documentElement.getAttribute('data-font-size')}"`);

  // If current themeMode is 'system', auto-convert to resolved on first visit
  const displayTheme = themeMode === 'system' ? 'light' : themeMode;

  return (
    <div className="h-full animate-fade-in" style={{ background: 'var(--color-bg-white)' }}>
      <div className="px-5 lg:px-6" style={{ paddingTop: '28px', paddingBottom: '32px', maxWidth: '560px', margin: '0 auto' }}>
        <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)', marginBottom: '4px' }}>
          设置
        </h1>
        <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '28px' }}>
          自定义您的阅读体验
        </p>

        <div style={{ background: 'var(--color-bg-white)', borderRadius: '8px', padding: '24px', border: '1px solid var(--color-border-light)' }}>
          <RadioGroup
            label="显示主题"
            options={THEME_OPTIONS}
            value={displayTheme}
            onChange={updateThemeMode}
          />

          <div style={{ height: '1px', background: 'var(--color-border-light)', marginBottom: '24px' }} />

          <RadioGroup
            label="正文字号"
            options={FONT_OPTIONS}
            value={fontSize}
            onChange={updateFontSize}
          />
        </div>

        <p style={{ fontSize: '11px', color: 'var(--color-text-label)', marginTop: '16px', textAlign: 'center' }}>
          偏好设置自动保存在浏览器中
        </p>
      </div>
    </div>
  );
}
