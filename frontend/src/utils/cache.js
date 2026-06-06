/**
 * 统一缓存层 — localStorage + TTL
 * 用法:
 *   Cache.set('key', data, 30)   // 缓存 30 分钟
 *   const data = Cache.get('key') // 返回 null 表示过期/不存在
 */

const STORE_KEY = 'signal_cache_v1';

function readStore() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
}

function writeStore(store) {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(store)); } catch {}
}

export const Cache = {
  set(key, data, ttlMinutes = 60) {
    const store = readStore();
    store[key] = {
      data,
      expires: Date.now() + ttlMinutes * 60 * 1000,
    };
    writeStore(store);
  },

  get(key) {
    const store = readStore();
    const item = store[key];
    if (!item) return null;
    if (Date.now() > item.expires) {
      delete store[key];
      writeStore(store);
      return null;
    }
    return item.data;
  },

  remove(key) {
    const store = readStore();
    delete store[key];
    writeStore(store);
  },

  clear() {
    localStorage.removeItem(STORE_KEY);
  },

  /** 获取所有缓存项的 TTL 状态（用于调试） */
  debug() {
    const store = readStore();
    const now = Date.now();
    return Object.entries(store).map(([k, v]) => ({
      key: k,
      remainingMin: Math.round((v.expires - now) / 60000),
      expired: now > v.expires,
    }));
  },
};

/* 预定义缓存策略 */
export const CACHE_TTL = {
  SOURCES: 24 * 60,      // 24 小时（来源几乎不变）
  TAGS: 24 * 60,          // 24 小时（标签几乎不变）
  REPORTS: 5,             // 5 分钟（每日更新）
  REPORT_DETAIL: 2,       // 2 分钟（当天可能有变化）
  BOOKMARKS: 2,           // 2 分钟
  HISTORY: 1,             // 1 分钟
  STATS: 5,               // 5 分钟
  USER_STATS: 5,          // 5 分钟
};
