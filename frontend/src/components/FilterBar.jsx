import Select from './Select';

const IMPORTANCE_OPTIONS = [
  { value: '', label: '全部重要度', dotColor: null },
  { value: 'high', label: '高', dotColor: '#D4322E' },
  { value: 'medium', label: '中', dotColor: '#C8960A' },
  { value: 'low', label: '低', dotColor: '#8C9096' },
];

export default function FilterBar({
  importance, source, tag,
  sources, tags,
  activeFilterCount,
  onImportanceChange, onSourceChange, onTagChange, onClear,
}) {
  const isActive = activeFilterCount > 0;
  const sourceOptions = [{ value: '', label: '全部来源' }, ...sources.map((s) => ({ value: s, label: s }))];
  // Tag options: first option is "全部" (value=''), then individual tags
  const tagOptions = [{ value: '', label: '全部标签' }, ...tags.map((t) => ({ value: t, label: t }))];

  const handleTagChange = (newTags) => {
    onTagChange(newTags); // newTags is an array in multi-select mode
  };

  return (
    <div style={{ background: '#F6F7F8', borderBottom: '1px solid #E8EAED', padding: '6px 16px' }}>
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

        {/* Filter status + clear */}
        {isActive && (
          <div className="flex items-center gap-2" style={{ marginLeft: '4px' }}>
            <span style={{ fontSize: '11px', color: '#686C72' }}>
              {activeFilterCount} 个筛选中
            </span>
            <button
              onClick={onClear}
              style={{
                fontSize: '11px',
                color: '#2864A8',
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
      </div>
    </div>
  );
}
