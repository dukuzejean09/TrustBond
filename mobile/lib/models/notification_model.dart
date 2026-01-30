import 'package:flutter/material.dart';

class NotificationModel {
  final String id;
  final String title;
  final String message;
  final NotificationType type;
  final DateTime createdAt;
  final bool isRead;
  final String? reportId;
  final String? alertType; // For police alerts: emergency, warning, info, security, etc.
  final bool isNationwide;
  final String? district;

  NotificationModel({
    required this.id,
    required this.title,
    required this.message,
    required this.type,
    required this.createdAt,
    this.isRead = false,
    this.reportId,
    this.alertType,
    this.isNationwide = false,
    this.district,
  });

  /// Create a notification from a backend alert
  factory NotificationModel.fromAlert(Map<String, dynamic> json) {
    NotificationType notifType;
    switch (json['alertType']) {
      case 'emergency':
        notifType = NotificationType.alert;
        break;
      case 'warning':
        notifType = NotificationType.alert;
        break;
      case 'security':
        notifType = NotificationType.alert;
        break;
      case 'info':
        notifType = NotificationType.announcement;
        break;
      case 'community':
        notifType = NotificationType.announcement;
        break;
      default:
        notifType = NotificationType.announcement;
    }

    return NotificationModel(
      id: 'ALERT_${json['id']}',
      title: json['title'] ?? 'Police Alert',
      message: json['message'] ?? '',
      type: notifType,
      createdAt: json['createdAt'] != null 
          ? DateTime.parse(json['createdAt'])
          : DateTime.now(),
      alertType: json['alertType'],
      isNationwide: json['isNationwide'] ?? false,
      district: json['district'],
    );
  }

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

  /// Get alert-specific icon based on alertType
  IconData get alertIcon {
    switch (alertType) {
      case 'emergency':
        return Icons.emergency;
      case 'warning':
        return Icons.warning_amber;
      case 'security':
        return Icons.security;
      case 'info':
        return Icons.info_outline;
      case 'weather':
        return Icons.cloud;
      case 'traffic':
        return Icons.traffic;
      case 'community':
        return Icons.people;
      default:
        return typeIcon;
    }
  }

  /// Get alert-specific color based on alertType
  Color get alertColor {
    switch (alertType) {
      case 'emergency':
        return const Color(0xFFD32F2F);
      case 'warning':
        return const Color(0xFFFF9800);
      case 'security':
        return const Color(0xFF9C27B0);
      case 'info':
        return const Color(0xFF2196F3);
      case 'weather':
        return const Color(0xFF00BCD4);
      case 'traffic':
        return const Color(0xFF607D8B);
      case 'community':
        return const Color(0xFF4CAF50);
      default:
        return typeColor;
    }
  }

  String get alertTypeLabel {
    switch (alertType) {
      case 'emergency':
        return '🚨 EMERGENCY';
      case 'warning':
        return '⚠️ WARNING';
      case 'security':
        return '🛡️ SECURITY';
      case 'info':
        return 'ℹ️ INFO';
      case 'weather':
        return '🌤️ WEATHER';
      case 'traffic':
        return '🚗 TRAFFIC';
      case 'community':
        return '👥 COMMUNITY';
      default:
        return 'ALERT';
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
