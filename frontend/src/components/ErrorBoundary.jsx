import { Component } from 'react';

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null, retryCount: 0 };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // 上报错误到控制台（生产环境可接入 Sentry 等日志服务）
    console.error('[ErrorBoundary]', error, errorInfo);
    if (typeof this.props.onError === 'function') {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    const { retryCount } = this.state;
    if (retryCount >= 3) {
      console.warn('[ErrorBoundary] 重试次数超过限制，不再重试');
      return;
    }
    this.setState({ hasError: false, error: null, retryCount: retryCount + 1 });
  };

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
            {this.state.retryCount < 3 && (
              <button
                onClick={this.handleRetry}
                style={{ fontSize: '11px', color: 'var(--color-brass)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                重试
              </button>
            )}
            {this.state.retryCount >= 3 && (
              <p style={{ fontSize: '10px', color: 'var(--color-text-label)', marginTop: '4px' }}>请刷新页面后重试</p>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
