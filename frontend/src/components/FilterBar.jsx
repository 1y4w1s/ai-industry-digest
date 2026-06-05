import Select from './Select';

const IMPORTANCE_OPTIONS = [
  { value: '', label: '全部重要度', dotColor: 'var(--color-high)' },
  { value: 'high', label: '高', dotColor: 'var(--color-high)' },
  { value: 'medium', label: '中', dotColor: 'var(--color-medium)' },
  { value: 'low', label: '低', dotColor: 'var(--color-low)' },
];

export default function FilterBar({
  importance, source, tag,
  sources, tags,
  activeFilterCount,
  onImportanceChange, onSourceChange, onTagChange, onClear,
  onToggleSidePanel, sidePanelOpen,
}) {
  const isActive = activeFilterCount > 0;
  const sourceOptions = [{ value: '', label: '全部来源' }, ...sources.map((s) => ({ value: s, label: s }))];
  const tagOptions = [{ value: '', label: '全部标签' }, ...tags.map((t) => ({ value: t, label: t }))];

  const handleTagChange = (newTags) => {
    onTagChange(newTags);
  };

  return (
    <div style={{ background: 'var(--color-bg-off)', borderBottom: '1px solid var(--color-border-light)', padding: '6px 16px' }}>
      <div className="flex items-center gap-2 flex-wrap">
        <Select
          value={importance}
          onChange={onImportanceChange}
          options={IMPORTANCE_OPTIONS}
          placeholder="重要性"
        />
        <Select
          value={source}
          onChange={onSourceChange}
          options={sourceOptions}
          placeholder="来源"
        />
        <Select
          value={tag}
          onChange={handleTagChange}
          options={tagOptions}
          placeholder="标签"
          multi
        />

        {isActive && (
          <div className="flex items-center gap-2" style={{ marginLeft: '4px' }}>
            <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>
              {activeFilterCount} 个筛选中
            </span>
            <button
              onClick={onClear}
              style={{
                fontSize: 'var(--fs-sm)',
                color: 'var(--color-blue-link)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
                textDecoration: 'none',
              }}
              onMouseEnter={(e) => e.target.style.textDecoration = 'underline'}
              onMouseLeave={(e) => e.target.style.textDecoration = 'none'}
            >
              清除
            </button>
          </div>
        )}
        
        {onToggleSidePanel && (
          <button onClick={onToggleSidePanel}
            className="hidden lg:flex xl:hidden ml-auto items-center gap-1 px-2 py-1 text-[11px] rounded cursor-pointer"
            style={{ background: 'var(--color-bg-toolbar)', border: '1px solid var(--color-border-light)', color: 'var(--color-text-muted)' }}>
            <span style={{ display: 'inline-block', transition: 'transform 0.2s', transform: sidePanelOpen ? 'rotate(180deg)' : 'none' }}>◀</span>
          </button>
        )}
      </div>
    </div>
  );
}
