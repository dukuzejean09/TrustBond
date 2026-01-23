import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../models/notification_model.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<NotificationModel> _notifications = [];

  @override
  void initState() {
    super.initState();
    _notifications = MockNotifications.getNotifications();
  }

  void _markAllAsRead() {
    setState(() {
      _notifications = _notifications.map((n) {
        return NotificationModel(
          id: n.id,
          title: n.title,
          message: n.message,
          type: n.type,
          createdAt: n.createdAt,
          isRead: true,
          reportId: n.reportId,
        );
      }).toList();
    });
  }

  int get _unreadCount {
    return _notifications.where((n) => !n.isRead).length;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          if (_unreadCount > 0)
            TextButton(
              onPressed: _markAllAsRead,
              child: const Text(
                'Mark all read',
                style: TextStyle(color: Colors.white),
              ),
            ),
        ],
      ),
      body: _notifications.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.notifications_none,
                    size: 80,
                    color: AppTheme.textSecondary.withOpacity(0.5),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No notifications',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'You\'re all caught up!',
                    style: TextStyle(color: AppTheme.textLight),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _notifications.length,
              itemBuilder: (context, index) {
                final notification = _notifications[index];
                return _NotificationCard(
                  notification: notification,
                  onTap: () {
                    // Mark as read
                    setState(() {
                      _notifications[index] = NotificationModel(
                        id: notification.id,
                        title: notification.title,
                        message: notification.message,
                        type: notification.type,
                        createdAt: notification.createdAt,
                        isRead: true,
                        reportId: notification.reportId,
                      );
                    });

                    // Show notification details
                    _showNotificationDetails(notification);
                  },
                  onDismiss: () {
                    setState(() {
                      _notifications.removeAt(index);
                    });
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: const Text('Notification dismissed'),
                        action: SnackBarAction(
                          label: 'Undo',
                          onPressed: () {
                            setState(() {
                              _notifications.insert(index, notification);
                            });
                          },
                        ),
                      ),
                    );
                  },
                );
              },
            ),
    );
  }

  void _showNotificationDetails(NotificationModel notification) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppTheme.dividerColor,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Type icon
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: notification.typeColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  notification.typeIcon,
                  color: notification.typeColor,
                  size: 28,
                ),
              ),
              const SizedBox(height: 16),

              // Title
              Text(
                notification.title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),

              // Time
              Text(
                notification.timeAgo,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 16),

              // Message
              Text(
                notification.message,
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 20),

              // Action button
              if (notification.reportId != null)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      // Navigate to report details
                    },
                    child: const Text('View Report'),
                  ),
                ),
              const SizedBox(height: 12),
            ],
          ),
        );
      },
    );
  }
}

class _NotificationCard extends StatelessWidget {
  final NotificationModel notification;
  final VoidCallback onTap;
  final VoidCallback onDismiss;

  const _NotificationCard({
    required this.notification,
    required this.onTap,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: Key(notification.id),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => onDismiss(),
      background: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: AppTheme.errorColor,
          borderRadius: BorderRadius.circular(16),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        child: const Icon(Icons.delete, color: Colors.white),
      ),
      child: Card(
        margin: const EdgeInsets.only(bottom: 12),
        color: notification.isRead ? null : notification.typeColor.withOpacity(0.05),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Icon
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: notification.typeColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    notification.typeIcon,
                    color: notification.typeColor,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                // Content
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              notification.title,
                              style: TextStyle(
                                fontWeight: notification.isRead
                                    ? FontWeight.normal
                                    : FontWeight.w600,
                                fontSize: 15,
                              ),
                            ),
                          ),
                          if (!notification.isRead)
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: notification.typeColor,
                                shape: BoxShape.circle,
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        notification.message,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: notification.isRead
                              ? AppTheme.textLight
                              : AppTheme.textSecondary,
                          fontSize: 13,
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        notification.timeAgo,
                        style: const TextStyle(
                          color: AppTheme.textLight,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
