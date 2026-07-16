import { forwardRef } from 'react';
import DOMPurify from 'dompurify';
import { renderMd } from '../utils/markdown';

/**
 * ChatPanel — AI 深入对话面板
 * forwardRef 透传 chatInputRef
 */
const ChatPanel = forwardRef(function ChatPanel({
  messages, chatInput, chatLoading, chatCollapsed,
  article, chatEndRef,
  onInputChange, onSubmit, onToggleCollapse, onSelectPrompt,
}, inputRef) {
  return (
    <div className="w-full lg:w-[400px] xl:w-[440px] flex-shrink-0 flex flex-col no-print lg:border-t-0" style={{ background: 'var(--color-bg-off)', borderTop: '1px solid var(--color-border-light)' }}>
      <div className="flex flex-col min-h-0 max-h-[40vh] lg:max-h-none h-full" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* 标题栏 + 移动端折叠按钮 */}
        <div className="px-5 pt-4 pb-2 flex-shrink-0 flex items-center justify-between">
          <h3 className="font-semibold text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>深入对话</h3>
          <button onClick={onToggleCollapse}
            className="lg:hidden flex items-center justify-center"
            style={{ background: 'var(--color-bg-hover)', border: 'none', borderRadius: '3px', cursor: 'pointer', padding: '2px 8px', fontSize: '11px', color: 'var(--color-text-label)' }}>
            {chatCollapsed ? '展开' : '折叠'}
          </button>
        </div>

        {/* 折叠内容 — 移动端折叠时隐藏 */}
        <div className={`flex-1 flex flex-col min-h-0 ${chatCollapsed ? 'hidden' : ''}`}>
          {/* 消息区 — 可滚动 */}
          <div className="flex-1 overflow-y-auto px-4 pb-2 space-y-2.5 min-h-0">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full" style={{ padding: '24px 12px' }}>
                <p className="text-xs mb-4" style={{ color: 'var(--color-text-label)' }}>问关于这篇文章的问题</p>
                <div className="flex flex-col gap-2 w-full max-w-[320px]">
                  {(() => {
                    const tags = article?.tags || [];
                    const prompts = ['总结核心观点', '有哪些技术细节？', '有什么争议？', '这篇文章的局限性？'];
                    if (tags.length > 0) {
                      prompts.push(`解释本文中的「${tags[0]}」概念`);
                      if (tags.length > 1) prompts.push(`本文如何体现「${tags[1]}」的发展？`);
                      if (tags.length > 2) prompts.push(`「${tags[2]}」在其中的作用是什么？`);
                      prompts.push(`和同类文章相比，本文的独特之处？`);
                    }
                    return [...new Set(prompts)].slice(0, 7).map((q) => (
                      <button key={q} onClick={() => { onSelectPrompt(q); }}
                        className="w-full text-left px-3.5 py-2.5 text-xs rounded transition-all hover:brightness-95"
                        style={{ background: 'var(--color-bg-white)', border: '1px solid var(--color-border-light)', color: 'var(--color-text-body)' }}>{q}</button>
                    ));
                  })()}
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className="max-w-[90%] px-3 py-2 text-xs leading-relaxed rounded"
                style={msg.role === 'user'
                  ? { background: 'var(--color-text-title)', color: 'var(--color-bg-white)' }
                  : { background: 'var(--color-bg-white)', color: 'var(--color-text-body)' }}>
                <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(renderMd(msg.content)) }} />
              </div>
            </div>
          ))}
          {chatLoading && (
            <div className="flex justify-start">
              <div className="px-3 py-2 rounded flex gap-1" style={{ background: 'var(--color-bg-white)' }}>
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        <div className="p-4 pt-3 flex-shrink-0" style={{ borderTop: '1px solid var(--color-border-light)' }}>
          <form onSubmit={onSubmit} className="flex gap-2">
            <input ref={inputRef} type="text" value={chatInput} onChange={(e) => onInputChange(e.target.value)}
              placeholder="输入问题..." className="flex-1 px-3 py-2 text-sm rounded"
              style={{ background: 'var(--color-bg-white)', border: '1px solid var(--color-border)', color: 'var(--color-text-body)' }} />
            <button type="submit" disabled={chatLoading || !chatInput.trim()}
              className="px-4 py-2 text-sm rounded disabled:opacity-40 font-medium"
              style={{ background: 'var(--color-text-title)', color: 'var(--color-bg-white)' }}>发送</button>
          </form>
        </div>
      </div>
    </div>
    </div>
  );
});

export default ChatPanel;
