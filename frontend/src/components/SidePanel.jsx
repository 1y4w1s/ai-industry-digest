import { api } from '../api/client';

export default function SidePanel({ keywords = [], insight = '', topArticles = [], onArticleClick, onAskAI }) {
  const handleQuickAsk = (question) => {
    if (onAskAI) onAskAI(question);
  };

  return (
    <div className="side-panel animate-fade-in">
      {/* 🔥 今日热点 */}
      {keywords.length > 0 && (
        <div className="side-panel-section">
          <h3 className="font-heading font-semibold text-xs text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-sm">🔥</span> 今日热点
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {keywords.map((k) => (
              <span
                key={k}
                className="px-2.5 py-1 text-xs rounded-full transition-all cursor-pointer hover:brightness-110"
                style={{ background: 'rgba(99,149,255,0.08)', color: '#6395FF', border: '1px solid rgba(99,149,255,0.2)' }}
                onClick={() => handleQuickAsk(`聊聊 "${k}" 相关的新闻`)}
              >
                {k}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 📊 趋势速览 */}
      {insight && (
        <div className="side-panel-section">
          <h3 className="font-heading font-semibold text-xs text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-sm">📊</span> 趋势速览
          </h3>
          <p className="text-xs leading-relaxed" style={{ color: '#9197C2', lineHeight: '1.7' }}>
            {insight.length > 150 ? insight.slice(0, 150) + '...' : insight}
          </p>
          <button
            onClick={() => handleQuickAsk('详细分析今天的趋势')}
            className="text-xs mt-2 transition-all hover:brightness-110"
            style={{ color: '#6395FF' }}
          >
            完整分析 →
          </button>
        </div>
      )}

      {/* ⭐ 今日 Top 3 */}
      {topArticles.length > 0 && (
        <div className="side-panel-section">
          <h3 className="font-heading font-semibold text-xs text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-sm">⭐</span> 今日 Top {Math.min(3, topArticles.length)}
          </h3>
          <div className="space-y-2">
            {topArticles.slice(0, 3).map((a, i) => (
              <div
                key={a.id || a.url}
                onClick={() => onArticleClick(a.id)}
                className="flex items-start gap-2.5 cursor-pointer group transition-all"
              >
                <span
                  className="flex-shrink-0 w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold mt-0.5"
                  style={{ background: i === 0 ? 'rgba(99,149,255,0.15)' : 'rgba(99,149,255,0.08)', color: '#6395FF' }}
                >
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs leading-relaxed transition-colors group-hover:text-accent" style={{ color: '#E2E6F9' }}>
                    {a.title}
                  </p>
                  <span className="text-[10px]" style={{ color: '#6E739C' }}>{a.source_name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 🤖 AI 快捷提问 */}
      <div className="side-panel-section pt-2" style={{ borderTop: '1px solid #2E2F4F' }}>
        <h3 className="font-heading font-semibold text-xs text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
          <span className="text-sm">🤖</span> AI 快捷提问
        </h3>
        <div className="flex flex-wrap gap-2">
          {['今天有什么大新闻？', '分析最新融资趋势', '推荐值得看的文章'].map((q) => (
            <button
              key={q}
              onClick={() => handleQuickAsk(q)}
              className="px-3 py-1.5 text-xs rounded-lg transition-all hover:brightness-110"
              style={{ background: '#23243E', color: '#9197C2', border: '1px solid #2E2F4F' }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
