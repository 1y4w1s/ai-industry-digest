import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

const STAGE_LABELS = {
  pending: '排队中',
  reading: '读取文件',
  cleaning: '数据清洗',
  extracting_images: '提取图片',
  chunking: '切片中',
  embedding: '向量化',
  saving_chunks: '保存切片',
  extracting: '实体识别',
  saving_entities: '保存实体',
  enriching: '完善元数据',
  completed: '完成',
  failed: '失败',
};

const STAGE_ORDER = [
  'pending', 'reading', 'cleaning', 'extracting_images',
  'chunking', 'embedding', 'saving_chunks',
  'extracting', 'saving_entities', 'enriching',
  'completed', 'failed',
];

function getStageIndex(stage) {
  const idx = STAGE_ORDER.indexOf(stage);
  return idx >= 0 ? idx : -1;
}

function FileProgressItem({ name, progress }) {
  const stage = progress?.stage || 'pending';
  const percent = progress?.percent || 0;
  const detail = progress?.detail || '';
  const isDone = stage === 'completed';
  const isFailed = stage === 'failed';
  const stageIndex = getStageIndex(stage);

  return (
    <div style={{ marginBottom: 16, padding: '12px 16px', borderRadius: 6, border: '1px solid var(--color-border)', background: isDone ? 'var(--color-bg-off, #f8f9fa)' : 'transparent' }}>
      {/* 文件名 + 状态 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontSize: 'var(--fs-sm, 0.875rem)', fontWeight: 500, color: 'var(--color-text-title)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, marginRight: 8 }}>
          {name}
        </span>
        <span style={{
          fontSize: '0.75rem', fontWeight: 500, whiteSpace: 'nowrap',
          color: isDone ? 'var(--color-success, #22c55e)' : isFailed ? 'var(--color-danger, #ef4444)' : 'var(--color-text-label)',
        }}>
          {isDone ? '✅ 完成' : isFailed ? '❌ 失败' : STAGE_LABELS[stage] || stage}
        </span>
      </div>

      {/* 进度条 */}
      <div style={{ height: 4, borderRadius: 2, background: 'var(--color-border, #e5e7eb)', overflow: 'hidden', marginBottom: 4 }}>
        <div style={{
          height: '100%', borderRadius: 2, transition: 'width 0.4s ease',
          width: `${isDone ? 100 : isFailed ? 0 : percent}%`,
          background: isFailed ? 'var(--color-danger, #ef4444)' : 'var(--color-text-title, #1f2937)',
        }} />
      </div>

      {/* 详情文字 */}
      {!isDone && !isFailed && detail && (
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: 0 }}>{detail}</p>
      )}
    </div>
  );
}

export default function UploadProgressPanel({ files, onDone }) {
  const [progresses, setProgresses] = useState({});
  const eventSourcesRef = useRef([]);

  // 连接 SSE
  useEffect(() => {
    const sources = files.map(file => {
      const url = api.kb.getProgressUrl(file.id);
      const es = new EventSource(url);

      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setProgresses(prev => ({ ...prev, [file.id]: data }));
        } catch { /* ignore parse errors */ }
      };

      es.onerror = () => { es.close(); };
      return es;
    });

    eventSourcesRef.current = sources;

    return () => {
      sources.forEach(es => es.close());
      eventSourcesRef.current = [];
    };
  }, [files]);

  // 判断是否全部完成
  const allDone = files.length > 0 && files.every(f => {
    const p = progresses[f.id];
    return p && (p.stage === 'completed' || p.stage === 'failed');
  });

  return (
    <div>
      <h3 className="text-base font-semibold mb-1" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: 'var(--color-text-title)' }}>
        文档处理中
      </h3>
      <p className="text-xs mb-5" style={{ color: 'var(--color-text-muted)' }}>
        {allDone ? '所有文件处理完成' : '后台正在处理文件，请稍候...'}
      </p>

      <div style={{ maxHeight: 360, overflowY: 'auto' }}>
        {files.map(file => (
          <FileProgressItem
            key={file.id}
            name={file.name}
            progress={progresses[file.id]}
          />
        ))}
      </div>

      {allDone && (
        <button
          onClick={onDone}
          style={{
            display: 'block', width: '100%', marginTop: 16, padding: '10px 0',
            fontSize: 'var(--fs-sm, 0.875rem)', fontWeight: 500,
            background: 'var(--color-text-title, #1f2937)', color: 'var(--color-bg-white, #fff)',
            border: 'none', borderRadius: 4, cursor: 'pointer',
          }}
          className="hover:opacity-80"
        >
          完成
        </button>
      )}
    </div>
  );
}
