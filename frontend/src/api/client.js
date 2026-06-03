const API_BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
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

  // 收藏
  getBookmarks: (page = 1) => request(`/bookmarks?page=${page}&page_size=20`),
  addBookmark: (articleId, note = '') =>
    request('/bookmarks', { method: 'POST', body: JSON.stringify({ article_id: articleId, note }) }),
  removeBookmark: (id) =>
    request(`/bookmarks/${id}`, { method: 'DELETE' }),

  // 历史
  getHistory: (page = 1) => request(`/history?page=${page}&page_size=20`),
  addHistory: (articleId) =>
    request('/history', { method: 'POST', body: JSON.stringify({ article_id: articleId }) }),

  // 反馈
  submitFeedback: (articleId, feedback) =>
    request('/feedback', { method: 'POST', body: JSON.stringify({ article_id: articleId, feedback }) }),

  // AI 对话
  chat: (message, articleId = null, sessionId = null) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, article_id: articleId, session_id: sessionId }),
    }),

  // 文章代理（绕过 CORS）
  getProxyUrl: (url) => `${API_BASE}/proxy?url=${encodeURIComponent(url)}`,
};
