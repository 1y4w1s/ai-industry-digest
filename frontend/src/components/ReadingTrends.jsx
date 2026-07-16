/**
 * ReadingTrends — 阅读趋势统计
 * 纯展示组件，仅接收 trends 数据
 */
export default function ReadingTrends({ trends }) {
  if (!trends) return null;

  const { monthly_trend, peak_hour, avg_read_length } = trends;
  const maxCount = Math.max(...(monthly_trend || []).map((m) => m.count), 1);
  const chartW = 400;
  const chartH = 180;
  const pad = { top: 16, right: 8, bottom: 24, left: 8 };

  const xScale = (i) => pad.left + (i / Math.max((monthly_trend?.length || 1) - 1, 1)) * (chartW - pad.left - pad.right);
  const yScale = (v) => pad.top + (1 - v / maxCount) * (chartH - pad.top - pad.bottom);

  const points = (monthly_trend || []).map((m, i) => ({
    x: xScale(i), y: yScale(m.count), label: m.month.slice(5), count: m.count,
  }));

  return (
    <div className="mb-6">
      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
        阅读趋势
      </div>
      <div style={{ border: '1px solid var(--color-border-light)', borderRadius: '6px', padding: '16px', background: 'var(--color-bg-white)' }}>
        <svg viewBox={`0 0 ${chartW} ${chartH}`} style={{ width: '100%', height: 'auto' }}>
          {/* Grid lines */}
          {[0.25, 0.5, 0.75, 1].map((r) => (
            <line key={r} x1={pad.left} y1={yScale(r * maxCount)} x2={chartW - pad.right} y2={yScale(r * maxCount)} stroke="var(--color-border-light)" strokeWidth="1" />
          ))}
          {/* Line */}
          <polyline
            fill="none" stroke="var(--color-brass)" strokeWidth="2" strokeLinejoin="round"
            points={points.map((p) => `${p.x},${p.y}`).join(' ')}
          />
          {/* Dots */}
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="3" fill="var(--color-brass)" stroke="var(--color-bg-white)" strokeWidth="1.5" />
          ))}
          {/* Labels */}
          {points.map((p, i) => (
            <text key={i} x={p.x} y={chartH - 2} textAnchor="middle" fontSize="8" fill="var(--color-text-label)">{p.label}</text>
          ))}
        </svg>
        <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', marginTop: '12px', fontSize: '12px', color: 'var(--color-text-body)' }}>
          <div>⏰ 阅读高峰：<strong>{peak_hour ?? '-'} 时</strong></div>
          <div>📄 平均篇幅：<strong>{avg_read_length ? `${Math.round(avg_read_length / 100) * 100} 字` : '-'}</strong></div>
        </div>
      </div>
    </div>
  );
}
