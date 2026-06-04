import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';

export default function BookmarksPage({ onReadArticle }) {
  const { isLoggedIn, login } = useAuth();
  const [bookmarks, setBookmarks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const fetchBookmarks = (pg) => {
    setLoading(true);
    api.getBookmarks(pg)
      .then((data) => setBookmarks(data))
      .catch(() => setBookmarks({ items: [], total: 0, pages: 0 }))
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
    <div className="h-full flex flex-col" style={{ background: '#FBFCFD' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px', maxWidth: '800px' }}>
          {/* Back link */}
          <div className="mb-5">
            <button onClick={() => navigate('/')} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>
              ← 返回首页
            </button>
          </div>

          {/* Login guard */}
          {!isLoggedIn ? (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: '#F0F1F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8C9096" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: '#1A1C1E', marginBottom: '8px' }}>当前页面需要登录才能浏览</p>
              <button onClick={() => { login(); }}
                style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}>
                登录 / 注册
              </button>
            </div>
          ) : (<>

          {/* Header */}
          <div className="mb-6" style={{ borderBottom: '1px solid #E8EAED', paddingBottom: '16px' }}>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '20px', fontWeight: 700, color: '#1A1C1E' }}>
              收藏的文章
            </h1>
            {bookmarks && (
              <div style={{ fontSize: '12px', color: '#686C72', marginTop: '4px' }}>
                共 {bookmarks.total} 篇收藏
              </div>
            )}
          </div>

          {/* List */}
          {loading ? (
            <div className="text-center py-16">
              <div className="flex gap-1.5 justify-center mb-3">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
              </div>
              <span style={{ fontSize: '13px', color: '#686C72' }}>加载中...</span>
            </div>
          ) : bookmarks?.items?.length > 0 ? (
            <div className="space-y-1">
              {bookmarks.items.map((b) => (
                <div key={b.id || b.article_id} className="flex items-start gap-2 group">
                  <div className="flex-1 min-w-0">
                    <ArticleCard
                      article={{ ...b.article, _imp: b.article?.importance || '' }}
                      onSelect={onReadArticle}
                      variant="detailed"
                    />
                  </div>
                  <button
                    onClick={(e) => handleRemove(e, b.id)}
                    style={{ fontSize: '11px', color: '#8C9096', background: 'none', border: 'none', cursor: 'pointer', padding: '8px 4px', opacity: 0, transition: 'opacity 0.15s' }}
                    className="group-hover:opacity-100 flex-shrink-0"
                  >
                    取消收藏
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: '#F0F1F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8C9096" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: '#1A1C1E', marginBottom: '4px' }}>还没有收藏</p>
              <p style={{ fontSize: '12px', color: '#686C72' }}>在阅读文章时可以收藏喜欢的内容</p>
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
