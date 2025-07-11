/**
 * Error Boundary - 错误边界组件
 * 捕获和处理React组件错误，特别是ResizeObserver相关的错误
 */
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // 检查是否是ResizeObserver错误
    if (error.message && error.message.includes('ResizeObserver')) {
      // 对于ResizeObserver错误，不显示错误状态，直接忽略
      return { hasError: false };
    }
    
    // 对于其他错误，显示错误状态
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // 只记录非ResizeObserver错误
    if (!error.message || !error.message.includes('ResizeObserver')) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '20px',
          background: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          margin: '10px'
        }}>
          <h2>⚠️ 组件渲染错误</h2>
          <p>抱歉，这个组件遇到了一个错误。请刷新页面重试。</p>
          <details style={{ marginTop: '10px' }}>
            <summary>错误详情</summary>
            <pre style={{ 
              background: '#f5f5f5', 
              padding: '10px', 
              borderRadius: '4px',
              fontSize: '12px',
              overflow: 'auto'
            }}>
              {this.state.error && this.state.error.toString()}
            </pre>
          </details>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              marginTop: '10px',
              padding: '8px 16px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            重试
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;