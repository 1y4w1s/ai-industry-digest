/**
 * Signal - 管理员数据看板
 * 展示业务统计 + 系统监控（F-15）综合数据
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3, Users, FileText, Bookmark, TrendingUp, Activity,
  Search, Clock, AlertTriangle, Target, Zap, Route, Compress, List
} from 'lucide-react';
import { getToken } from '../lib/token';
import { useAuth } from '../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function adminRequest(path) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  });
  if (!res.ok) {
    throw new Error(`请求失败: ${res.status}`);
  }
  return res.json();
}

// ── 通用组件 ──────────────────────────────

function StatsCard({ title, value, icon: Icon, color, subtitle }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );
}

function LatencyCard({ label, value, unit, color }) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}<span className="text-sm font-normal text-gray-400 ml-1">{unit}</span></p>
    </div>
  );
}

function ProgressBar({ label, value, max, color = 'bg-blue-500' }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600 truncate">{label}</span>
        <span className="font-medium ml-2">{value}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── 热门文章 ──────────────────────────────

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

// ── 来源分布 ──────────────────────────────

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
              <div className="h-full bg-green-500 rounded-full" style={{ width: `${(source.count / maxCount) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 路由分布 ──────────────────────────────

function RouteDistribution({ routing }) {
  if (!routing || !Object.keys(routing).length) return null;
  const maxVal = Math.max(...Object.values(routing), 1);
  const colors = ['bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-teal-500', 'bg-yellow-500', 'bg-gray-500'];
  let i = 0;
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Route className="w-5 h-5 text-purple-500" />
        检索意图分布
      </h3>
      <div className="space-y-3">
        {Object.entries(routing).map(([route, count]) => {
          const color = colors[i++ % colors.length];
          return <ProgressBar key={route} label={route} value={count} max={maxVal} color={color} />;
        })}
      </div>
    </div>
  );
}

// ── 压缩效果 ──────────────────────────────

function CompressionStats({ compression }) {
  if (!compression || !compression.avg_ratio) return null;
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Compress className="w-5 h-5 text-cyan-500" />
        上下文压缩效果
      </h3>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-cyan-600">{(compression.avg_ratio * 100).toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">平均压缩比</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-cyan-600">{compression.avg_compressed_chars}</p>
          <p className="text-xs text-gray-500 mt-1">平均压缩后字符</p>
        </div>
      </div>
      {compression.mode_distribution && Object.keys(compression.mode_distribution).length > 0 && (
        <>
          <p className="text-xs text-gray-500 mb-2">压缩模式分布</p>
          {Object.entries(compression.mode_distribution).map(([mode, count]) => (
            <ProgressBar key={mode} label={mode} value={count} max={Math.max(...Object.values(compression.mode_distribution))} color="bg-cyan-500" />
          ))}
        </>
      )}
    </div>
  );
}

// ── 错误统计 ──────────────────────────────

function ErrorStats({ errors }) {
  if (!errors || !errors.top?.length) return null;
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-red-500" />
        常见错误（TOP 5）
      </h3>
      <div className="space-y-2">
        {errors.top.map((err, i) => (
          <div key={i} className="flex items-center justify-between p-2 bg-red-50 rounded text-sm">
            <span className="text-red-700 truncate flex-1 mr-2">{err.msg}</span>
            <span className="text-red-500 font-medium flex-shrink-0">{err.count} 次</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 主页面 ────────────────────────────────

const ADMIN_USER = '1y4w1s';

export default function AdminDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [popularArticles, setPopularArticles] = useState([]);
  const [sourceDistribution, setSourceDistribution] = useState([]);
  const [monitor, setMonitor] = useState(null);
  const [activeTab, setActiveTab] = useState('business');

  useEffect(() => {
    const isAdmin = user?.user_metadata?.nickname === ADMIN_USER || user?.email?.startsWith(ADMIN_USER);
    if (!isAdmin) {
      navigate('/');
      return;
    }
    const token = getToken();
    if (!token) {
      navigate('/login');
      return;
    }

    Promise.all([
      adminRequest('/admin/stats/overview'),
      adminRequest('/admin/stats/articles/popular?limit=10'),
      adminRequest('/admin/stats/articles'),
      fetch(`${API_BASE}/monitor/dashboard?days=7`).then(r => r.json()),
    ])
      .then(([overview, popular, articles, monitorData]) => {
        setStats(overview);
        setPopularArticles(popular);
        setSourceDistribution(articles.source_distribution);
        setMonitor(monitorData);
      })
      .catch(err => {
        console.error('获取数据失败:', err);
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

  const s = monitor?.summary || {};
  const errorRate = s.error_rate != null ? (s.error_rate * 100).toFixed(2) : '—';
  const zeroRate = s.zero_result_rate != null ? (s.zero_result_rate * 100).toFixed(2) : '—';

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">管理员数据看板</h1>
          <p className="text-gray-500 mt-1">业务统计 + 系统监控 · 综合概览</p>
        </div>

        {/* Tab 切换 */}
        <div className="flex gap-1 mb-6 bg-white rounded-lg p-1 shadow-sm border inline-flex">
          <button
            onClick={() => setActiveTab('business')}
            className={`px-4 py-2 text-sm rounded-md transition ${activeTab === 'business' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
          >
            业务数据
          </button>
          <button
            onClick={() => setActiveTab('monitor')}
            className={`px-4 py-2 text-sm rounded-md transition ${activeTab === 'monitor' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
          >
            系统监控
          </button>
        </div>

        {/* ── Tab: 业务数据 ───────────────── */}
        {activeTab === 'business' && (
          <>
            {/* 业务统计卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatsCard title="用户总数" value={stats?.total_users || 0} icon={Users} color="text-blue-600" />
              <StatsCard title="文章总数" value={stats?.total_articles || 0} icon={FileText} color="text-green-600" />
              <StatsCard title="收藏总数" value={stats?.total_bookmarks || 0} icon={Bookmark} color="text-orange-600" />
              <StatsCard title="今日活跃" value={stats?.daily_active_users || 0} icon={Activity} color="text-purple-600" />
            </div>

            {/* 本周新增 + 总阅读 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <StatsCard title="本周新增文章" value={stats?.articles_this_week || 0} icon={FileText} color="text-emerald-600" subtitle="过去 7 天入库" />
              <StatsCard title="总阅读次数" value={stats?.total_reads || 0} icon={TrendingUp} color="text-rose-600" subtitle="累计阅读记录" />
            </div>

            {/* 图表区域 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PopularArticles articles={popularArticles} />
              <SourceDistribution sources={sourceDistribution} />
            </div>
          </>
        )}

        {/* ── Tab: 系统监控 ───────────────── */}
        {activeTab === 'monitor' && (
          <>
            {/* 检索概览 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatsCard title="总检索次数" value={s.total_searches || 0} icon={Search} color="text-blue-600" subtitle={`近 ${monitor?.period?.days || 7} 天`} />
              <StatsCard title="错误次数" value={s.total_errors || 0} icon={AlertTriangle} color="text-red-600" subtitle={`错误率 ${errorRate}%`} />
              <StatsCard title="零结果率" value={`${zeroRate}%`} icon={Target} color="text-amber-600" subtitle="无匹配结果的检索比例" />
              <StatsCard title="平均延迟" value={s.avg_latency_ms != null ? `${s.avg_latency_ms}` : '—'} icon={Clock} color="text-indigo-600" subtitle="毫秒" />
            </div>

            {/* 延迟百分位 */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                延迟分布
              </h3>
              <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
                <LatencyCard label="平均延迟" value={s.avg_latency_ms ?? '—'} unit="ms" color="text-gray-700" />
                <LatencyCard label="P50（中位数）" value={s.p50_latency_ms ?? '—'} unit="ms" color="text-green-600" />
                <LatencyCard label="P95" value={s.p95_latency_ms ?? '—'} unit="ms" color="text-amber-600" />
                <LatencyCard label="P99" value={s.p99_latency_ms ?? '—'} unit="ms" color="text-orange-600" />
                <LatencyCard label="Top1 平均分" value={s.avg_top_score ?? '—'} unit="" color="text-blue-600" />
              </div>
            </div>

            {/* 图表区域：路由分布 + 压缩效果 + 错误统计 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <RouteDistribution routing={monitor?.routing} />
              <CompressionStats compression={monitor?.compression} />
              <ErrorStats errors={monitor?.errors} />
            </div>
          </>
        )}

        {/* 底部信息 */}
        <div className="mt-8 text-center text-sm text-gray-400">
          数据更新时间: {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
}
