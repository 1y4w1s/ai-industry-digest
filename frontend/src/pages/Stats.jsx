import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getStats(), api.getReports(1, 100)])
      .then(([s, r]) => {
        setStats({ ...s, reportCount: r.total || 0 });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center text-text-tertiary py-12 text-sm">加载中...</div>;
  if (!stats) return <div className="text-center text-text-tertiary py-12 text-sm">加载失败</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-heading text-xl font-bold text-text-primary">数据统计</h1>
        <p className="text-sm text-text-secondary mt-1">系统整体运行概况</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: '文章总数', value: stats.total_articles || 0, icon: '📦', color: 'accent' },
          { label: '日报数', value: stats.reportCount || 0, icon: '📰', color: 'success' },
          { label: '信息源', value: stats.sources?.length || 0, icon: '📡', color: 'warning' },
          { label: '标签', value: stats.tags?.length || 0, icon: '🏷️', color: 'text-primary' },
        ].map((card) => (
          <div key={card.label} className="bg-bg-surface border border-border-primary rounded-2xl p-5">
            <div className="text-2xl mb-2">{card.icon}</div>
            <div className={`text-3xl font-heading font-bold text-${card.color}`}>{card.value}</div>
            <div className="text-xs text-text-tertiary mt-1">{card.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-bg-surface border border-border-primary rounded-2xl p-5">
          <h2 className="font-heading font-semibold text-sm text-text-primary mb-3">📡 信息源</h2>
          <div className="flex flex-wrap gap-2">
            {stats.sources?.map((s) => (
              <span key={s} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary">{s}</span>
            ))}
          </div>
        </div>
        <div className="bg-bg-surface border border-border-primary rounded-2xl p-5">
          <h2 className="font-heading font-semibold text-sm text-text-primary mb-3">🏷️ 标签</h2>
          <div className="flex flex-wrap gap-2">
            {stats.tags?.map((t) => (
              <span key={t} className="px-3 py-1.5 bg-accent/10 border border-accent/20 rounded-lg text-xs text-accent">{t}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
