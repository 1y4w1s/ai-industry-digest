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
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
      // 内部链接使用 SPA 导航，外部链接新标签打开
      if (url.startsWith('/')) {
        return `<a href="${url}" style="color:var(--color-blue-link);text-decoration:underline">${text}</a>`;
      }
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color:var(--color-blue-link);text-decoration:underline">${text}</a>`;
    })
    .replace(/\n/g, '<br/>');
}

/**
 * Detect if text contains HTML block-level tags
 */
function hasHtmlTags(text) {
  return /<(\/)?(p|h[1-4]|ul|ol|li|blockquote|div|pre|br|strong|em)[^>]*>/i.test(text);
}

/**
 * Safely render article content: HTML preserved if present, plain text formatted otherwise
 */
export function renderArticleContent(text) {
  if (!text) return '暂无原文内容';

  if (hasHtmlTags(text)) {
    // Content has HTML — render directly with safe tag filtering
    return sanitizeHtml(text);
  }

  // Plain text — format with typography
  return formatPlainText(text);
}

/**
 * Strip unsafe tags, only allow formatting/structural HTML
 */
function sanitizeHtml(html) {
  const allowed = new Set([
    'p', 'br', 'h1', 'h2', 'h3', 'h4',
    'ul', 'ol', 'li',
    'strong', 'b', 'em', 'i', 'u',
    'blockquote', 'pre', 'code', 'span', 'div',
    'hr',
  ]);

  // Escape & < > first to prevent XSS
  let safe = html
    .replace(/&(?!(?:amp|lt|gt|quot|#\d+);)/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Restore actual < > for allowed tags
  const tagPattern = /&lt;(\/?)(\w+)([^&]*)&gt;/g;
  safe = safe.replace(tagPattern, (match, slash, tagName, attrs) => {
    const tag = tagName.toLowerCase();
    if (allowed.has(tag)) {
      // Remove all attributes except class, keep it clean
      return `<${slash}${tag}>`;
    }
    // Return escaped text for disallowed tags (strip tag, keep content)
    return '';
  });

  // Decode HTML entities back for readable display
  safe = safe
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#8211;/g, '—')
    .replace(/&#8212;/g, '—')
    .replace(/&#8216;/g, "'")
    .replace(/&#8217;/g, "'")
    .replace(/&#8220;/g, '"')
    .replace(/&#8221;/g, '"')
    .replace(/&#8230;/g, '…');

  // Normalize excess blank lines
  safe = safe.replace(/\n{3,}/g, '\n\n');

  return safe;
}

/**
 * Format plain text into typographic HTML
 */
function formatPlainText(text) {
  const formatInline = (s) => s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="font-size:0.85em;background:var(--color-bg-hover);padding:1px 4px;border-radius:2px">$1</code>');

  const lines = text.split('\n');
  const result = [];
  let inList = false;
  let listType = null;

  const closeList = () => {
    if (inList) {
      result.push(`</${listType}>`);
      inList = false;
      listType = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();

    if (!trimmed) { closeList(); continue; }

    // headers
    if (/^#{1,3}\s/.test(trimmed)) {
      closeList();
      const level = trimmed.match(/^#+/)[0].length;
      const content = formatInline(trimmed.replace(/^#+\s*/, ''));
      const tag = `h${Math.min(level + 1, 4)}`;
      const sizes = { h2: '18px', h3: '16px', h4: '15px' };
      result.push(`<${tag} style="font-family:var(--font-display);font-size:${sizes[tag]||'15px'};font-weight:700;color:var(--color-text-title);margin:1.5em 0 0.5em;line-height:1.4">${content}</${tag}>`);
      continue;
    }

    // bold line as sub-header
    if (/^\*\*[^*]+\*\*/.test(trimmed) && trimmed.length < 80) {
      closeList();
      result.push(`<div style="font-weight:600;color:var(--color-text-title);margin:1.2em 0 0.3em;font-size:14px">${formatInline(trimmed)}</div>`);
      continue;
    }

    // blockquote
    if (/^>\s?/.test(trimmed)) {
      closeList();
      result.push(`<blockquote style="margin:1em 0;padding:10px 14px;background:var(--color-bg-off);border-left:3px solid var(--color-border);border-radius:0 4px 4px 0;color:var(--color-text-body);font-size:14px;line-height:1.7">${formatInline(trimmed.replace(/^>\s?/, ''))}</blockquote>`);
      continue;
    }

    // bullet list
    if (/^[-*]\s/.test(trimmed)) {
      if (!inList || listType !== 'ul') { closeList(); result.push('<ul style="margin:0.5em 0;padding-left:1.5em;list-style:disc">'); inList = true; listType = 'ul'; }
      result.push(`<li style="margin:0.3em 0;color:var(--color-text-body);font-size:14px;line-height:1.7">${formatInline(trimmed.replace(/^[-*]\s*/, ''))}</li>`);
      continue;
    }

    // numbered list
    if (/^\d+[\.\u3002]\s/.test(trimmed)) {
      if (!inList || listType !== 'ol') { closeList(); result.push('<ol style="margin:0.5em 0;padding-left:1.5em">'); inList = true; listType = 'ol'; }
      result.push(`<li style="margin:0.3em 0;color:var(--color-text-body);font-size:14px;line-height:1.7">${formatInline(trimmed.replace(/^\d+[\.\u3002]\s*/, ''))}</li>`);
      continue;
    }

    // paragraph
    closeList();
    const prevEnd = result[result.length - 1] || '';
    if (prevEnd && !prevEnd.endsWith('</p>') && !prevEnd.endsWith('</h2>') && !prevEnd.endsWith('</h3>') && !prevEnd.endsWith('</h4>') && !prevEnd.endsWith('</div>') && !prevEnd.endsWith('</blockquote>') && !prevEnd.endsWith('</ul>') && !prevEnd.endsWith('</ol>')) {
      result.push('<br/>' + formatInline(trimmed));
    } else {
      result.push(`<p style="margin:0.5em 0;color:var(--color-text-body);font-size:15px;line-height:1.8">${formatInline(trimmed)}`);
    }
  }

  closeList();
  const last = result[result.length - 1] || '';
  if (last.startsWith('<p ') && !last.endsWith('</p>')) result[result.length - 1] = last + '</p>';
  return result.join('\n');
}
