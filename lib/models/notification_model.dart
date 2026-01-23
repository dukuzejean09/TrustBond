import 'package:flutter/material.dart';

class NotificationModel {
  final String id;
  final String title;
  final String message;
  final NotificationType type;
  final DateTime createdAt;
  final bool isRead;
  final String? reportId;

  NotificationModel({
    required this.id,
    required this.title,
    required this.message,
    required this.type,
    required this.createdAt,
    this.isRead = false,
    this.reportId,
  });

  Color get typeColor {
    switch (type) {
      case NotificationType.statusUpdate:
        return const Color(0xFF2196F3);
      case NotificationType.alert:
        return const Color(0xFFE53935);
      case NotificationType.announcement:
        return const Color(0xFF1E3A5F);
      case NotificationType.reminder:
        return const Color(0xFFFF9800);
    }
  }

  IconData get typeIcon {
    switch (type) {
      case NotificationType.statusUpdate:
        return Icons.update;
      case NotificationType.alert:
        return Icons.notification_important;
      case NotificationType.announcement:
        return Icons.campaign;
      case NotificationType.reminder:
        return Icons.alarm;
    }
  }

  String get timeAgo {
    final now = DateTime.now();
    final difference = now.difference(createdAt);

    if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return '${createdAt.day}/${createdAt.month}/${createdAt.year}';
    }
  }
}

enum NotificationType {
  statusUpdate,
  alert,
  announcement,
  reminder,
}

// Mock notifications data
class MockNotifications {
  static List<NotificationModel> getNotifications() {
    return [
      NotificationModel(
        id: 'NOT001',
        title: 'Report Status Updated',
        message: 'Your report #RPT001 is now under review by the authorities.',
        type: NotificationType.statusUpdate,
        createdAt: DateTime.now().subtract(const Duration(hours: 1)),
        reportId: 'RPT001',
      ),
      NotificationModel(
        id: 'NOT002',
        title: 'Safety Alert',
        message: 'A theft incident was reported in your area. Stay vigilant.',
        type: NotificationType.alert,
        createdAt: DateTime.now().subtract(const Duration(hours: 3)),
      ),
      NotificationModel(
        id: 'NOT003',
        title: 'Report Verified',
        message: 'Your report #RPT002 has been verified. Thank you for your contribution.',
        type: NotificationType.statusUpdate,
        createdAt: DateTime.now().subtract(const Duration(days: 1)),
        reportId: 'RPT002',
        isRead: true,
      ),
      NotificationModel(
        id: 'NOT004',
        title: 'Community Update',
        message: 'New safety measures implemented in Kigali city center.',
        type: NotificationType.announcement,
        createdAt: DateTime.now().subtract(const Duration(days: 2)),
        isRead: true,
      ),
      NotificationModel(
        id: 'NOT005',
        title: 'Offline Report Reminder',
        message: 'You have 1 saved report. Submit when connected to the internet.',
        type: NotificationType.reminder,
        createdAt: DateTime.now().subtract(const Duration(days: 3)),
        isRead: true,
      ),
    ];
  }
}
