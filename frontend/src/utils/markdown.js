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
    // **bold** (must come before *italic*)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // *italic*
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // `inline code`
    .replace(/`(.+?)`/g, '<code style="font-size:0.9em;background:var(--color-bg-hover);padding:1px 4px;border-radius:2px">$1</code>')
    // newlines
    .replace(/\n/g, '<br/>');
}
