import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../api/client';
import KnowledgeGraphDrawer from '../components/KnowledgeGraphDrawer';
import KnowledgePreviewDrawer from '../components/KnowledgePreviewDrawer';
import KBChatBubble from '../components/KBChatBubble';

const PAGE_SIZE = 20;

// ── SVG Icons ──
const Icon = {
  search: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>,
  plus: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>,
  trash: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>,
  download: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>,
  refresh: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" /></svg>,
  query: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>,
  reset: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" /></svg>,
  graph: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" /></svg>,
  eye: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
  dots: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zm0 6a.75.75 0 110-1.5.75.75 0 010 1.5zm0 6a.75.75 0 110-1.5.75.75 0 010 1.5z" /></svg>,
  batch: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg>,
};

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZE);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadPublic, setUploadPublic] = useState(true);  // 上传时是否公开
  const [selected, setSelected] = useState(new Set());
  const fileInputRef = useRef(null);
  const uploadInputRef = useRef(null);
  const searchTimer = useRef(null);

  // 筛选状态
  const [searchQ, setSearchQ] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');

  // 抽屉状态
  const [graphDoc, setGraphDoc] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [previewContent, setPreviewContent] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // 批量下拉状态
  const [batchOpen, setBatchOpen] = useState(false);
  const [menuDoc, setMenuDoc] = useState(null);

  // 标签编辑
  const [editTagsDoc, setEditTagsDoc] = useState(null);
  const [editTagsInput, setEditTagsInput] = useState('');

  // 实际用于请求的参数
  const [queryParams, setQueryParams] = useState({
    q: '', file_type: '', status: '', source: '',
  });

  // 防抖搜索
  const handleSearchChange = (value) => {
    setSearchQ(value);
    clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      setPage(1);
      setQueryParams((prev) => ({ ...prev, q: value }));
    }, 300);
  };

  // 查询
  const handleQuery = () => {
    setPage(1);
    setQueryParams({
      q: searchQ,
      file_type: fileTypeFilter,
      status: statusFilter,
      source: sourceFilter,
    });
  };

  // 重置
  const handleReset = () => {
    setSearchQ('');
    setFileTypeFilter('');
    setStatusFilter('');
    setSourceFilter('');
    setPage(1);
    setQueryParams({ q: '', file_type: '', status: '', source: '' });
  };

  // 获取文档列表
  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (queryParams.q) params.q = queryParams.q;
      if (queryParams.file_type) params.file_type = queryParams.file_type;
      if (queryParams.status) params.status = queryParams.status;
      if (queryParams.source) params.source = queryParams.source;
      const data = await api.kb.list(params);
      setDocuments(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('获取文档列表失败:', err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, queryParams]);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  // 上传
  const handleUpload = async (files) => {
    if (!files?.length) return;
    setUploading(true);
    try {
      for (const file of files) {
        await api.kb.upload(file, '', uploadPublic);
      }
      await fetchDocuments();
    } catch (err) {
      console.error('上传失败:', err);
    } finally {
      setUploading(false);
    }
  };

  // 处理文档
  const handleProcess = async (id) => {
    try {
      await api.kb.process(id);
      await fetchDocuments();
    } catch (err) {
      console.error('处理失败:', err);
    }
  };

  // 删除文档
  const handleDelete = async (id, name) => {
    if (!confirm(`确定删除「${name}」？此操作不可恢复。`)) return;
    try {
      await api.kb.delete(id);
      await fetchDocuments();
      if (graphDoc?.id === id) setGraphDoc(null);
      if (previewDoc?.id === id) setPreviewDoc(null);
    } catch (err) {
      console.error('删除失败:', err);
    }
  };

  // 批量操作
  const handleBatchDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`确定删除选中的 ${selected.size} 个文档？`)) return;
    try {
      await api.kb.batchDelete([...selected]);
      setSelected(new Set());
      await fetchDocuments();
    } catch (err) {
      console.error('批量删除失败:', err);
    }
    setBatchOpen(false);
  };

  const handleBatchProcess = async () => {
    if (selected.size === 0) return;
    try {
      await api.kb.batchProcess([...selected]);
      await fetchDocuments();
    } catch (err) {
      console.error('批量处理失败:', err);
    }
    setBatchOpen(false);
  };

  // 图谱
  const openGraph = async (doc) => {
    setGraphDoc(doc);
    setGraphData(null);
    setGraphLoading(true);
    try {
      const data = await api.kb.getGraph(doc.id);
      setGraphData(data);
    } catch (err) {
      console.error('获取图谱失败:', err);
    } finally {
      setGraphLoading(false);
    }
  };

  // 预览
  const openPreview = async (doc) => {
    setPreviewDoc(doc);
    setPreviewContent(null);
    setPreviewLoading(true);
    try {
      const data = await api.kb.preview(doc.id);
      setPreviewContent(data);
    } catch (err) {
      console.error('预览失败:', err);
    } finally {
      setPreviewLoading(false);
    }
  };

  // 标签编辑
  const handleSaveTags = async () => {
    if (!editTagsDoc) return;
    try {
      const tags = editTagsInput.split(',').map((t) => t.trim()).filter(Boolean);
      await api.kb.updateTags(editTagsDoc.id, tags);
      setEditTagsDoc(null);
      await fetchDocuments();
    } catch (err) {
      console.error('保存标签失败:', err);
    }
  };

  // 辅助
  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === documents.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(documents.map((d) => d.id)));
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-h-0 animate-fade-in">
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'var(--color-border-light)' }}>
          <div><div className="h-5 w-24 rounded" style={{ background: 'var(--color-bg-hover)' }} /></div>
        </div>
        <div className="px-6 py-3 border-b" style={{ borderColor: 'var(--color-border-light)' }}>
          <div className="h-8 w-full max-w-md rounded" style={{ background: 'var(--color-bg-hover)' }} />
        </div>
        <div className="flex-1 p-6">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="h-12 mb-2 rounded flex items-center gap-4" style={{ background: 'var(--color-bg-hover)', opacity: 1 - i * 0.15 }}>
              <div className="h-3 w-3/12 rounded" style={{ background: 'var(--color-bg-white)' }} />
              <div className="h-3 w-1/12 rounded" style={{ background: 'var(--color-bg-white)' }} />
              <div className="h-3 w-1/12 rounded" style={{ background: 'var(--color-bg-white)' }} />
              <div className="h-3 w-1/12 rounded" style={{ background: 'var(--color-bg-white)' }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="flex-1 flex flex-col min-h-0 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-6 py-4 border-b flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
        <div>
          <h1 className="text-lg font-semibold" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: 'var(--color-text-title)' }}>
            知识库
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            共 {total} 个文档
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ToolBtn icon={Icon.download} label="下载" onClick={() => api.kb.download(previewDoc?.id || selected.values().next().value)} disabled={!previewDoc && selected.size !== 1} />
          <ToolBtn icon={Icon.refresh} label="刷新" onClick={fetchDocuments} />
        </div>
      </div>

      {/* ── Search bar ── */}
      <div className="px-6 py-3 border-b flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
        <div className="relative max-w-md">
          <span className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-label)' }}>{Icon.search}</span>
          <input
            type="text"
            value={searchQ}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="搜索文件名..."
            style={{
              width: '100%',
              padding: '7px 12px 7px 36px',
              fontSize: 'var(--fs-sm)',
              background: 'var(--color-bg-off)',
              border: '1px solid var(--color-border)',
              borderRadius: '4px',
              color: 'var(--color-text-body)',
              outline: 'none',
            }}
          />
          {searchQ && (
            <button
              onClick={() => { setSearchQ(''); setQueryParams((p) => ({ ...p, q: '' })); }}
              style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-label)', padding: 4 }}
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          )}
        </div>
      </div>

      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between px-6 py-2.5 border-b flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
        <div className="flex items-center gap-2">
          <Btn icon={Icon.plus} label="新增" onClick={() => setUploadOpen(true)} primary />
          <div style={{ position: 'relative' }}>
            <Btn icon={Icon.batch} label="批量" onClick={() => setBatchOpen(!batchOpen)} disabled={selected.size === 0} />
            {batchOpen && (
              <>
                <div style={{ position: 'fixed', inset: 0, zIndex: 50 }} onClick={() => setBatchOpen(false)} />
                <div style={{
                  position: 'absolute', top: '100%', left: 0, marginTop: 4, zIndex: 51,
                  background: 'var(--color-bg-white)', border: '1px solid var(--color-border)',
                  borderRadius: '4px', minWidth: 140, padding: '4px 0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                }}>
                  <DropdownItem onClick={handleBatchDelete}>批量删除</DropdownItem>
                  <DropdownItem onClick={handleBatchProcess}>批量处理</DropdownItem>
                  <div style={{ height: 1, background: 'var(--color-border-light)', margin: '4px 0' }} />
                  <DropdownItem onClick={() => { setSelected(selected.size === documents.length ? new Set() : new Set(documents.map(d => d.id))); setBatchOpen(false); }}>
                    {selected.size === documents.length ? '取消全选' : '全选'}
                  </DropdownItem>
                </div>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2" style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>
          <span>每页显示:</span>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            style={{
              padding: '4px 8px', fontSize: 'var(--fs-sm)',
              background: 'var(--color-bg-off)', border: '1px solid var(--color-border)',
              borderRadius: '4px', color: 'var(--color-text-body)', outline: 'none',
            }}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* ── Filter bar ── */}
      <div className="flex items-center gap-3 px-6 py-2.5 border-b flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
        <SelectFilter value={fileTypeFilter} onChange={setFileTypeFilter} label="分类" options={[
          { value: '', label: '全部分类' },
          { value: 'text', label: 'TXT' },
          { value: 'markdown', label: 'Markdown' },
          { value: 'pdf', label: 'PDF' },
          { value: 'docx', label: 'DOCX' },
        ]} />
        <SelectFilter value={statusFilter} onChange={setStatusFilter} label="状态" options={[
          { value: '', label: '全部状态' },
          { value: 'pending', label: '待处理' },
          { value: 'processing', label: '处理中' },
          { value: 'completed', label: '已完成' },
          { value: 'failed', label: '失败' },
        ]} />
        <SelectFilter value={sourceFilter} onChange={setSourceFilter} label="来源" options={[
          { value: '', label: '全部来源' },
          { value: 'user', label: '用户上传' },
          { value: 'website', label: '网站' },
        ]} />
        <Btn icon={Icon.query} label="查询" onClick={handleQuery} />
        <Btn icon={Icon.reset} label="重置" onClick={handleReset} />
      </div>

      {/* ── Table ── */}
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
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>还没有文档，点击「+ 新增」上传</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)', minWidth: 800 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-light)', color: 'var(--color-text-label)' }}>
                <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: 500, width: 40 }}>
                  <input type="checkbox" checked={selected.size === documents.length && documents.length > 0}
                    onChange={toggleSelectAll} style={{ cursor: 'pointer' }}
                  />
                </th>
                <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: 500, width: 50 }}>#</th>
                <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: 500 }}>名称</th>
                <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: 500, width: 80 }}>类型</th>
                <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: 500, width: 80 }}>来源</th>
                <th style={{ padding: '10px 8px', textAlign: 'center', fontWeight: 500, width: 70 }}>命中</th>
                <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: 500, width: 160 }}>状态</th>
                <th style={{ padding: '10px 8px', textAlign: 'right', fontWeight: 500, width: 120 }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc, idx) => {
                const seq = (page - 1) * pageSize + idx + 1;
                return (
                  <tr key={doc.id}
                    style={{ borderBottom: '1px solid var(--color-border-light)', transition: 'background 0.12s' }}
                    className="hover:bg-[var(--color-bg-off)]"
                  >
                    <td style={{ padding: '10px 8px' }}>
                      <input type="checkbox" checked={selected.has(doc.id)}
                        onChange={() => toggleSelect(doc.id)} style={{ cursor: 'pointer' }}
                      />
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-text-label)' }}>{seq}</td>
                    <td style={{ padding: '10px 8px' }}>
                      <span onClick={() => openPreview(doc)}
                        style={{ color: 'var(--color-text-title)', fontWeight: 500, cursor: 'pointer' }}
                        className="hover:underline"
                      >
                        {doc.name}
                      </span>
                      {doc.is_public === false && (
                        <span style={{
                          marginLeft: 6, padding: '1px 6px', borderRadius: '3px', fontSize: '10px',
                          background: 'rgba(200,150,10,0.1)', color: '#8c7a0a',
                          border: '1px solid rgba(200,150,10,0.2)',
                          verticalAlign: 'middle',
                        }}>私有</span>
                      )}
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      <span style={{
                        padding: '2px 8px', borderRadius: '3px', fontSize: '10px',
                        background: 'var(--color-bg-hover)', textTransform: 'uppercase',
                        letterSpacing: '0.3px', color: 'var(--color-text-muted)',
                      }}>
                        {doc.file_type === 'markdown' ? 'MD' : doc.file_type?.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-text-muted)', fontSize: '11px' }}>
                      {doc.source === 'website' ? '网站' : '用户'}
                    </td>
                    <td style={{ padding: '10px 8px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      {doc.hit_count ?? 0}
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      <StatusBadge status={doc.status} chunksCount={doc.chunks_count} />
                    </td>
                    <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                      <div className="flex items-center justify-end gap-1">
                        {doc.status === 'completed' && (
                          <IconBtn icon={Icon.graph} title="图谱" onClick={() => openGraph(doc)} />
                        )}
                        <IconBtn icon={Icon.eye} title="预览" onClick={() => openPreview(doc)} />
                        <div style={{ position: 'relative' }}>
                          <IconBtn icon={Icon.dots} title="更多" onClick={() => setMenuDoc(menuDoc === doc.id ? null : doc.id)} />
                          {menuDoc === doc.id && (
                            <>
                              <div style={{ position: 'fixed', inset: 0, zIndex: 50 }} onClick={() => setMenuDoc(null)} />
                              <div style={{
                                position: 'absolute', right: 0, top: '100%', marginTop: 4, zIndex: 51,
                                background: 'var(--color-bg-white)', border: '1px solid var(--color-border)',
                                borderRadius: '4px', minWidth: 120, padding: '4px 0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                              }}>
                                {doc.status === 'failed' && (
                                  <DropdownItem onClick={() => { handleProcess(doc.id); setMenuDoc(null); }}>重试</DropdownItem>
                                )}
                                <DropdownItem onClick={() => {
                                  setEditTagsDoc(doc);
                                  setEditTagsInput((doc.tags || []).join(', '));
                                  setMenuDoc(null);
                                }}>修改标签</DropdownItem>
                                <DropdownItem onClick={() => { api.kb.download(doc.id); setMenuDoc(null); }}>下载</DropdownItem>
                                <div style={{ height: 1, background: 'var(--color-border-light)', margin: '4px 0' }} />
                                <DropdownItem onClick={() => { handleDelete(doc.id, doc.name); setMenuDoc(null); }} danger>删除</DropdownItem>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Pagination ── */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-6 py-3 border-t flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-label)' }}>
            第 {page}/{totalPages} 页，共 {total} 个文档
          </span>
          <div className="flex items-center gap-1">
            <PageBtn disabled={page <= 1} onClick={() => setPage(page - 1)}>‹</PageBtn>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              let n;
              if (totalPages <= 7) {
                n = i + 1;
              } else if (page <= 4) {
                n = i + 1;
              } else if (page >= totalPages - 3) {
                n = totalPages - 6 + i;
              } else {
                n = page - 3 + i;
              }
              return (
                <PageBtn key={n} active={n === page} onClick={() => setPage(n)}>
                  {n}
                </PageBtn>
              );
            })}
            <PageBtn disabled={page >= totalPages} onClick={() => setPage(page + 1)}>›</PageBtn>
          </div>
        </div>
      )}

      {/* ── Drawers ── */}
      <KnowledgeGraphDrawer
        open={!!graphDoc}
        onClose={() => { setGraphDoc(null); setGraphData(null); }}
        doc={graphDoc}
        data={graphData}
        loading={graphLoading}
      />

      <KnowledgePreviewDrawer
        open={!!previewDoc}
        onClose={() => { setPreviewDoc(null); setPreviewContent(null); }}
        doc={previewDoc}
        data={previewContent}
        loading={previewLoading}
      />

      {/* ── Upload Card Modal ── */}
      {uploadOpen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.3)' }}
          onClick={() => setUploadOpen(false)}
        >
          <div onClick={(e) => e.stopPropagation()} style={{
            background: 'var(--color-bg-white)', borderRadius: '6px', padding: '32px',
            width: 'min(480px, 90vw)', boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          }}>
            <h3 className="text-base font-semibold mb-1" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: 'var(--color-text-title)' }}>
              上传文档
            </h3>
            <p className="text-xs mb-5" style={{ color: 'var(--color-text-muted)' }}>
              支持 TXT / Markdown / PDF / DOCX，单文件最大 10MB
            </p>

            {/* 拖拽区域 */}
            <div
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = 'var(--color-border-bold)'; e.currentTarget.style.background = 'var(--color-bg-off)'; }}
              onDragLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.background = 'transparent'; }}
              onDrop={(e) => { e.preventDefault(); handleUpload(e.dataTransfer.files); setUploadOpen(false); }}
              style={{
                padding: '48px 24px', borderRadius: '6px',
                border: '2px dashed var(--color-border)',
                textAlign: 'center', cursor: 'pointer',
                transition: 'all 0.2s', marginBottom: 16,
              }}
              className="hover:bg-[var(--color-bg-off)]"
            >
              <svg className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--color-text-label)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)', marginBottom: 12 }}>
                拖拽文件到此处
              </p>
              <span style={{
                display: 'inline-block', padding: '8px 24px', fontSize: 'var(--fs-sm)',
                background: 'var(--color-text-title)', color: 'var(--color-bg-white)',
                border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 500,
              }}
                onClick={(e) => { e.stopPropagation(); uploadInputRef.current?.click(); }}
                className="hover:opacity-80"
              >
                选择文件
              </span>
              <input ref={uploadInputRef} type="file" accept=".txt,.md,.pdf,.docx" multiple style={{ display: 'none' }}
                onChange={(e) => { handleUpload(e.target.files); setUploadOpen(false); e.target.value = ''; }}
              />
            </div>

            <label className="flex items-center justify-between px-1 mb-4" style={{ cursor: 'pointer' }}
              onClick={() => setUploadPublic(!uploadPublic)}
            >
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                {uploadPublic ? '公开（所有人可见）' : '私有（仅自己可见）'}
              </span>
              <div style={{
                width: 36, height: 20, borderRadius: 10,
                background: uploadPublic ? 'var(--color-text-title)' : 'var(--color-border)',
                position: 'relative', transition: 'background 0.2s',
              }}>
                <div style={{
                  width: 16, height: 16, borderRadius: '50%',
                  background: 'white', position: 'absolute', top: 2,
                  left: uploadPublic ? 18 : 2, transition: 'left 0.2s',
                }} />
              </div>
            </label>

            <div className="flex justify-end gap-2">
              <button onClick={() => setUploadOpen(false)} style={{
                padding: '8px 20px', fontSize: 'var(--fs-sm)', borderRadius: '4px',
                background: 'var(--color-bg-off)', border: '1px solid var(--color-border)',
                cursor: 'pointer', color: 'var(--color-text-body)',
              }}>取消</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Tags Editor Modal ── */}
      {editTagsDoc && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.3)' }}
          onClick={() => setEditTagsDoc(null)}
        >
          <div onClick={(e) => e.stopPropagation()} style={{
            background: 'var(--color-bg-white)', borderRadius: '6px', padding: '24px',
            minWidth: 360, boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          }}>
            <h3 className="text-base font-semibold mb-4" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: 'var(--color-text-title)' }}>
              编辑标签 — {editTagsDoc.name}
            </h3>
            <div className="flex flex-wrap gap-2 mb-3">
              {(editTagsInput.split(',').map(t => t.trim()).filter(Boolean)).map((tag) => (
                <span key={tag} style={{
                  padding: '3px 10px', borderRadius: '3px', fontSize: '12px',
                  background: 'var(--color-border-light)', color: 'var(--color-text-body)',
                  display: 'flex', alignItems: 'center', gap: 6,
                }}>
                  {tag}
                  <button onClick={() => {
                    const tags = editTagsInput.split(',').map(t => t.trim()).filter(Boolean).filter(t => t !== tag);
                    setEditTagsInput(tags.join(', '));
                  }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', padding: 0, fontSize: 14 }}>
                    ×
                  </button>
                </span>
              ))}
            </div>
            <input
              type="text"
              value={editTagsInput}
              onChange={(e) => setEditTagsInput(e.target.value)}
              placeholder="输入标签，用逗号分隔..."
              style={{
                width: '100%', padding: '8px 12px', fontSize: 'var(--fs-sm)',
                border: '1px solid var(--color-border)', borderRadius: '4px',
                background: 'var(--color-bg-off)', color: 'var(--color-text-body)',
                outline: 'none', marginBottom: 16,
              }}
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setEditTagsDoc(null)} style={{
                padding: '8px 20px', fontSize: 'var(--fs-sm)', borderRadius: '4px',
                background: 'var(--color-bg-off)', border: '1px solid var(--color-border)',
                cursor: 'pointer', color: 'var(--color-text-body)',
              }}>取消</button>
              <button onClick={handleSaveTags} style={{
                padding: '8px 20px', fontSize: 'var(--fs-sm)', borderRadius: '4px',
                background: 'var(--color-text-title)', border: 'none',
                cursor: 'pointer', color: 'var(--color-bg-white)', fontWeight: 500,
              }}>保存</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Knowledge Base Chat Bubble ── */}
      <KBChatBubble documentIds={selected.size > 0 ? [...selected] : null} />
    </div>
  );
}

