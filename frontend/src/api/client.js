const API_BASE = import.meta.env.VITE_API_URL || '/api';
const TOKEN_KEY = 'signal_auth_token';
// Demo 用户 token（用于未登录时的演示模式）
const DEMO_TOKEN = 'demo-user';

function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}

async function request(path, options = {}) {
  const token = getToken() || DEMO_TOKEN;
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { headers, ...options });
  if (res.status === 429) {
    throw new Error('请求过于频繁，请稍后再试');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `请求失败 (${res.status})`);
  }
  return res.json();
}

export const api = {
  // 日报
  getReports: (page = 1, size = 7) =>
    request(`/reports?page=${page}&page_size=${size}`),

  getReport: (date) => request(`/reports/${date}`),

  getReportDates: () => request('/reports/dates'),

  // 文章
  getArticles: (params = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.set('page', params.page);
    if (params.page_size) q.set('page_size', params.page_size);
    if (params.keyword) q.set('keyword', params.keyword);
    if (params.tag) q.set('tag', params.tag);
    if (params.source) q.set('source', params.source);
    if (params.importance) q.set('importance', params.importance);
    if (params.date_from) q.set('date_from', params.date_from);
    if (params.date_to) q.set('date_to', params.date_to);
    return request(`/articles?${q}`);
  },

  getArticle: (id) => request(`/articles/${id}`),

  // 统计
  getStats: () => request('/stats'),
  getSources: () => request('/sources'),
  getTags: () => request('/tags'),

  // 用户
  getMe: () => request('/auth/me'),
  getStats: () => request('/auth/stats'),
  getReadingTrends: () => request('/auth/reading-trends'),

  // 收藏
  getBookmarks: (page = 1) => request(`/auth/bookmarks?page=${page}&page_size=20`),
  addBookmark: (articleId, note = '') =>
    request('/auth/bookmarks', { method: 'POST', body: JSON.stringify({ article_id: articleId, note }) }),
  removeBookmark: (id) =>
    request(`/auth/bookmarks/${id}`, { method: 'DELETE' }),

  // 历史
  getHistory: (page = 1) => request(`/auth/history?page=${page}&page_size=20`),
  addHistory: (articleId) =>
    request('/auth/history', { method: 'POST', body: JSON.stringify({ article_id: articleId }) }),
  clearHistory: () =>
    request('/auth/history', { method: 'DELETE' }),

  // 反馈
  submitFeedback: (articleId, feedback) =>
    request('/auth/feedback', { method: 'POST', body: JSON.stringify({ article_id: articleId, feedback }) }),

  // AI 对话
  chat: (message, articleId = null, sessionId = null) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, article_id: articleId, session_id: sessionId }),
    }),

  // 首页聚合
  getHome: () => request('/home'),
};
