/**
 * Lightweight inline markdown → HTML renderer
 * Handles: **bold**, *italic*, `code`, newlines
 */
export function renderMd(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="font-size:0.9em;background:var(--color-bg-hover);padding:1px 4px;border-radius:2px">$1</code>')
    .replace(/\n/g, '<br/>');
}

/**
 * Format article content with proper typography and hierarchy
 * Handles headers, lists, paragraphs, blockquotes, and inline formatting
 */
export function formatArticleContent(text) {
  if (!text) return '';

  // Escape HTML
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Process inline formatting first (within lines)
  const formatInline = (s) => s
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="font-size:0.85em;background:var(--color-bg-hover);padding:1px 4px;border-radius:2px">$1</code>');

  const lines = safe.split('\n');
  const result = [];
  let inList = false;
  let listType = null; // 'ul' or 'ol'

  const closeList = () => {
    if (inList) {
      result.push(`</${listType}>`);
      inList = false;
      listType = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const trimmed = raw.trim();

    // Empty line = paragraph break
    if (!trimmed) {
      closeList();
      // Add paragraph spacing (unless previous was already a block)
      const prev = result[result.length - 1] || '';
      if (prev && !prev.endsWith('</p>') && !prev.endsWith('</h3>') && !prev.endsWith('</h2>') && !prev.endsWith('</h1>') && !prev.endsWith('</blockquote>') && !prev.endsWith('</ul>') && !prev.endsWith('</ol>')) {
        result.push('</p><p style="margin-top:1em">');
      }
      continue;
    }

    // Headers: ## Title or ### Title
    if (/^#{1,3}\s/.test(trimmed)) {
      closeList();
      const level = trimmed.match(/^#+/)[0].length;
      const content = formatInline(trimmed.replace(/^#+\s*/, ''));
      const tag = `h${level + 1}`; // h2 for ##, h3 for ###
      const sizes = { h2: '18px', h3: '16px', h4: '15px' };
      result.push(
        `<${tag} style="font-family:var(--font-display);font-size:${sizes[tag] || '15px'};font-weight:700;color:var(--color-text-title);margin:1.5em 0 0.5em 0;line-height:1.4">${content}</${tag}>`
      );
      continue;
    }

    // Lines starting with **bold** at beginning → treat as sub-header
    if (/^\*\*[^*]+\*\*/.test(trimmed) && trimmed.length < 80) {
      closeList();
      const content = formatInline(trimmed);
      result.push(
        `<div style="font-weight:600;color:var(--color-text-title);margin:1.2em 0 0.3em 0;font-size:14px">${content}</div>`
      );
      continue;
    }

    // Blockquotes: > text
    if (/^>\s?/.test(trimmed)) {
      closeList();
      const content = formatInline(trimmed.replace(/^>\s?/, ''));
      result.push(
        `<blockquote style="margin:1em 0;padding:10px 14px;background:var(--color-bg-off);border-left:3px solid var(--color-border);border-radius:0 4px 4px 0;color:var(--color-text-body);font-size:14px;line-height:1.7">${content}</blockquote>`
      );
      continue;
    }

    // Bullet list: - or *
    if (/^[-*]\s/.test(trimmed)) {
      if (!inList || listType !== 'ul') {
        closeList();
        result.push('<ul style="margin:0.5em 0;padding-left:1.5em;list-style:disc">');
        inList = true;
        listType = 'ul';
      }
      result.push(`<li style="margin:0.3em 0;color:var(--color-text-body);font-size:14px;line-height:1.7">${formatInline(trimmed.replace(/^[-*]\s*/, ''))}</li>`);
      continue;
    }

    // Numbered list: 1. 2. etc.
    if (/^\d+[\.\u3002]\s/.test(trimmed)) {
      if (!inList || listType !== 'ol') {
        closeList();
        result.push('<ol style="margin:0.5em 0;padding-left:1.5em">');
        inList = true;
        listType = 'ol';
      }
      result.push(`<li style="margin:0.3em 0;color:var(--color-text-body);font-size:14px;line-height:1.7">${formatInline(trimmed.replace(/^\d+[\.\u3002]\s*/, ''))}</li>`);
      continue;
    }

    // Regular paragraph line
    closeList();
    // If previous line was a heading/blockquote close, just add paragraph
    const prevClose = result[result.length - 1] || '';
    if (!prevClose.endsWith('</p>') && !prevClose.endsWith('</h2>') && !prevClose.endsWith('</h3>') && !prevClose.endsWith('</h4>') && !prevClose.endsWith('</div>') && !prevClose.endsWith('</blockquote>') && !prevClose.endsWith('</ul>') && !prevClose.endsWith('</ol>') && prevClose !== '') {
      // Continuation of previous paragraph → add line break
      result.push('<br/>' + formatInline(trimmed));
    } else {
      result.push(`<p style="margin:0.5em 0;color:var(--color-text-body);font-size:15px;line-height:1.8">${formatInline(trimmed)}`);
    }
  }

  // Close any open tags
  closeList();
  // Close last paragraph if open
  const last = result[result.length - 1] || '';
  if (last.startsWith('<p ') && !last.endsWith('</p>')) {
    result[result.length - 1] = last + '</p>';
  }

  return result.join('\n');
}