// ── Sub-components ──

function StatusBadge({ status, chunksCount }) {
  const config = {
    pending: { label: '待处理', bg: '#FFF3E0', color: '#E65100' },
    processing: { label: `处理中${chunksCount ? `(${chunksCount})` : ''}`, bg: '#E3F2FD', color: '#1565C0' },
    completed: { label: `已完成${chunksCount ? `(${chunksCount})` : ''}`, bg: '#E8F5E9', color: '#2E7D32' },
    failed: { label: '失败', bg: '#FFEBEE', color: '#C62828' },
  };
  const s = config[status] || { label: status, bg: 'var(--color-bg-off)', color: 'var(--color-text-muted)' };
  return (
    <span style={{ padding: '3px 10px', borderRadius: '3px', fontSize: '11px', background: s.bg, color: s.color, fontWeight: 500, display: 'inline-block' }}>
      {s.label}
    </span>
  );
}

function ToolBtn({ icon, label, onClick, disabled }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '6px 14px', fontSize: 'var(--fs-sm)',
        background: 'transparent', border: '1px solid var(--color-border)',
        borderRadius: '4px', cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.4 : 1, color: 'var(--color-text-muted)',
        transition: 'all 0.12s',
      }}
      className="hover:bg-[var(--color-bg-hover)] hover:border-[var(--color-border-bold)]"
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function Btn({ icon, label, onClick, disabled, primary }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '6px 14px', fontSize: 'var(--fs-sm)',
        background: primary ? 'var(--color-text-title)' : 'transparent',
        border: primary ? 'none' : '1px solid var(--color-border)',
        borderRadius: '4px', cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        color: primary ? 'var(--color-bg-white)' : 'var(--color-text-muted)',
        fontWeight: primary ? 500 : 400,
        transition: 'all 0.12s',
      }}
      className={!primary ? "hover:bg-[var(--color-bg-hover)]" : ""}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function IconBtn({ icon, title, onClick }) {
  return (
    <button onClick={onClick} title={title}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: 30, height: 30, borderRadius: '4px',
        background: 'transparent', border: 'none',
        cursor: 'pointer', color: 'var(--color-text-muted)',
        transition: 'all 0.12s',
      }}
      className="hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-body)]"
    >
      {icon}
    </button>
  );
}

