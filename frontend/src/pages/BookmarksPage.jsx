import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';

export default function BookmarksPage() {
  const { isLoggedIn, login } = useAuth();
  const [bookmarks, setBookmarks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();
  const goToArticle = (id) => navigate(`/?article=${encodeURIComponent(id)}`);

  const fetchBookmarks = (pg) => {
    setLoading(true);
    const cached = localStorage.getItem('signal_bookmarks');
    if (cached && pg === 1) {
      try { setBookmarks(JSON.parse(cached)); } catch {}
    }
    api.getBookmarks(pg)
      .then((data) => {
        setBookmarks(data);
        if (pg === 1) localStorage.setItem('signal_bookmarks', JSON.stringify(data));
      })
      .catch(() => { if (!cached || pg > 1) setBookmarks({ items: [], total: 0, pages: 0 }); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchBookmarks(page); }, [page]);

  const handleRemove = async (e, bookmarkId) => {
    e.stopPropagation();
    try {
      await api.removeBookmark(bookmarkId);
      fetchBookmarks(page);
    } catch {}
  };

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px', maxWidth: '800px' }}>
          <div className="mb-5">
            <button onClick={() => navigate('/')} style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>
              ← 返回首页
            </button>
          </div>

          {!isLoggedIn ? (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: 'var(--color-bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '8px' }}>当前页面需要登录才能浏览</p>
              <button onClick={() => { login(); }}
                style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer' }}>
                登录 / 注册
              </button>
            </div>
          ) : (<>

          <div className="mb-6" style={{ borderBottom: '1px solid var(--color-border-light)', paddingBottom: '16px' }}>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: 'var(--fs-xl)', fontWeight: 700, color: 'var(--color-text-title)' }}>
              收藏的文章
            </h1>
            {bookmarks && (
              <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                共 {bookmarks.total} 篇收藏
              </div>
            )}
          </div>

          {loading ? (
            <div className="text-center py-16">
              <div className="flex gap-1.5 justify-center mb-3">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
              </div>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>加载中...</span>
            </div>
          ) : bookmarks?.items?.length > 0 ? (
            <div className="space-y-1">
              {bookmarks.items.map((b) => (
                <div key={b.id || b.article_id} className="flex items-start gap-2 group">
                  <div className="flex-1 min-w-0">
                    <ArticleCard article={{ ...b.articles, _imp: b.articles?.importance || '' }} onSelect={goToArticle} variant="detailed" />
                  </div>
                  <button onClick={(e) => handleRemove(e, b.id)}
                    style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-label)', background: 'none', border: 'none', cursor: 'pointer', padding: '8px 4px', flexShrink: 0 }}>
                    取消收藏
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: 'var(--color-bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '4px' }}>还没有收藏</p>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>在阅读文章时可以收藏喜欢的内容</p>
            </div>
          )}
          </>)}

          {bookmarks?.pages > 1 && (
            <Pagination page={page} totalPages={bookmarks.pages} onPageChange={(pg) => setPage(pg)} />
          )}
        </div>
      </div>
    </div>
  );
}
