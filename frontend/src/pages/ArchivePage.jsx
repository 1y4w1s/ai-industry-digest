import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

const MONTHS = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月'];
const DAY_HEADERS = ['一','二','三','四','五','六','日'];

function Calendar({ dates, loading, onSelectDate }) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());

  const dateSet = new Set(dates);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = (new Date(year, month, 1).getDay() + 6) % 7;

  const rows = [];
  let row = Array(firstDay).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    row.push({ day: d, hasReport: dateSet.has(dateStr), dateStr });
    if (row.length === 7) { rows.push(row); row = []; }
  }
  if (row.length > 0) { while (row.length < 7) row.push(null); rows.push(row); }

  const prevMonth = () => { if (month === 0) { setYear(y => y - 1); setMonth(11); } else setMonth(m => m - 1); };
  const nextMonth = () => { if (month === 11) { setYear(y => y + 1); setMonth(0); } else setMonth(m => m + 1); };

  return (
    <div>
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={prevMonth} style={{ background: 'none', border: '1px solid var(--color-border)', borderRadius: '4px', padding: '6px 12px', cursor: 'pointer', color: 'var(--color-text-body)', fontSize: '12px' }}>← 上月</button>
        <h2 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '18px', fontWeight: 700, color: 'var(--color-text-title)' }}>{year} 年 {MONTHS[month]}</h2>
        <button onClick={nextMonth} style={{ background: 'none', border: '1px solid var(--color-border)', borderRadius: '4px', padding: '6px 12px', cursor: 'pointer', color: 'var(--color-text-body)', fontSize: '12px' }}>下月 →</button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="flex gap-1.5 justify-center mb-3">
            <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
            <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
            <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
          </div>
          <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>加载中...</span>
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {DAY_HEADERS.map((h) => (
                <th key={h} style={{ padding: '8px 0', fontSize: '11px', fontWeight: 500, color: 'var(--color-text-muted)', textAlign: 'center', borderBottom: '1px solid var(--color-border-light)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((week, wi) => (
              <tr key={wi}>
                {week.map((cell, di) => (
                  <td key={di} style={{ padding: '2px', textAlign: 'center', border: '1px solid var(--color-border-light)', width: `${100 / 7}%`, height: '50px', verticalAlign: 'top' }}>
                    {cell ? (
                      <button onClick={() => onSelectDate(cell.dateStr)}
                        disabled={!cell.hasReport}
                        style={{
                          width: '100%', height: '100%', minHeight: '40px',
                          border: 'none', borderRadius: '4px', cursor: cell.hasReport ? 'pointer' : 'default',
                          background: cell.hasReport ? 'rgba(40,100,168,0.08)' : 'transparent',
                          color: cell.hasReport ? 'var(--color-blue-link)' : 'var(--color-text-label)',
                          fontWeight: cell.hasReport ? 600 : 400,
                          fontSize: '13px',
                          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                          transition: 'background 0.15s',
                        }}
                        onMouseEnter={(e) => { if (cell.hasReport) e.target.style.background = 'rgba(40,100,168,0.15)'; }}
                        onMouseLeave={(e) => { if (cell.hasReport) e.target.style.background = 'rgba(40,100,168,0.08)'; }}>
                        {cell.day}
                        {cell.hasReport && (
                          <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--color-blue-link)', marginTop: '2px' }} />
                        )}
                      </button>
                    ) : null}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function ArchivePage() {
  const navigate = useNavigate();
  const [dates, setDates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getReportDates()
      .then((data) => { setDates(data.dates || []); setLoading(false); })
      .catch(() => { setDates([]); setLoading(false); });
  }, []);

  const handleSelectDate = (dateStr) => {
    navigate(`/?date=${dateStr}`);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-8 py-6" style={{ maxWidth: '700px', margin: '0 auto' }}>
          <button onClick={() => navigate('/')} style={{ fontSize: '12px', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0, marginBottom: '20px' }}>
            ← 返回首页
          </button>

          <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '22px', fontWeight: 700, color: 'var(--color-text-title)', marginBottom: '4px' }}>
            日报归档
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '24px' }}>
            共 {dates.length} 期日报 · 点击有标记的日期查看
          </p>

          <div style={{ border: '1px solid var(--color-border-light)', borderRadius: '8px', padding: '20px', background: 'var(--color-bg-white)' }}>
            <Calendar dates={dates} loading={loading} onSelectDate={handleSelectDate} />
          </div>
        </div>
      </div>
    </div>
  );
}
