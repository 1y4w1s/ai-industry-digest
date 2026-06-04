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

  // Load sources + tags once
  useEffect(() => {
    api.getSources().then((d) => setSources(d.sources || [])).catch(() => {});
    api.getTags().then((d) => setTags(d.tags || [])).catch(() => {});
  }, []);

  // Load reports list
  useEffect(() => {
    setLoading(true);
    const fetchReports = async () => {
      try {
        const data = await api.getReports(page);
        setReports(data.items || []);
        setTotal(data.total || 0);
        if (!selectedDate && data.items?.length > 0) {
          setSelectedDate(data.items[0].report_date);
        }
        // Cache successful response
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          reports: data.items || [],
          timestamp: Date.now(),
        }));
      } catch {
        // On failure, try cache
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          try {
            const { reports: cachedReports } = JSON.parse(cached);
            if (cachedReports.length > 0) {
              setReports(cachedReports);
              if (!selectedDate) setSelectedDate(cachedReports[0].report_date);
            }
          } catch {}
        }
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, [page]);

  // Load report detail when selectedDate changes
  useEffect(() => {
    if (!selectedDate) return;
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
  };
}
