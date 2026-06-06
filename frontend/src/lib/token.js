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

/** 检查是否已登录 */
export function isLoggedIn() {
  return !!getToken();
}
