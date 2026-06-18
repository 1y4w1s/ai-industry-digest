import { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import { renderMd } from '../utils/markdown';
import DOMPurify from 'dompurify';

export default function KBChatBubble({ documentIds = null }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState([]);  // 引用的知识库来源
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await api.kb.chat(userMessage, documentIds, sessionId);
      setSessionId(response.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }]);
      setSources(response.sources || []);
    } catch (err) {
      setMessages((prev) => [...prev, { 
        role: 'assistant', 
        content: `抱歉，知识库对话失败：${err.message}` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed right-6 bottom-6 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-105 z-50"
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}
        title="知识库对话"
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>
    );
  }

  return (
    <div
      className="fixed right-6 bottom-6 w-96 h-[500px] rounded-xl shadow-2xl flex flex-col z-50"
      style={{
        background: 'var(--color-bg-white)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 border-b flex items-center justify-between"
        style={{ borderColor: 'var(--color-border-light)' }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-semibold" style={{ color: 'var(--color-text-title)' }}>
              知识库助手
            </div>
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              {documentIds ? '限定文档对话' : '全库对话'}
            </div>
          </div>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="p-1 rounded hover:bg-gray-100 transition-colors"
          style={{ color: 'var(--color-text-muted)' }}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div
              className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
              style={{ background: 'var(--color-bg-off)' }}
            >
              <svg className="w-6 h-6" style={{ color: 'var(--color-text-label)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
              我是知识库助手，可以帮您查询和理解知识库中的文档内容
            </p>
            <div className="mt-4 flex flex-wrap gap-2 justify-center">
              {['知识库中有哪些文档？', '帮我总结一下文档内容', '查找关于AI的技术文档'].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="px-2.5 py-1 text-xs rounded transition-all"
                  style={{
                    background: 'var(--color-bg-hover)',
                    color: 'var(--color-text-muted)',
                    border: '1px solid var(--color-border-light)',
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className="max-w-[85%] px-3 py-2 rounded text-xs leading-relaxed"
              style={
                msg.role === 'user'
                  ? {
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                    }
                  : {
                      background: 'var(--color-bg-off)',
                      color: 'var(--color-text-body)',
                      border: '1px solid var(--color-border-light)',
                    }
              }
            >
              {msg.role === 'assistant' ? (
                <div
                  dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(renderMd(msg.content)),
                  }}
                />
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div
              className="px-3 py-2 rounded text-xs"
              style={{
                background: 'var(--color-bg-off)',
                color: 'var(--color-text-muted)',
                border: '1px solid var(--color-border-light)',
              }}
            >
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-current" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-current" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-current" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        {/* Sources */}
        {sources.length > 0 && messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
          <div className="mt-2 pt-2 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
            <div className="text-xs mb-1" style={{ color: 'var(--color-text-label)' }}>
              参考来源：
            </div>
            <div className="space-y-1">
              {sources.map((source, idx) => (
                <div
                  key={idx}
                  className="text-xs flex items-center gap-1"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  <span className="w-1 h-1 rounded-full" style={{ background: 'var(--color-text-label)' }} />
                  <span>{source.name}</span>
                  <span className="text-xs" style={{ color: 'var(--color-border)' }}>
                    (相关度: {source.relevance})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="询问知识库内容..."
            disabled={loading}
            className="flex-1 px-3 py-2 text-xs rounded-lg outline-none transition-all"
            style={{
              background: 'var(--color-bg-off)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-body)',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--color-border-focus)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'var(--color-border)';
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-4 py-2 text-xs rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
            }}
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}