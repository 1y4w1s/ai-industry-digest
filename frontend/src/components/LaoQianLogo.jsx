/**
 * LaoQian Logo — 捞乾品牌标识
 *
 * 图形：菱形渔网 + 金色圆点
 *   三条斜线交织 = 从 AI 信息海中打捞干货
 *   金色圆点 = 干货/金粒（谐音"捞乾/捞钱"）
 *   菱形结构 = 抽象的 "K"（乾）
 *
 * Props:
 *   size:    图形尺寸（默认 28）
 *   showText: 是否显示"捞乾"字标（默认 true）
 *   color:   网线颜色（默认 --color-brass）
 */
export default function LaoQianLogo({ size = 28, showText = true, color }) {
  const strokeColor = color || 'var(--color-brass)';
  const dotColor = color || 'var(--color-brass)';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: showText ? 8 : 0 }}>
      <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
        {/* 菱形网 */}
        <path d="M4 4 L16 16 L28 4" stroke={strokeColor} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M4 16 L16 28 L28 16" stroke={strokeColor} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M16 4 L4 16 L16 28" stroke={strokeColor} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M16 4 L28 16 L16 28" stroke={strokeColor} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        {/* 金色圆点 */}
        <circle cx="16" cy="16" r="4" fill={dotColor}/>
        <circle cx="16" cy="16" r="2.5" fill="#F5E6B0"/>
      </svg>
      {showText && (
        <span className="logo logo-lg" style={{
          fontFamily: 'var(--font-display)',
          fontSize: size * 0.64,
          fontWeight: 700,
          letterSpacing: '0.06em',
          color: 'var(--color-text-title)',
          lineHeight: 1,
        }}>
          捞乾
        </span>
      )}
    </div>
  );
}
