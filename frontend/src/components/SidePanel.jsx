export default function SidePanel({ keywords = [], insight = '', topArticles = [], onArticleClick, onAskAI }) {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* 🔥 今日热点 */}
      {keywords.length > 0 && (
        <div style={{ borderRadius: '4px', padding: '16px', background: '#F6F7F8' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: '#686C72' }}>
            <span style={{ marginRight: '6px' }}>🔥</span> 今日热点
          </h3>
          <div className="flex flex-wrap gap-2">
            {keywords.map((k) => (
              <span key={k} className="px-2.5 py-1 text-xs rounded-full cursor-pointer hover:brightness-95" style={{ background: '#E8EAED', color: '#2C2E32' }}>
                {k}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 📊 趋势速览 */}
      {insight && (
        <div style={{ borderRadius: '4px', padding: '16px', background: '#F6F7F8' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: '#686C72' }}>
            <span style={{ marginRight: '6px' }}>📊</span> 趋势速览
          </h3>
          <p className="text-xs leading-relaxed" style={{ color: '#2C2E32', lineHeight: '1.7' }}>
            {insight.length > 200 ? insight.slice(0, 200) + '...' : insight}
          </p>
        </div>
      )}

      {/* ⭐ Top 5 */}
      {topArticles.length > 0 && (
        <div style={{ borderRadius: '4px', padding: '16px', background: '#F6F7F8' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: '#686C72' }}>
            <span style={{ marginRight: '6px' }}>⭐</span> Top {Math.min(5, topArticles.length)}
          </h3>
          <div className="space-y-2.5">
            {topArticles.slice(0, 5).map((a, i) => (
              <div key={a.id || a.url} onClick={() => onArticleClick(a.id)} className="flex items-start gap-2.5 cursor-pointer group transition-all">
                <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-[10px] font-bold rounded" style={{ background: i < 3 ? '#E8EAED' : '#F0F1F2', color: '#686C72' }}>{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs leading-relaxed group-hover:text-blue-link transition-colors" style={{ color: '#1A1C1E' }}>{a.title}</p>
                  <span className="text-[10px]" style={{ color: '#8C9096' }}>{a.source_name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 📡 来源分布 */}
      {keywords.length > 0 && (
        <div style={{ borderRadius: '4px', padding: '16px', background: '#F6F7F8' }}>
          <h3 className="font-heading font-semibold text-xs uppercase tracking-wider mb-3" style={{ color: '#686C72' }}>
            <span style={{ marginRight: '6px' }}>📡</span> 来源分布
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {['arXiv', '量子位', '36氪', '机器之心'].map((s) => (
              <span key={s} className="px-2 py-1 text-xs rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
