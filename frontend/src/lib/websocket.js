/**
 * Signal - WebSocket 客户端
 * 实时推送通知
 */

const WS_RECONNECT_DELAY = 5000; // 重连延迟
const WS_MAX_RECONNECT = 3; // 最大重连次数

class WebSocketClient {
  constructor() {
    this.ws = null;
    this.url = null;
    this.token = null;
    this.reconnectCount = 0;
    this.listeners = new Map();
    this.isConnecting = false;
  }

  /**
   * 连接 WebSocket
   * @param {string} url - WebSocket URL
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
      const wsUrl = `${url}?token=${token}`;
      this.ws = new WebSocket(wsUrl);

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
        console.log('[WS] 连接关闭:', event.code, event.reason);
        this.isConnecting = false;
        this.emit('disconnected', { code: event.code, reason: event.reason });

        // 非正常关闭且未超过重连次数，尝试重连
        if (event.code !== 1000 && this.reconnectCount < WS_MAX_RECONNECT) {
          this.reconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] 错误:', error);
        this.isConnecting = false;
        this.emit('error', error);
      };

    } catch (error) {
      console.error('[WS] 连接失败:', error);
      this.isConnecting = false;
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'User disconnect');
      this.ws = null;
    }
  }

  /**
   * 重连
   */
  reconnect() {
    if (this.isConnecting) return;

    this.reconnectCount++;
    console.log(`[WS] 尝试重连 (${this.reconnectCount}/${WS_MAX_RECONNECT})...`);

    setTimeout(() => {
      if (this.url && this.token) {
        this.connect(this.url, this.token);
      }
    }, WS_RECONNECT_DELAY);
  }

  /**
   * 处理消息
   */
  handleMessage(message) {
    const { type, data, timestamp } = message;

    // 心跳响应
    if (type === 'ping') {
      this.send({ type: 'pong' });
      return;
    }

    if (type === 'pong') {
      return;
    }

    // 触发对应类型的监听器
    this.emit(type, data || message);

    // 触发通用消息监听
    this.emit('message', message);
  }

  /**
   * 发送消息
   */
  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * 添加事件监听
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * 移除事件监听
   */
  off(event, callback) {
    if (!this.listeners.has(event)) return;
    
    if (callback) {
      const callbacks = this.listeners.get(event).filter(cb => cb !== callback);
      this.listeners.set(event, callbacks);
    } else {
      this.listeners.delete(event);
    }
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (!this.listeners.has(event)) return;
    this.listeners.get(event).forEach(callback => {
      try {
        callback(data);
      } catch (e) {
        console.error(`[WS] 监听器错误 (${event}):`, e);
      }
    });
  }

  /**
   * 获取连接状态
   */
  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// 单例
export const wsClient = new WebSocketClient();

// 消息类型常量
export const MessageType = {
  BOOKMARK_ADDED: 'bookmark_added',
  BOOKMARK_REMOVED: 'bookmark_removed',
  HISTORY_UPDATED: 'history_updated',
  TASK_COMPLETED: 'task_completed',
  ANNOUNCEMENT: 'announcement',
};

export default wsClient;
