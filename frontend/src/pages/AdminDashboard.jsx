/**
 * Signal - 管理员数据看板
 * 展示系统统计信息
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, Users, FileText, Bookmark, TrendingUp, Activity } from 'lucide-react';
import { client } from '../api/client';

// 统计卡片组件
function StatsCard({ title, value, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );
}

// 热门文章列表组件
function PopularArticles({ articles }) {
  if (!articles?.length) return null;

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-blue-500" />
        热门文章
      </h3>
      <div className="space-y-3">
        {articles.map((article, index) => (
          <div key={article.id} className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded">
            <span className="text-sm font-medium text-gray-400 w-6">{index + 1}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{article.title}</p>
              <p className="text-xs text-gray-500">{article.source}</p>
            </div>
            <span className="text-sm text-blue-600 font-medium">{article.read_count} 次阅读</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// 来源分布组件
function SourceDistribution({ sources }) {
  if (!sources?.length) return null;

  const maxCount = Math.max(...sources.map(s => s.count));

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-green-500" />
        来源分布
      </h3>
      <div className="space-y-3">
        {sources.slice(0, 10).map(source => (
          <div key={source.source} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">{source.source}</span>
              <span className="font-medium">{source.count}</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 rounded-full"
                style={{ width: `${(source.count / maxCount) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [popularArticles, setPopularArticles] = useState([]);
  const [sourceDistribution, setSourceDistribution] = useState([]);

  useEffect(() => {
    // 检查登录状态
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    // 获取统计数据
    Promise.all([
      client.get('/api/admin/stats/overview'),
      client.get('/api/admin/stats/articles/popular?limit=10'),
      client.get('/api/admin/stats/articles'),
    ])
      .then(([overview, popular, articles]) => {
        setStats(overview);
        setPopularArticles(popular);
        setSourceDistribution(articles.source_distribution);
      })
      .catch(err => {
        console.error('获取统计数据失败:', err);
        if (err.status === 401) {
          navigate('/login');
        }
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 标题 */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">管理员数据看板</h1>
          <p className="text-gray-500 mt-1">系统运行数据概览</p>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="用户总数"
            value={stats?.total_users || 0}
            icon={Users}
            color="text-blue-600"
          />
          <StatsCard
            title="文章总数"
            value={stats?.total_articles || 0}
            icon={FileText}
            color="text-green-600"
          />
          <StatsCard
            title="收藏总数"
            value={stats?.total_bookmarks || 0}
            icon={Bookmark}
            color="text-orange-600"
          />
          <StatsCard
            title="今日活跃"
            value={stats?.daily_active_users || 0}
            icon={Activity}
            color="text-purple-600"
          />
        </div>

        {/* 图表区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PopularArticles articles={popularArticles} />
          <SourceDistribution sources={sourceDistribution} />
        </div>

        {/* 底部信息 */}
        <div className="mt-8 text-center text-sm text-gray-400">
          数据更新时间: {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
}
