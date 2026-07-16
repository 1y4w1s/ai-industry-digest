import { IconShare, IconPlay, IconPause, IconStop, IconBookmark, IconBookmarkFilled } from './icons';
import PDFExportButton from './PDFExportButton';

/**
 * ArticleMetaActions — 文章元数据 + 操作按钮行
 *
 * Props:
 *   article:      { source_name, published_at, url }
 *   readingMinutes: number
 *   articleText:  string (用于 TTS)
 *   tts:          { supported: bool, state: string, toggle: fn, stop: fn }
 *   isBookmarked: bool
 *   onShare:      fn
 *   onBookmark:   fn
 *   onExportPDF:  fn
 *   exporting:    bool
 */
export default function ArticleMetaActions({
  article, readingMinutes, articleText,
  tts, isBookmarked,
  onShare, onBookmark, onExportPDF, exporting,
}) {
  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-6" style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
        <div className="flex items-center gap-2">
          <span>{article.source_name}</span><span>·</span><span>{article.published_at?.slice(0, 10)}</span><span>·</span><span>{readingMinutes} 分钟阅读</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap sm:ml-auto no-print">
          {/* 分享 / 复制链接 */}
          <button onClick={onShare} title="分享 / 复制链接"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: 'var(--color-text-muted)', transition: 'color 0.15s' }}>
            <IconShare />
            <span>分享</span>
          </button>

          {/* TTS button — hidden on devices without SpeechSynthesis */}
          {tts.supported && (<>
          <button onClick={() => tts.toggle(articleText)}
            title={tts.state === 'idle' ? '朗读' : tts.state === 'playing' ? '暂停' : '继续'}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: tts.state !== 'idle' ? 'var(--color-brass)' : 'var(--color-text-muted)', transition: 'color 0.15s' }}>
            {tts.state === 'playing' ? <IconPause /> : <IconPlay />}
            <span>{tts.state === 'idle' ? '朗读' : tts.state === 'playing' ? '暂停' : '继续'}</span>
          </button>
          {tts.state !== 'idle' && (
            <button onClick={() => tts.stop()}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: 'var(--color-text-muted)' }}>
              <IconStop />
            </button>
          )}
          </>)}

          {/* Bookmark button */}
          <button onClick={onBookmark} title={isBookmarked ? '取消收藏' : '收藏'}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: isBookmarked ? '#C8960A' : 'var(--color-text-muted)', transition: 'color 0.15s' }}>
            {isBookmarked ? <IconBookmarkFilled /> : <IconBookmark />}
            <span>{isBookmarked ? '已收藏' : '收藏'}</span>
          </button>
          {article.url && (<a href={article.url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-brass)' }}>在新窗口阅读 ↗</a>)}
        </div>
      </div>

      {/* PDF export */}
      <PDFExportButton onExport={onExportPDF} disabled={exporting} />
    </>
  );
}
