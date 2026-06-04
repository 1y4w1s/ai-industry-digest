export default function DataStats({ totalArticles, sourceCount, highCount }) {
  return (
    <div style={{
      fontSize: 'var(--fs-sm)',
      color: 'var(--color-text-muted)',
      marginTop: '8px',
      marginBottom: '20px',
      paddingTop: '8px',
      borderTop: '1px solid var(--color-border-light)',
    }}>
      {totalArticles} 篇文章 · {sourceCount} 个来源 · {highCount} 篇高重要性
    </div>
  );
}
