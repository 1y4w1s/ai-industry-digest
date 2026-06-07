/**
 * 统一 Token 管理
 * AuthContext + api/client.js 共用，单一来源
 */

const STORAGE_KEY = 'signal_auth_token';

/** 临时用户 token（未登录时的演示模式） */
export const DEMO_TOKEN = 'demo-user';

/** 获取当前 token */
export function getToken() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

/** 保存 token（登录成功时调用） */
export function setToken(token) {
  try {
    localStorage.setItem(STORAGE_KEY, token);
  } catch { /* ignore */ }
}

/** 清除 token（登出时调用） */
export function clearToken() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch { /* ignore */ }
}

/** 获取带 Bearer 前缀的 Authorization header 值 */
export function getAuthHeader() {
  const token = getToken() || DEMO_TOKEN;
  return token ? `Bearer ${token}` : null;
}

/** 检查是否已登录（localStorage 中有真实 token 而非 demo） */
export function isLoggedIn() {
  const token = getToken();
  return !!token && token !== DEMO_TOKEN;
}

/**
 * 检查 token 是否即将过期（提前 5 分钟算"即将"）
 * @returns {boolean} true = 需要刷新
 */
export function isTokenExpiringSoon() {
  const token = getToken();
  if (!token || token === DEMO_TOKEN) return false;

  try {
    const payloadBase64 = token.split('.')[1];
    const payload = JSON.parse(atob(payloadBase64));
    const exp = payload.exp * 1000;
    const fiveMinutes = 5 * 60 * 1000;
    return (exp - Date.now()) < fiveMinutes;
  } catch {
    return false;
  }
}

/**
 * 用 Supabase refreshSession 换取新的 access_token
 * 需要在调用方注入 supabase client，避免循环依赖
 * @param {object} supabase - Supabase client 实例
 * @returns {Promise<string|null>} 新 token 或 null
 */
export async function refreshAccessToken(supabase) {
  if (!supabase) return null;
  try {
    const { data, error } = await supabase.auth.refreshSession();
    if (error) throw error;
    if (data?.session?.access_token) {
      setToken(data.session.access_token);
      return data.session.access_token;
    }
  } catch (e) {
    console.warn('[Token] 刷新失败:', e.message);
  }
  return null;
}
