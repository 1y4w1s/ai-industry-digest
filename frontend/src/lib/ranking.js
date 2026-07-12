/**
 * 零登录推荐排序（确定性，无 LLM，可复现）
 *
 * 评分公式（每条文章 0~6 分）：
 *   score = mainThreadBoost × 3 + hasSoWhat × 2 + recencyScore
 *
 * - mainThreadBoost: 文章 URL/ID 命中今日 main-thread.stories[].article_ids
 *   → +1，否则 0；命中权重 × 3 → 主线文章最多得 3 分
 * - hasSoWhat: 文章的 reason/so_what 字段非空 → +1；权重 × 2 → 最多得 2 分
 * - recencyScore: 基于 published_at 与"当前列表最新时间"差
 *   → 0~1 线性，权重 × 1 → 最多得 1 分
 *
 * 同分时回退到原顺序（稳定排序）。
 *
 * @param {Array} articles - 原始文章列表
 * @param {Object|null} mainThread - /api/main-thread 返回的 {stories: [...]}
 * @returns {Array} 排序后的新数组（不修改原数组）
 */
export function rankArticles(articles, mainThread) {
  if (!Array.isArray(articles) || articles.length === 0) return articles || [];

  // 1. 构建主线文章 ID 集合
  const mainThreadIds = new Set();
  if (mainThread && Array.isArray(mainThread.stories)) {
    for (const story of mainThread.stories) {
      const ids = story.article_ids || [];
      for (const id of ids) {
        if (id) mainThreadIds.add(id);
      }
    }
  }

  // 2. 计算 recency 参考点（最新文章的 published_at）
  let newestTs = 0;
  for (const a of articles) {
    const ts = a.published_at ? new Date(a.published_at).getTime() : 0;
    if (ts > newestTs) newestTs = ts;
  }
  // 7 天外视为 0 分
  const SEVEN_DAYS = 7 * 24 * 60 * 60 * 1000;
  const oldestTs = newestTs - SEVEN_DAYS;

  // 3. 打分（带原索引做稳定排序）
  const scored = articles.map((article, idx) => {
    const articleId = article.url || article.id || '';
    const inMainThread = mainThreadIds.has(articleId) ? 1 : 0;
    const hasSoWhat = article.reason || article.so_what ? 1 : 0;
    const ts = article.published_at ? new Date(article.published_at).getTime() : 0;
    let recency = 0;
    if (newestTs > 0 && ts > 0 && newestTs > oldestTs) {
      recency = Math.max(0, Math.min(1, (ts - oldestTs) / (newestTs - oldestTs)));
    }

    const score = inMainThread * 3 + hasSoWhat * 2 + recency * 1;
    return { article, idx, score };
  });

  // 4. 排序：score desc, then idx asc（稳定）
  scored.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.idx - b.idx;
  });

  return scored.map((s) => s.article);
}
