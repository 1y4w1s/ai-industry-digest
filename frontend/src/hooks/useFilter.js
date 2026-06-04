import { useState, useMemo, useCallback } from 'react';

export function useFilter(articles) {
  const [importance, setImportance] = useState('');
  const [source, setSource] = useState('');
  const [tag, setTag] = useState([]);

  const filteredArticles = useMemo(() => {
    return articles.filter((a) => {
      if (importance && a._imp !== importance) return false;
      if (source && a.source_name !== source) return false;
      if (tag.length > 0 && !(a.tags || []).some((t) => tag.includes(t))) return false;
      return true;
    });
  }, [articles, importance, source, tag]);

  const filteredGroups = useMemo(() => {
    const groups = {};
    for (const a of filteredArticles) {
      const src = a.source_name || '其他';
      if (!groups[src]) groups[src] = [];
      groups[src].push(a);
    }
    return groups;
  }, [filteredArticles]);

  const activeFilterCount = [importance, source].filter(Boolean).length + tag.length;

  const clearFilters = useCallback(() => {
    setImportance('');
    setSource('');
    setTag([]);
  }, []);

  const toggleTag = useCallback((keyword) => {
    setTag((prev) => {
      const idx = prev.indexOf(keyword);
      if (idx >= 0) return prev.filter((_, i) => i !== idx);
      return [...prev, keyword];
    });
  }, []);

  return {
    importance, setImportance,
    source, setSource,
    tag, setTag,
    filteredArticles,
    filteredGroups,
    activeFilterCount,
    clearFilters,
    toggleTag,
  };
}
