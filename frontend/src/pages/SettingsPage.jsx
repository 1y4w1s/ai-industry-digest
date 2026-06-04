import { useTheme } from '../context/ThemeContext';

const THEME_OPTIONS = [
  { value: 'light', label: '浅色模式', icon: '☀️' },
  { value: 'dark', label: '深色模式', icon: '🌙' },
  { value: 'system', label: '跟随系统', icon: '💻' },
];

const FONT_OPTIONS = [
  { value: 'small', label: '小', desc: '13px' },
  { value: 'medium', label: '中', desc: '15px' },
  { value: 'large', label: '大', desc: '17px' },
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
              onClick={() => onChange(opt.value)}
              style={{
                padding: '10px 16px',
                fontSize: '13px',
                fontWeight: isSelected ? 500 : 400,
                background: isSelected ? 'var(--color-text-title)' : 'var(--color-bg-off)',
                color: isSelected ? 'var(--color-bg-white)' : 'var(--color-text-body)',
                border: isSelected ? '1px solid var(--color-text-title)' : '1px solid var(--color-border-light)',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.15s',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {opt.icon && <span>{opt.icon}</span>}
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
            value={themeMode}
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
