import { Component } from 'react';

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center p-8 min-h-[120px]">
          <div className="text-center">
            <div style={{ width: '32px', height: '32px', margin: '0 auto 8px', opacity: 0.4 }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--color-text-label)', marginBottom: '6px' }}>该区域加载失败</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              style={{ fontSize: '11px', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            >
              重试
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