function DropdownItem({ onClick, children, danger }) {
  return (
    <button onClick={onClick}
      style={{
        display: 'block', width: '100%', textAlign: 'left',
        padding: '7px 16px', fontSize: 'var(--fs-sm)',
        background: 'transparent', border: 'none',
        cursor: 'pointer', transition: 'background 0.1s',
        color: danger ? 'var(--color-high)' : 'var(--color-text-body)',
      }}
      className="hover:bg-[var(--color-bg-hover)]"
    >
      {children}
    </button>
  );
}

function PageBtn({ disabled, active, onClick, children }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        minWidth: 32, height: 32, padding: '0 6px',
        fontSize: '13px', borderRadius: '4px',
        background: active ? 'var(--color-text-title)' : 'transparent',
        color: active ? 'var(--color-bg-white)' : 'var(--color-text-muted)',
        border: active ? 'none' : '1px solid transparent',
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontWeight: active ? 600 : 400,
        opacity: disabled ? 0.4 : 1,
        transition: 'all 0.12s',
      }}
      className={!active && !disabled ? "hover:bg-[var(--color-bg-hover)] hover:border-[var(--color-border)]" : ""}
    >
      {children}
    </button>
  );
}

function SelectFilter({ value, onChange, label, options }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        padding: '6px 12px', fontSize: 'var(--fs-sm)',
        background: 'var(--color-bg-off)', border: '1px solid var(--color-border)',
        borderRadius: '4px', color: 'var(--color-text-body)', outline: 'none',
      }}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  );
}
