export default function DataStats({ totalArticles, sourceCount, highCount }) {
  return (
    <div style={{
      fontSize: '12px',
      color: '#686C72',
      marginTop: '8px',
      marginBottom: '20px',
      paddingTop: '8px',
      borderTop: '1px solid #E8EAED',
    }}>
      {totalArticles} 篇文章 · {sourceCount} 个来源 · {highCount} 篇高重要性
    </div>
  );
}
