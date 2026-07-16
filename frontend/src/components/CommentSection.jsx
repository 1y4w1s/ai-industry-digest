import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client';
import { useToast } from './Toast';
import { isLoggedIn, getToken } from '../lib/token';
import DOMPurify from 'dompurify';

/* ── SVG icons ───────────── */
const IconSend = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);
const IconFlag = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" /><line x1="4" y1="22" x2="4" y2="15" />
  </svg>
);
const IconReply = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 17 4 12 9 7" /><path d="M20 18v-2a4 4 0 0 0-4-4H4" />
  </svg>
);

function fmtTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return '刚刚';
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
    if (diff < 604800) return `${Math.floor(diff / 86400)} 天前`;
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return ''; }
}

export default function CommentSection({ articleId }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [authorName, setAuthorName] = useState('');
  const [replyTo, setReplyTo] = useState(null); // { id, author_name }
  const [submitting, setSubmitting] = useState(false);
  const [reportedIds, setReportedIds] = useState(new Set());
  const toast = useToast();

  // 点击"回复"时聚焦回复输入框
  const replyInputRef = useRef(null);

  const fetchComments = useCallback(async () => {
    if (!articleId) return;
    setLoading(true);
    try {
      const res = await api.getComments(articleId);
      setComments(res.comments || []);
    } catch {
      // 静默降级
      setComments([]);
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const loggedIn = isLoggedIn();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = newComment.trim();
    if (!text) return;

    setSubmitting(true);
    try {
      const body = {
        article_id: articleId,
        content: text,
        author_name: authorName.trim() || '',
        parent_id: replyTo ? replyTo.id : null,
      };
      await api.createComment(body);
      setNewComment('');
      setReplyTo(null);
      toast('评论已发表', 'success');
      fetchComments();
    } catch (err) {
      toast(err.message || '评论发表失败', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReport = async (commentId) => {
    if (reportedIds.has(commentId)) {
      toast('你已举报过该评论', 'info');
      return;
    }
    if (!window.confirm('举报该评论为不当内容？')) return;
    try {
      const token = getToken() || 'anonymous';
      await api.reportComment(commentId, '用户举报', token);
      setReportedIds((prev) => new Set(prev).add(commentId));
      toast('举报已提交，编辑部将尽快处理', 'success');
    } catch (err) {
      toast(err.message || '举报提交失败', 'error');
    }
  };

  const renderComment = (c, isReply = false) => {
    const timeStr = fmtTime(c.created_at);
    const reported = reportedIds.has(c.id);

    return (
      <div key={c.id} className={`${isReply ? 'ml-8 mt-2' : 'mb-4'}`}
        style={{
          padding: isReply ? '10px 12px' : '12px 14px',
          background: isReply ? 'var(--color-bg-off)' : 'var(--color-bg-white)',
          border: '1px solid var(--color-border-light)',
          borderRadius: '8px',
        }}>
        <div className="flex items-center gap-2 mb-1">
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-title)' }}>
            {DOMPurify.sanitize(c.author_name || '匿名读者')}
          </span>
          {c.user_id && (
            <span style={{
              fontSize: '10px', padding: '1px 5px', borderRadius: '3px',
              background: '#eef2ff', color: '#4338ca',
            }}>登录用户</span>
          )}
        </div>
        <p style={{ fontSize: '13px', lineHeight: 1.6, color: 'var(--color-text-body)', margin: '4px 0 6px', wordBreak: 'break-word' }}>
          {DOMPurify.sanitize(c.content)}
        </p>
        <div className="flex items-center gap-3" style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          <span>{timeStr}</span>
          {!isReply && (
            <button onClick={() => setReplyTo(replyTo?.id === c.id ? null : { id: c.id, author_name: c.author_name || '匿名读者' })}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-blue-link)', padding: 0, fontSize: '11px' }}>
              <IconReply /> 回复
            </button>
          )}
          <button onClick={() => handleReport(c.id)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', background: 'none', border: 'none', cursor: 'pointer', color: reported ? '#b91c1c' : 'var(--color-text-label)', padding: 0, fontSize: '11px' }}>
            <IconFlag /> {reported ? '已举报' : '举报'}
          </button>
        </div>

        {/* 回复列表 */}
        {c.replies && c.replies.length > 0 && (
          <div className="mt-2 space-y-2">
            {c.replies.map((r) => renderComment(r, true))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="mt-8 pt-6 no-print" style={{ borderTop: '1px solid var(--color-border-light)' }}>
      <h3 className="font-semibold text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-muted)' }}>
        评论{loading ? '' : ` (${comments.length})`}
      </h3>
      <p className="text-xs mb-4" style={{ color: 'var(--color-text-label)' }}>
        发表评论即表示你同意遵守社区规范。编辑部保留审核权利。
      </p>

      {/* 评论区列表 */}
      <div className="mb-5 max-h-[500px] overflow-y-auto">
        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} style={{
                padding: '12px 14px', border: '1px solid var(--color-border-light)',
                borderRadius: '8px', background: 'var(--color-bg-white)',
              }}>
                <div style={{ height: '12px', width: '30%', background: 'var(--color-border-light)', borderRadius: '4px', marginBottom: '8px' }} />
                <div style={{ height: '12px', width: '70%', background: 'var(--color-border-light)', borderRadius: '4px', marginBottom: '4px' }} />
                <div style={{ height: '10px', width: '20%', background: 'var(--color-border-light)', borderRadius: '4px' }} />
              </div>
            ))}
          </div>
        ) : comments.length === 0 ? (
          <p className="text-xs py-6 text-center" style={{ color: 'var(--color-text-label)' }}>暂无评论，来写第一条吧</p>
        ) : (
          <div className="space-y-2">
            {comments.map((c) => renderComment(c))}
          </div>
        )}
      </div>

      {/* 发表评论表单 */}
      <form onSubmit={handleSubmit} className="space-y-2">
        {/* 匿名展示名 */}
        {!loggedIn && (
          <input
            type="text"
            value={authorName}
            onChange={(e) => setAuthorName(e.target.value)}
            placeholder={'你的昵称（选填，默认\u201c匿名读者\u201d）'}
            maxLength={50}
            style={{
              width: '100%', padding: '8px 10px', fontSize: '12px',
              background: 'var(--color-bg-white)', border: '1px solid var(--color-border)',
              borderRadius: '6px', color: 'var(--color-text-body)',
              boxSizing: 'border-box',
            }}
          />
        )}

        {/* 回复提示 */}
        {replyTo && (
          <div className="flex items-center gap-2" style={{ fontSize: '12px', color: 'var(--color-text-label)' }}>
            <span>回复 <strong>{DOMPurify.sanitize(replyTo.author_name)}</strong></span>
            <button type="button" onClick={() => setReplyTo(null)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b91c1c', padding: 0, fontSize: '11px' }}>
              取消
            </button>
          </div>
        )}

        <div className="flex gap-2">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={replyTo ? `回复 ${replyTo.author_name}...` : '分享你的看法...（最多 2000 字）'}
            maxLength={2000}
            rows={2}
            style={{
              flex: 1, padding: '8px 10px', fontSize: '12px', resize: 'none',
              background: 'var(--color-bg-white)', border: '1px solid var(--color-border)',
              borderRadius: '6px', color: 'var(--color-text-body)',
              fontFamily: 'inherit', lineHeight: 1.5,
            }}
          />
          <button type="submit" disabled={submitting || !newComment.trim()}
            className="self-end disabled:opacity-40"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              padding: '8px 14px', fontSize: '12px', borderRadius: '6px',
              background: 'var(--color-text-title)', color: 'var(--color-bg-white)',
              border: 'none', cursor: 'pointer',
            }}>
            <IconSend />
            {submitting ? '...' : '发送'}
          </button>
        </div>
      </form>
    </div>
  );
}
