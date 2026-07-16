import { IconPDF } from './icons';

export default function PDFExportButton({ onExport, disabled }) {
  return (
    <div className="mt-8 pt-6 text-center no-print" style={{ borderTop: '1px solid var(--color-border-light)' }}>
      <button onClick={onExport} disabled={disabled}
        style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '12px', color: 'var(--color-text-muted)', background: 'transparent', border: '1px solid var(--color-border)', borderRadius: '4px', cursor: 'pointer', transition: 'all 0.15s' }}>
        <IconPDF />
        导出 PDF
      </button>
    </div>
  );
}
