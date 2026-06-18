import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Cache, CACHE_TTL } from '../utils/cache';

const CACHE_KEY = 'signal_home_cache';

export function useReport(initialDate = null) {
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(initialDate);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);
  const [fromCache, setFromCache] = useState(false);
  const [cacheAge, setCacheAge] = useState(null);
  const [loadingMore, setLoadingMore] = useState(false);

  // Single aggregated fetch: reports + sources + tags + first report detail in 1 request
  useEffect(() => {
    setLoading(true);
    setFromCache(false);
    setCacheAge(null);

    const fetchHome = async () => {
      try {
        const data = await api.getHome();

        const reportsList = data.reports?.items || [];
        const srcList = data.sources || [];
        const tagList = data.tags || [];

        setReports(reportsList);
        setTotal(data.reports?.total || reportsList.length);
        setSources(srcList);
        setTags(tagList);

        // 只有在没有初始日期时才自动选择最新日期
        if (!selectedDate && reportsList.length > 0) {
          setSelectedDate(reportsList[0].report_date);
        }

        // 使用服务端预取的首日报详情，避免瀑布请求
        if (data.report_detail) {
          setReport(data.report_detail);
        }

        // Cache successful response
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          reports: reportsList,
          timestamp: Date.now(),
        }));
        // Cache sources & tags via Cache utility
        Cache.set('sources', srcList, CACHE_TTL.SOURCES);
        Cache.set('tags', tagList, CACHE_TTL.TAGS);
      } catch {
        // On failure, try cache
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          try {
            const { reports: cachedReports, timestamp } = JSON.parse(cached);
            if (cachedReports.length > 0) {
              setReports(cachedReports);
              if (!selectedDate) setSelectedDate(cachedReports[0].report_date);
              setFromCache(true);
              setCacheAge(Math.floor((Date.now() - (timestamp || 0)) / 60000));
            }
          } catch {}
        }
      } finally {
        setLoading(false);
      }
    };

    fetchHome();
  }, []); // Only run once on mount — page switching is local now

  // 加载更多日报数据
  const loadMore = async () => {
    if (loadingMore || reports.length >= total) return;
    
    setLoadingMore(true);
    const nextPage = Math.floor(reports.length / 14) + 1; // 每页14条
    
    try {
      const data = await api.getReports(nextPage, 14);
      if (data.items && data.items.length > 0) {
        setReports(prev => [...prev, ...data.items]);
        setTotal(data.total || total);
      }
    } catch (error) {
      console.error('Failed to load more reports:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  // 检查是否有更多数据可加载
  const hasMore = reports.length < total;

  // 强制刷新日报列表（用于查看更早的历史数据）
  const refreshReports = async () => {
    setLoading(true);
    try {
      const data = await api.getReports(1, 31); // 获取更多数据
      setReports(data.items || []);
      setTotal(data.total || 0);
      setPage(1);
    } catch (error) {
      console.error('Failed to refresh reports:', error);
    } finally {
      setLoading(false);
    }
  };

  // When selectedDate changes, fetch that day's report detail
  useEffect(() => {
    if (!selectedDate) return;
    // If report already matches selectedDate from the initial load, skip
    if (report?.report_date === selectedDate) return;

    setDetailLoading(true);
    api.getReport(selectedDate).then((data) => setReport(data)).catch(() => {}).finally(() => setDetailLoading(false));
  }, [selectedDate]);

  // Flatten articles from report
  const articles = [];
  if (report) {
    for (const level of ['high', 'medium', 'low'])
      for (const a of (report.articles?.[level] || [])) articles.push({ ...a, _imp: level });
  }

  const highArticles = articles.filter((a) => a._imp === 'high');

  return {
    reports, selectedDate, setSelectedDate,
    report, loading, detailLoading,
    page, setPage, total,
    sources, tags,
    articles, highArticles,
    fromCache, cacheAge,
    loadMore, loadingMore, hasMore,
    refreshReports,
  };
}
