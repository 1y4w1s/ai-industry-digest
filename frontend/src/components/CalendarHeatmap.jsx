/**
 * CalendarHeatmap — 月度阅读热力图
 * 纯展示组件，仅接收 heatmap 数据
 */
export default function CalendarHeatmap({ heatmap }) {
  if (!heatmap || Object.keys(heatmap).length === 0) return null;

  const byMonth = {};
  for (const [dateStr, count] of Object.entries(heatmap)) {
    const monthKey = dateStr.slice(0, 7);
    if (!byMonth[monthKey]) byMonth[monthKey] = {};
    byMonth[monthKey][parseInt(dateStr.slice(8))] = count;
  }

  const maxVal = Math.max(...Object.values(heatmap).map(Number), 1);
  const dayHeaders = ['一', '二', '三', '四', '五', '六', '日'];
  const cellSize = 28;

  const bg = (count) => {
    if (!count) return 'var(--color-bg-hover)';
    const i = Math.min(count / maxVal, 1);
    if (i <= 0.25) return '#d4edda';
    if (i <= 0.5) return '#a3d9a5';
    if (i <= 0.75) return '#5cb85c';
    return '#2d7d2d';
  };

  const now = new Date();
  const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  if (!byMonth[monthKey]) return null;

  const [year, month] = monthKey.split('-').map(Number);
  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDay = (new Date(year, month - 1, 1).getDay() + 6) % 7;
  const today = now.getDate();

  const rows = [];
  let row = new Array(firstDay).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    if (d > today) { row.push(null); } else { row.push(byMonth[monthKey]?.[d] ?? 0); }
    if (row.length === 7) { rows.push(row); row = []; }
  }
  if (row.length > 0) { while (row.length < 7) row.push(null); rows.push(row); }

  return (
    <div className="mb-6">
      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
        阅读热力图
      </div>
      <div style={{ border: '1px solid var(--color-border-light)', borderRadius: '6px', padding: '12px', background: 'var(--color-bg-white)' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-title)', marginBottom: '8px' }}>
          {year} 年 {month} 月
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {dayHeaders.map((h) => (
                <th key={h} style={{ width: `${100 / 7}%`, padding: '4px 0', fontSize: '10px', fontWeight: 400, color: 'var(--color-text-label)', textAlign: 'center' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((week, wi) => (
              <tr key={wi}>
                {week.map((val, di) => {
                  const dayNum = wi * 7 + di - firstDay + 1;
                  const cellIsToday = dayNum === today && dayNum > 0 && dayNum <= daysInMonth;
                  return (
                    <td key={di} style={{ padding: '2px', textAlign: 'center' }}>
                      {val !== null ? (
                        <div style={{
                          width: `${cellSize}px`, height: `${cellSize}px`, margin: '0 auto',
                          borderRadius: '4px', background: bg(val),
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '11px', fontWeight: cellIsToday ? 700 : 400,
                          color: val > 0 ? 'white' : 'var(--color-text-body)',
                          border: cellIsToday ? '2px solid var(--color-text-title)' : 'none',
                        }}>
                          {dayNum}
                        </div>
                      ) : null}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex items-center gap-1 mt-2 justify-end" style={{ fontSize: '9px', color: 'var(--color-text-label)' }}>
          <span>少</span>
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: 'var(--color-bg-hover)' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#d4edda' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#a3d9a5' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#5cb85c' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#2d7d2d' }} />
          <span>多</span>
        </div>
      </div>
    </div>
  );
}
