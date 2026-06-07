/**
 * Signal - 实时通知组件
 * 显示 WebSocket 推送的通知
 */

import { useEffect, useState, useCallback } from 'react';
import { wsClient, MessageType } from '../lib/websocket';
import { X, Bookmark, History, Bell, CheckCircle } from 'lucide-react';

// 通知类型配置
const NOTIFICATION_CONFIG = {
  [MessageType.BOOKMARK_ADDED]: {
    icon: Bookmark,
    title: '收藏成功',
    color: 'text-green-500',
    bgColor: 'bg-green-50',
  },
  [MessageType.BOOKMARK_REMOVED]: {
    icon: Bookmark,
    title: '已取消收藏',
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
  },
  [MessageType.HISTORY_UPDATED]: {
    icon: History,
    title: '阅读记录已更新',
    color: 'text-blue-500',
    bgColor: 'bg-blue-50',
  },
  [MessageType.TASK_COMPLETED]: {
    icon: CheckCircle,
    title: '任务完成',
    color: 'text-green-500',
    bgColor: 'bg-green-50',
  },
  [MessageType.ANNOUNCEMENT]: {
    icon: Bell,
    title: '系统公告',
    color: 'text-orange-500',
    bgColor: 'bg-orange-50',
  },
};

/**
 * 单条通知组件
 */
function NotificationItem({ notification, onClose }) {
  const { type, data, timestamp } = notification;
  const config = NOTIFICATION_CONFIG[type] || {
    icon: Bell,
    title: '通知',
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
  };

  const Icon = config.icon;

  return (
    <div
      className={`
        flex items-start gap-3 p-4 rounded-lg shadow-lg border
        ${config.bgColor} animate-slide-in
      `}
    >
      <Icon className={`w-5 h-5 mt-0.5 ${config.color}`} />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900">{config.title}</p>
        {data?.message && (
          <p className="text-sm text-gray-600 mt-1">{data.message}</p>
        )}
        <p className="text-xs text-gray-400 mt-1">
          {new Date(timestamp).toLocaleTimeString()}
        </p>
      </div>
      <button
        onClick={() => onClose(notification.id)}
        className="text-gray-400 hover:text-gray-600"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

/**
 * 通知容器组件
 */
export function NotificationContainer() {
  const [notifications, setNotifications] = useState([]);

  // 添加通知
  const addNotification = useCallback((notification) => {
    const id = Date.now() + Math.random();
    setNotifications(prev => [...prev, { ...notification, id }]);

    // 5秒后自动消失
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  }, []);

  // 移除通知
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // 监听 WebSocket 消息
  useEffect(() => {
    const handleMessage = (message) => {
      addNotification(message);
    };

    // 监听所有消息类型
    Object.values(MessageType).forEach(type => {
      wsClient.on(type, handleMessage);
    });

    return () => {
      Object.values(MessageType).forEach(type => {
        wsClient.off(type, handleMessage);
      });
    };
  }, [addNotification]);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {notifications.map(notification => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={removeNotification}
        />
      ))}
    </div>
  );
}

export default NotificationContainer;
