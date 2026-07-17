/**
 * Signal - WebSocket 客户端
 * 通过 WebSocket subprotocol (Sec-WebSocket-Protocol) 传递 JWT token，
 * 避免 token 出现在 URL query string 中被日志记录。
 */

class WebSocketClient {
  constructor() {
    this.ws = null;
    this.url = '';
    this.token = '';
    this.reconnectCount = 0;
    this.maxRetries = 5;
    this.baseDelay = 1000;
    this.listeners = new Map();
    this.isConnecting = false;
  }

  /**
   * 连接 WebSocket
   * @param {string} url - WebSocket URL (不含 token)
   * @param {string} token - JWT token
   */
  connect(url, token) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WS] 已连接');
      return;
    }

    this.url = url;
    this.token = token;
    this.isConnecting = true;

    try {
      // 通过 WebSocket subprotocol 传递 token，避免出现在 URL 中
      this.ws = new WebSocket(url, [token]);

      this.ws.onopen = () => {
        console.log('[WS] 连接成功');
        this.reconnectCount = 0;
        this.isConnecting = false;
        this.emit('connected', {});
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (e) {
          console.error('[WS] 消息解析失败:', e);
        }
      };

      this.ws.onclose = (event) => {
        this.isConnecting = false;
        console.log(`[WS] 连接关闭 (code: ${event.code})`);

        // 非正常关闭 && 未超最大重试次数 → 自动重连
        if (event.code !== 1000 && this.reconnectCount < this.maxRetries) {
          this.scheduleReconnect();
        }
        this.emit('disconnected', { code: event.code });
      };

      this.ws.onerror = (error) => {
        console.error('[WS] 连接错误:', error);
        this.isConnecting = false;
        this.emit('error', { error });
      };
    } catch (error) {
      console.error('[WS] 创建连接失败:', error);
      this.isConnecting = false;
      this.emit('error', { error });
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, '用户主动断开');
      this.ws = null;
    }
    this.reconnectCount = this.maxRetries; // 阻止自动重连
    console.log('[WS] 已断开');
  }

  scheduleReconnect() {
    const delay = this.baseDelay * Math.pow(2, this.reconnectCount);
    console.log(`[WS] ${delay}ms 后重连 (第 ${this.reconnectCount + 1} 次)`);
    this.reconnectCount++;

    setTimeout(() => {
      if (this.token) {
        this.connect(this.url, this.token);
      }
    }, delay);
  }

  handleMessage(message) {
    const { type, ...data } = message;

    switch (type) {
      case 'connected':
        console.log('[WS] 连接确认:', data.message);
        break;
      case 'ping':
        this.send({ type: 'pong' });
        break;
      case 'pong':
        break;
      default:
        this.emit(type, data);
    }
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      this.listeners.set(event, callbacks.filter(cb => cb !== callback));
    }
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(cb => cb(data));
    }
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
export const MessageType = {
  BOOKMARK_ADDED: 'bookmark_added',
  BOOKMARK_REMOVED: 'bookmark_removed',
  HISTORY_UPDATED: 'history_updated',
  COMMENT_ADDED: 'comment_added',
};
