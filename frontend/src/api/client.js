const API_BASE = import.meta.env.VITE_API_URL || '/api';

import {
  getToken, DEMO_TOKEN, getAuthHeader,
  isLoggedIn, isTokenExpiringSoon, refreshAccessToken,
} from '../lib/token';
import { supabase } from '../lib/supabase';

// ── 全局刷新锁 + session 状态 ──
// _refreshPromise: 多个并发请求同时遇到 401 时，共用同一个刷新结果
// _sessionDead: 一次刷新+重试都失败后标记 session 已死，不再重复刷新
// _deadToken: 标记 session 死亡时的 token 值，token 变了就重置
let _refreshPromise = null;
let _sessionDead = false;
let _deadToken = null;

async function _doRefresh() {
  // 如果 session 已经被标记为死亡，检查 token 是否变了（用户可能重新登录了）
  if (_sessionDead) {
    const currentToken = getToken();
    if (currentToken && currentToken !== _deadToken) {
      console.log('[API] 检测到 token 已变更，重置 session 状态');
      _sessionDead = false;
      _deadToken = null;
    } else {
      console.log('[API] Session 已失效，跳过刷新');
      return null;
    }
  }

  // 如果已经有刷新在进行中，直接复用
  if (_refreshPromise) {
    console.log('[API] 刷新正在进行中，等待...');
    return _refreshPromise;
  }

  _refreshPromise = (async () => {
    try {
      const newToken = await refreshAccessToken(supabase);
      if (newToken) {
        console.log('[API] Token 刷新成功');
        return newToken;
      }
      console.warn('[API] Token 刷新失败');
      return null;
    } finally {
      // 刷新完成后释放锁
      _refreshPromise = null;
    }
  })();

  return _refreshPromise;
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const auth = getAuthHeader();
  if (auth) {
    headers['Authorization'] = auth;
  }

  // 预判：token 即将过期 → 提前刷新（用户无感知）
  if (isLoggedIn() && isTokenExpiringSoon()) {
    console.log('[API] Token 即将过期，提前刷新...');
    const newToken = await _doRefresh();
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`;
    }
  }

  let res = await fetch(`${API_BASE}${path}`, { headers, ...options });

  // 401 拦截：已登录用户 → 尝试刷新 token 后重试
  if (res.status === 401 && isLoggedIn()) {
    console.log('[API] 收到 401，尝试刷新 token...');
    const newToken = await _doRefresh();

    if (newToken) {
      // 刷新成功 → 重试原请求
      headers['Authorization'] = `Bearer ${newToken}`;
      res = await fetch(`${API_BASE}${path}`, { headers, ...options });
      console.log('[API] Token 刷新成功，请求重试完成');

      // 重试成功 → session 复活
      if (res.ok) {
        _sessionDead = false;
      }

      // 重试后仍然 401 → session 确实已失效
      // 标记 session_dead，后续请求不再尝试刷新
      if (res.status === 401) {
        console.warn('[API] 重试后仍然 401，session 已失效，后续请求跳过刷新');
        _sessionDead = true;
        _deadToken = getToken();
      }
    } else {
      // 刷新失败 → 不清除 token，不跳登录
      // token 留在 localStorage，用户仍可浏览公开内容
      // 调用方自行决定是否提示用户
      console.warn('[API] Token 刷新失败，保留当前 token，继续以未登录状态浏览');
    }
  }

  // 限流提示
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
  addHistoryWithDepth: (articleId, readPercent, durationSec) =>
    request('/auth/history', { method: 'POST', body: JSON.stringify({ article_id: articleId, read_percent: readPercent, duration_sec: durationSec }) }),
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

  // 个性化推荐
  getRecommend: (limit = 5) => request(`/recommend?limit=${limit}`),

  // 知识库
  kb: {
    list: (params = {}) => {
      const q = new URLSearchParams();
      if (params.page) q.set('page', params.page);
      if (params.page_size) q.set('page_size', params.page_size);
      if (params.tag) q.set('tag', params.tag);
      if (params.status) q.set('status', params.status);
      if (params.file_type) q.set('file_type', params.file_type);
      if (params.source) q.set('source', params.source);
      if (params.q) q.set('q', params.q);
      return request(`/kb/documents?${q}`);
    },

    get: (id) => request(`/kb/documents/${id}`),

    upload: async (file, tags = '', isPublic = true) => {
      const auth = getAuthHeader();
      const formData = new FormData();
      formData.append('file', file);
      if (tags) formData.append('tags', tags);
      formData.append('is_public', isPublic ? 'true' : 'false');
      const res = await fetch(`${API_BASE}/kb/documents`, {
        method: 'POST',
        headers: auth ? { 'Authorization': auth } : {},
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '上传失败');
      }
      return res.json();
    },

    delete: (id) => request(`/kb/documents/${id}`, { method: 'DELETE' }),

    process: (id) => request(`/kb/documents/${id}/process`, { method: 'POST' }),

    getChunks: (id) => request(`/kb/documents/${id}/chunks`),

    getGraph: (id) => request(`/kb/documents/${id}/graph`),

    preview: (id) => request(`/kb/documents/${id}/preview`),

    download: (id) => {
      const token = getToken() || DEMO_TOKEN;
      window.open(`${API_BASE}/kb/documents/${id}/download?token=${token}`, '_blank');
    },

    updateTags: (id, tags) =>
      request(`/kb/documents/${id}/tags`, {
        method: 'PUT',
        body: JSON.stringify({ tags }),
      }),

    batchDelete: (ids) =>
      request('/kb/batch/delete', {
        method: 'POST',
        body: JSON.stringify({ ids }),
      }),

    batchProcess: (ids) =>
      request('/kb/batch/process', {
        method: 'POST',
        body: JSON.stringify({ ids }),
      }),

    chat: (message, documentIds = null, sessionId = null) =>
      request('/kb/chat', {
        method: 'POST',
        body: JSON.stringify({ message, document_ids: documentIds, session_id: sessionId }),
      }),
  },

  // 全站搜索
  searchAll: (q, page = 1, page_size = 50) =>
    request(`/search?q=${encodeURIComponent(q)}&page=${page}&page_size=${page_size}`),
};

// Dev/test: 暴露到全局方便 DevTools 调试
if (typeof window !== 'undefined') window.__api = api;
