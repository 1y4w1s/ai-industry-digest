import { useState, useEffect, useRef, useCallback } from 'react';

const NODE_RADIUS = 24;
const COLORS = {
  concept: '#4A90D9',
  person: '#D4322E',
  organization: '#2E7D32',
  technology: '#C8960A',
  product: '#8E6BBF',
};

const RELATION_LABELS = {
  is_a: '是一种',
  part_of: '是...的一部分',
  related_to: '相关',
  based_on: '基于',
  developed_by: '由...开发',
  author_of: '作者',
  published_by: '发布',
};

export default function KnowledgeGraphDrawer({ open, onClose, doc, data, loading }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [dimensions, setDimensions] = useState({ w: 600, h: 500 });

  // 监听容器尺寸
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setDimensions({ w: Math.max(width, 300), h: Math.max(height - 60, 400) });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [open]);

  // 力导向布局
  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    const { w, h } = dimensions;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    ctx.scale(dpr, dpr);

    const { nodes: nodeList, edges } = data;
    if (!nodeList?.length) return;

    // 初始化位置（圆形布局）
    const nodes = nodeList.map((n, i) => {
      const angle = (2 * Math.PI * i) / nodeList.length;
      const radius = Math.min(w, h) * 0.28;
      return {
        ...n,
        x: w / 2 + radius * Math.cos(angle),
        y: h / 2 + radius * Math.sin(angle),
        vx: 0, vy: 0,
        pinned: false,
      };
    });

    const nodeMap = {};
    nodes.forEach((n) => { nodeMap[n.id] = n; });

    const links = edges
      .filter((e) => nodeMap[e.source_entity_id] && nodeMap[e.target_entity_id])
      .map((e) => ({
        source: nodeMap[e.source_entity_id],
        target: nodeMap[e.target_entity_id],
        type: e.relation_type,
        label: e.label || RELATION_LABELS[e.relation_type] || e.relation_type,
      }));

    // 力导向迭代
    const W = w, H = h;
    const iterations = 120;
    const repulsion = 1200;
    const attraction = 0.006;
    const damping = 0.85;
    const centerForce = 0.02;

    for (let iter = 0; iter < iterations; iter++) {
      const cooling = 1 - iter / iterations;

      // 互斥力
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsion / (dist * dist) * cooling;
          a.vx += (dx / dist) * force;
          a.vy += (dy / dist) * force;
          b.vx -= (dx / dist) * force;
          b.vy -= (dy / dist) * force;
        }
      }

      // 吸引力（连线）
      for (const link of links) {
        const a = link.source, b = link.target;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 100) * attraction * cooling;
        a.vx += (dx / dist) * force;
        a.vy += (dy / dist) * force;
        b.vx -= (dx / dist) * force;
        b.vy -= (dy / dist) * force;
      }

      // 向心力
      for (const node of nodes) {
        node.vx += (W / 2 - node.x) * centerForce * cooling;
        node.vy += (H / 2 - node.y) * centerForce * cooling;
      }

      // 更新位置
      for (const node of nodes) {
        node.vx *= damping;
        node.vy *= damping;
        node.x += node.vx;
        node.y += node.vy;
        // 边界约束
        node.x = Math.max(NODE_RADIUS, Math.min(W - NODE_RADIUS, node.x));
        node.y = Math.max(NODE_RADIUS, Math.min(H - NODE_RADIUS, node.y));
      }
    }

    // 绘制
    ctx.clearRect(0, 0, W, H);

    // 绘制边
    for (const link of links) {
      const { source: s, target: t, label } = link;
      const dx = t.x - s.x;
      const dy = t.y - s.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;

      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = 'var(--color-border)';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 箭头
      const arrowSize = 6;
      const nx = dx / dist;
      const ny = dy / dist;
      const ax = t.x - nx * NODE_RADIUS;
      const ay = t.y - ny * NODE_RADIUS;
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - nx * arrowSize + ny * arrowSize * 0.5, ay - ny * arrowSize - nx * arrowSize * 0.5);
      ctx.lineTo(ax - nx * arrowSize - ny * arrowSize * 0.5, ay - ny * arrowSize + nx * arrowSize * 0.5);
      ctx.closePath();
      ctx.fillStyle = 'var(--color-border-bold)';
      ctx.fill();

      // 关系标签
      const mx = (s.x + t.x) / 2;
      const my = (s.y + t.y) / 2;
      ctx.font = '10px var(--font-body)';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      const labelW = ctx.measureText(label).width + 10;
      ctx.fillStyle = 'var(--color-bg-white)';
      ctx.fillRect(mx - labelW / 2, my - 12, labelW, 16);
      ctx.fillStyle = 'var(--color-text-muted)';
      ctx.fillText(label, mx, my - 2);
    }

    // 绘制节点
    for (const node of nodes) {
      const isHovered = hoveredNode?.id === node.id;
      const color = COLORS[node.type] || '#8C9096';
      const radius = isHovered ? NODE_RADIUS * 1.2 : NODE_RADIUS;

      // 阴影
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius + 2, 0, Math.PI * 2);
      ctx.fillStyle = isHovered ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.06)';
      ctx.fill();

      // 圆形
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = isHovered ? color : color + 'CC';
      ctx.fill();

      // 边框
      ctx.lineWidth = isHovered ? 2.5 : 1.5;
      ctx.strokeStyle = isHovered ? color : 'rgba(255,255,255,0.6)';
      ctx.stroke();

      // 文字（首字母）
      ctx.font = `bold ${radius * 0.7}px var(--font-body)`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#FFFFFF';
      ctx.fillText(node.name.charAt(0), node.x, node.y);

      // 节点名称标签
      ctx.font = '11px var(--font-body)';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isHovered ? 'var(--color-text-title)' : 'var(--color-text-muted)';
      ctx.fillText(node.name.length > 10 ? node.name.slice(0, 10) + '…' : node.name, node.x, node.y + radius + 6);

      // 悬浮时显示完整信息
      if (isHovered) {
        ctx.font = '10px var(--font-body)';
        ctx.fillStyle = 'var(--color-text-label)';
        ctx.fillText(node.type, node.x, node.y + radius + 20);
      }
    }
  }, [data, dimensions, hoveredNode]);

  // 鼠标交互
  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas || !data?.nodes?.length) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    let found = null;
    for (const node of data.nodes) {
      const nx = node.x || 0;
      const ny = node.y || 0;
      if (Math.sqrt((mx - nx) ** 2 + (my - ny) ** 2) <= NODE_RADIUS) {
        found = node;
        break;
      }
    }
    setHoveredNode(found);
  }, [data]);

  useEffect(() => { drawGraph(); }, [drawGraph]);

  return (
    <>
      {/* 遮罩 */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.3)',
          zIndex: 90,
          opacity: open ? 1 : 0,
          pointerEvents: open ? 'auto' : 'none',
          transition: 'opacity 0.3s ease',
        }}
      />

      {/* 抽屉 */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 'min(680px, 90vw)',
          background: 'var(--color-bg-white)',
          borderLeft: '1px solid var(--color-border-light)',
          zIndex: 100,
          display: 'flex',
          flexDirection: 'column',
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.3s cubic-bezier(0.4,0,0.2,1)',
        }}
        className="animate-slide-right"
      >
        {/* 抽屉标题 */}
        <div className="flex items-center justify-between px-6 py-4 border-b flex-shrink-0" style={{ borderColor: 'var(--color-border-light)' }}>
          <div>
            <h2 className="text-base font-semibold" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: 'var(--color-text-title)' }}>
              知识图谱
            </h2>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
              {doc?.name || ''} · {data ? `${data.nodes?.length || 0} 个实体，${data.edges?.length || 0} 个关系` : ''}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '6px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-text-muted)',
              borderRadius: '4px',
            }}
            className="hover:bg-[var(--color-bg-hover)]"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 图谱容器 */}
        <div
          ref={containerRef}
          className="flex-1 overflow-hidden"
          style={{ position: 'relative', minHeight: 0 }}
        >
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
              </div>
            </div>
          ) : data ? (
            <>
              <canvas
                ref={canvasRef}
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setHoveredNode(null)}
                style={{
                  width: '100%',
                  height: '100%',
                  cursor: hoveredNode ? 'pointer' : 'default',
                }}
              />
              {/* 图例 */}
              <div style={{
                position: 'absolute',
                bottom: 16,
                left: 16,
                padding: '10px 14px',
                background: 'var(--color-bg-white)',
                border: '1px solid var(--color-border-light)',
                borderRadius: '4px',
                fontSize: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}>
                <span style={{ color: 'var(--color-text-label)', fontWeight: 500, marginBottom: 2 }}>图例</span>
                {Object.entries(COLORS).map(([type, color]) => (
                  <div key={type} className="flex items-center gap-2">
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
                    <span style={{ color: 'var(--color-text-muted)' }}>{type}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>暂无图谱数据</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
