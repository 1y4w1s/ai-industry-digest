import { useState, useEffect } from 'react';
import { api } from '../api/client';

const CACHE_KEY = 'signal_home_cache';

export function useReport() {
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);
  const [fromCache, setFromCache] = useState(false);
  const [cacheAge, setCacheAge] = useState(null);

  // Single aggregated fetch: reports + sources + tags + latest report in 1 request
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
        setTotal(data.reports?.total || 0);
        setSources(srcList);
        setTags(tagList);

        if (!selectedDate && reportsList.length > 0) {
          setSelectedDate(reportsList[0].report_date);
        }

        setReport(data.report_detail);

        // Cache successful response
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          reports: reportsList,
          timestamp: Date.now(),
        }));
        // Cache sources & tags separately (shared by other pages)
        localStorage.setItem('signal_sources', JSON.stringify(srcList));
        localStorage.setItem('signal_tags', JSON.stringify(tagList));
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
  };
}
