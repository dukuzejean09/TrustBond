import 'package:flutter/material.dart';

class AlertModel {
  final String id;
  final String title;
  final String description;
  final AlertType type;
  final double latitude;
  final double longitude;
  final String address;
  final DateTime createdAt;
  final double distance;
  final bool isRead;

  AlertModel({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.latitude,
    required this.longitude,
    required this.address,
    required this.createdAt,
    required this.distance,
    this.isRead = false,
  });

  String get typeLabel {
    switch (type) {
      case AlertType.incident:
        return 'Incident';
      case AlertType.safety:
        return 'Safety Notice';
      case AlertType.police:
        return 'Police Announcement';
      case AlertType.warning:
        return 'Warning';
    }
  }

  Color get typeColor {
    switch (type) {
      case AlertType.incident:
        return const Color(0xFFE53935);
      case AlertType.safety:
        return const Color(0xFF2196F3);
      case AlertType.police:
        return const Color(0xFF1E3A5F);
      case AlertType.warning:
        return const Color(0xFFFF9800);
    }
  }

  IconData get typeIcon {
    switch (type) {
      case AlertType.incident:
        return Icons.report_problem;
      case AlertType.safety:
        return Icons.shield;
      case AlertType.police:
        return Icons.local_police;
      case AlertType.warning:
        return Icons.warning_amber;
    }
  }

  String get formattedDistance {
    if (distance < 1) {
      return '${(distance * 1000).toInt()}m away';
    }
    return '${distance.toStringAsFixed(1)}km away';
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

enum AlertType {
  incident,
  safety,
  police,
  warning,
}

// Mock alerts data
class MockAlerts {
  static List<AlertModel> getAlerts() {
    return [
      AlertModel(
        id: 'ALT001',
        title: 'Theft reported nearby',
        description: 'A theft incident was reported in Kimironko area. Please be vigilant and secure your belongings.',
        type: AlertType.incident,
        latitude: -1.9380,
        longitude: 29.8700,
        address: 'Kimironko, Kigali',
        createdAt: DateTime.now().subtract(const Duration(hours: 2)),
        distance: 0.8,
      ),
      AlertModel(
        id: 'ALT002',
        title: 'Road safety reminder',
        description: 'Please follow traffic rules and be careful when crossing streets. Several accidents reported this week.',
        type: AlertType.safety,
        latitude: -1.9456,
        longitude: 29.8790,
        address: 'Nyabugogo, Kigali',
        createdAt: DateTime.now().subtract(const Duration(hours: 5)),
        distance: 2.3,
      ),
      AlertModel(
        id: 'ALT003',
        title: 'Increased patrols in city center',
        description: 'Rwanda National Police has increased patrols in the city center area for improved security.',
        type: AlertType.police,
        latitude: -1.9403,
        longitude: 29.8739,
        address: 'City Center, Kigali',
        createdAt: DateTime.now().subtract(const Duration(days: 1)),
        distance: 1.5,
      ),
      AlertModel(
        id: 'ALT004',
        title: 'Mobile money scam warning',
        description: 'Be aware of fraudulent calls claiming to be from mobile money services. Never share your PIN.',
        type: AlertType.warning,
        latitude: -1.9500,
        longitude: 29.8800,
        address: 'Kigali',
        createdAt: DateTime.now().subtract(const Duration(days: 2)),
        distance: 3.0,
      ),
      AlertModel(
        id: 'ALT005',
        title: 'Street light outage',
        description: 'Multiple street lights are not working on KN 5 Rd. Use caution when walking at night.',
        type: AlertType.safety,
        latitude: -1.9420,
        longitude: 29.8750,
        address: 'KN 5 Rd, Kigali',
        createdAt: DateTime.now().subtract(const Duration(days: 3)),
        distance: 0.5,
      ),
    ];
  }
}
