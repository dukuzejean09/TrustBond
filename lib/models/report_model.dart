import 'package:flutter/material.dart';
import 'incident_type.dart';
import 'evidence_model.dart';

enum ReportStatus {
  draft,
  submitted,
  underReview,
  verified,
  closed,
}

class ReportModel {
  final String id;
  final IncidentType incidentType;
  final String description;
  final bool isAnonymous;
  final double latitude;
  final double longitude;
  final String address;
  final DateTime incidentDate;
  final TimeOfDay incidentTime;
  final List<EvidenceModel> evidenceList;
  final ReportStatus status;
  final DateTime submittedAt;
  final DateTime? updatedAt;
  final String? responseMessage;

  ReportModel({
    required this.id,
    required this.incidentType,
    required this.description,
    required this.isAnonymous,
    required this.latitude,
    required this.longitude,
    required this.address,
    required this.incidentDate,
    required this.incidentTime,
    required this.evidenceList,
    required this.status,
    required this.submittedAt,
    this.updatedAt,
    this.responseMessage,
  });

  String get statusLabel {
    switch (status) {
      case ReportStatus.draft:
        return 'Draft';
      case ReportStatus.submitted:
        return 'Submitted';
      case ReportStatus.underReview:
        return 'Under Review';
      case ReportStatus.verified:
        return 'Verified';
      case ReportStatus.closed:
        return 'Closed';
    }
  }

  Color get statusColor {
    switch (status) {
      case ReportStatus.draft:
        return Colors.grey;
      case ReportStatus.submitted:
        return const Color(0xFF2196F3);
      case ReportStatus.underReview:
        return const Color(0xFFFF9800);
      case ReportStatus.verified:
        return const Color(0xFF4CAF50);
      case ReportStatus.closed:
        return const Color(0xFF9E9E9E);
    }
  }

  IconData get statusIcon {
    switch (status) {
      case ReportStatus.draft:
        return Icons.edit_note;
      case ReportStatus.submitted:
        return Icons.send;
      case ReportStatus.underReview:
        return Icons.pending;
      case ReportStatus.verified:
        return Icons.verified;
      case ReportStatus.closed:
        return Icons.check_circle;
    }
  }

  String get formattedDate {
    return '${incidentDate.day}/${incidentDate.month}/${incidentDate.year}';
  }

  String get formattedTime {
    final hour = incidentTime.hour.toString().padLeft(2, '0');
    final minute = incidentTime.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'incidentTypeId': incidentType.id,
      'description': description,
      'isAnonymous': isAnonymous,
      'latitude': latitude,
      'longitude': longitude,
      'address': address,
      'incidentDate': incidentDate.toIso8601String(),
      'incidentTime': '${incidentTime.hour}:${incidentTime.minute}',
      'evidenceList': evidenceList.map((e) => e.toJson()).toList(),
      'status': status.name,
      'submittedAt': submittedAt.toIso8601String(),
      'updatedAt': updatedAt?.toIso8601String(),
      'responseMessage': responseMessage,
    };
  }

  ReportModel copyWith({
    String? id,
    IncidentType? incidentType,
    String? description,
    bool? isAnonymous,
    double? latitude,
    double? longitude,
    String? address,
    DateTime? incidentDate,
    TimeOfDay? incidentTime,
    List<EvidenceModel>? evidenceList,
    ReportStatus? status,
    DateTime? submittedAt,
    DateTime? updatedAt,
    String? responseMessage,
  }) {
    return ReportModel(
      id: id ?? this.id,
      incidentType: incidentType ?? this.incidentType,
      description: description ?? this.description,
      isAnonymous: isAnonymous ?? this.isAnonymous,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      address: address ?? this.address,
      incidentDate: incidentDate ?? this.incidentDate,
      incidentTime: incidentTime ?? this.incidentTime,
      evidenceList: evidenceList ?? this.evidenceList,
      status: status ?? this.status,
      submittedAt: submittedAt ?? this.submittedAt,
      updatedAt: updatedAt ?? this.updatedAt,
      responseMessage: responseMessage ?? this.responseMessage,
    );
  }
}
