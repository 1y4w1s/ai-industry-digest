import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../api/client';
import KnowledgeGraphDrawer from '../components/KnowledgeGraphDrawer';

const PAGE_SIZE = 20;

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [graphDoc, setGraphDoc] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // 筛选
  const [statusFilter, setStatusFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: PAGE_SIZE };
      if (statusFilter) params.status = statusFilter;
      if (tagFilter) params.tag = tagFilter;
      const data = await api.kb.list(params);
      setDocuments(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('获取文档列表失败:', err);
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, tagFilter]);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  // 上传文档
  const handleUpload = async (files) => {
    if (!files?.length) return;
    setUploading(true);
    try {
      for (const file of files) {
        await api.kb.upload(file);
      }
      await fetchDocuments();
    } catch (err) {
      console.error('上传失败:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    handleUpload(e.target.files);
    e.target.value = '';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  // 处理文档
  const handleProcess = async (id) => {
    setProcessingId(id);
    try {
      await api.kb.process(id);
      await fetchDocuments();
    } catch (err) {
      console.error('处理失败:', err);
    } finally {
      setProcessingId(null);
    }
  };

  // 删除文档
  const handleDelete = async (id, name) => {
    if (!confirm(`确定删除「${name}」？此操作不可恢复。`)) return;
    try {
      await api.kb.delete(id);
      await fetchDocuments();
      if (graphDoc?.id === id) {
        setGraphDoc(null);
        setGraphData(null);
      }
    } catch (err) {
      console.error('删除失败:', err);
    }
  };

  // 查看知识图谱
  const openGraph = async (doc) => {
    setGraphDoc(doc);
    setGraphData(null);
    setGraphLoading(true);
    try {
      const data = await api.kb.getGraph(doc.id);
      setGraphData(data);
    } catch (err) {
      console.error('获取知识图谱失败:', err);
    } finally {
      setGraphLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="flex-1 flex flex-col min-h-0 animate-fade-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'var(--color-border-light)' }}>
        <div>
          <h1 className="text-lg font-semibold" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: 'var(--color-text-title)' }}>
            知识库
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            管理上传的文档，构建知识图谱 · 共 {total} 个文档
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          style={{
            padding: '8px 20px',
            fontSize: 'var(--fs-sm)',
            background: 'var(--color-text-title)',
            color: 'var(--color-bg-white)',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 500,
            opacity: uploading ? 0.6 : 1,
            transition: 'opacity 0.15s',
          }}
          onMouseEnter={(e) => { if (!uploading) e.target.style.opacity = 0.8; }}
          onMouseLeave={(e) => { if (!uploading) e.target.style.opacity = 1; }}
        >
          {uploading ? '上传中...' : '+ 上传文档'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.pdf,.docx"
          multiple
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />
      </div>

      {/* 上传拖放区域 */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        style={{
          margin: '16px 24px',
          padding: '32px',
          borderRadius: '4px',
          border: `2px dashed ${dragOver ? 'var(--color-border-bold)' : 'var(--color-border)'}`,
          background: dragOver ? 'var(--color-bg-off)' : 'transparent',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        <svg className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--color-text-label)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>
          {dragOver ? '释放以上传文件' : '拖拽文件到此处，或点击选择文件'}
        </p>
        <p style={{ fontSize: '11px', color: 'var(--color-text-label)', marginTop: '4px' }}>
          支持 TXT、Markdown、PDF、DOCX 格式
        </p>
      </div>

      {/* 筛选栏 */}
      <div className="flex items-center gap-3 px-6 mb-3">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          style={{
            padding: '6px 12px',
            fontSize: 'var(--fs-sm)',
            background: 'var(--color-bg-off)',
            border: '1px solid var(--color-border)',
            borderRadius: '4px',
            color: 'var(--color-text-body)',
            outline: 'none',
          }}
        >
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="processing">处理中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        <input
          type="text"
          placeholder="按标签筛选..."
          value={tagFilter}
          onChange={(e) => { setTagFilter(e.target.value); setPage(1); }}
          style={{
            padding: '6px 12px',
            fontSize: 'var(--fs-sm)',
            background: 'var(--color-bg-off)',
            border: '1px solid var(--color-border)',
            borderRadius: '4px',
            color: 'var(--color-text-body)',
            outline: 'none',
            width: '200px',
          }}
        />
        {(statusFilter || tagFilter) && (
          <button
            onClick={() => { setStatusFilter(''); setTagFilter(''); setPage(1); }}
            style={{
              fontSize: '11px',
              color: 'var(--color-text-muted)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            清除筛选
          </button>
        )}
      </div>

      {/* 文档列表 */}
      <div className="flex-1 overflow-auto px-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="flex gap-1.5">
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
            </div>
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <svg className="w-12 h-12 mb-3" style={{ color: 'var(--color-border)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>还没有文档，上传一个开始吧</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-light)', color: 'var(--color-text-label)' }}>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500, width: '40%' }}>文件名</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500, width: '10%' }}>类型</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500, width: '8%' }}>大小</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500, width: '8%' }}>状态</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500, width: '14%' }}>标签</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500, width: '14%' }}>上传时间</th>
                <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 500, width: '16%' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr
                  key={doc.id}
                  style={{
                    borderBottom: '1px solid var(--color-border-light)',
                    transition: 'background 0.12s',
                  }}
                  className="hover:bg-[var(--color-bg-off)]"
                >
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ color: 'var(--color-text-title)', fontWeight: 500 }}>{doc.name}</span>
                  </td>
                  <td style={{ padding: '10px 12px', color: 'var(--color-text-muted)' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '3px',
                      fontSize: '10px',
                      background: 'var(--color-bg-hover)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.3px',
                    }}>
                      {doc.file_type}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', color: 'var(--color-text-muted)' }}>{formatFileSize(doc.file_size)}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <StatusBadge status={doc.status} />
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div className="flex flex-wrap gap-1">
                      {(doc.tags || []).map((t) => (
                        <span key={t} style={{
                          padding: '1px 6px',
                          fontSize: '10px',
                          borderRadius: '3px',
                          background: 'var(--color-border-light)',
                          color: 'var(--color-text-muted)',
                        }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px', color: 'var(--color-text-muted)', fontSize: '11px' }}>
                    {new Date(doc.created_at).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                    <div className="flex items-center justify-end gap-2">
                      {doc.status === 'pending' && (
                        <ActionBtn onClick={() => handleProcess(doc.id)} disabled={processingId === doc.id}>
                          {processingId === doc.id ? '...' : '处理'}
                        </ActionBtn>
                      )}
                      <ActionBtn onClick={() => openGraph(doc)} disabled={doc.status !== 'completed' || doc.status === 'failed'} title={doc.status !== 'completed' ? '文档未完成处理' : ''}>
                        图谱
                      </ActionBtn>
                      <ActionBtn onClick={() => handleDelete(doc.id, doc.name)} className="text-[var(--color-high)] hover:bg-[var(--color-bg-hover)]">
                        删除
                      </ActionBtn>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-6 py-3 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-label)' }}>
            第 {page}/{totalPages} 页，共 {total} 个文档
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              style={{
                padding: '6px 14px',
                fontSize: 'var(--fs-sm)',
                background: 'var(--color-bg-off)',
                border: '1px solid var(--color-border)',
                borderRadius: '4px',
                cursor: page <= 1 ? 'not-allowed' : 'pointer',
                opacity: page <= 1 ? 0.4 : 1,
                color: 'var(--color-text-body)',
              }}
            >
              上一页
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              style={{
                padding: '6px 14px',
                fontSize: 'var(--fs-sm)',
                background: 'var(--color-bg-off)',
                border: '1px solid var(--color-border)',
                borderRadius: '4px',
                cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                opacity: page >= totalPages ? 0.4 : 1,
                color: 'var(--color-text-body)',
              }}
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {/* 知识图谱抽屉 */}
      <KnowledgeGraphDrawer
        open={!!graphDoc}
        onClose={() => { setGraphDoc(null); setGraphData(null); }}
        doc={graphDoc}
        data={graphData}
        loading={graphLoading}
      />
    </div>
  );
}

// --- 子组件 ---

function StatusBadge({ status }) {
  const config = {
    pending: { label: '待处理', bg: '#FFF3E0', color: '#E65100' },
    processing: { label: '处理中', bg: '#E3F2FD', color: '#1565C0' },
    completed: { label: '已完成', bg: '#E8F5E9', color: '#2E7D32' },
    failed: { label: '失败', bg: '#FFEBEE', color: '#C62828' },
  };
  const s = config[status] || { label: status, bg: 'var(--color-bg-off)', color: 'var(--color-text-muted)' };
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: '3px',
      fontSize: '10px',
      background: s.bg,
      color: s.color,
      fontWeight: 500,
    }}>
      {s.label}
    </span>
  );
}

function ActionBtn({ onClick, disabled, children, title, className }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      style={{
        padding: '4px 10px',
        fontSize: '11px',
        background: 'transparent',
        border: '1px solid var(--color-border)',
        borderRadius: '4px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        color: 'var(--color-text-muted)',
        transition: 'all 0.12s',
      }}
      className={className || 'hover:bg-[var(--color-bg-hover)] hover:border-[var(--color-border-bold)]'}
    >
      {children}
    </button>
  );
}
