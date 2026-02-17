/// Mirrors the backend `reports` table (submission payload).
class Report {
  final String? reportId;
  final String deviceHash;
  final String incidentTypeId;
  final String description;
  final double latitude;
  final double longitude;
  final double? gpsAccuracy;
  final String? motionLevel;    // low | medium | high
  final double? movementSpeed;
  final bool? wasStationary;
  final String? villageLocationId;
  final DateTime? reportedAt;
  final String? ruleStatus;
  final bool? isFlagged;

  const Report({
    this.reportId,
    required this.deviceHash,
    required this.incidentTypeId,
    required this.description,
    required this.latitude,
    required this.longitude,
    this.gpsAccuracy,
    this.motionLevel,
    this.movementSpeed,
    this.wasStationary,
    this.villageLocationId,
    this.reportedAt,
    this.ruleStatus,
    this.isFlagged,
  });

  factory Report.fromJson(Map<String, dynamic> json) {
    return Report(
      reportId: json['report_id'] as String?,
      deviceHash: json['device_hash'] as String? ?? '',
      incidentTypeId: json['incident_type_id'] as String,
      description: json['description'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      gpsAccuracy: (json['gps_accuracy'] as num?)?.toDouble(),
      motionLevel: json['motion_level'] as String?,
      movementSpeed: (json['movement_speed'] as num?)?.toDouble(),
      wasStationary: json['was_stationary'] as bool?,
      villageLocationId: json['village_location_id'] as String?,
      reportedAt: json['reported_at'] != null
          ? DateTime.tryParse(json['reported_at'] as String)
          : null,
      ruleStatus: json['rule_status'] as String?,
      isFlagged: json['is_flagged'] as bool?,
    );
  }

  /// Payload sent to POST /api/v1/reports
  Map<String, dynamic> toSubmitJson() => {
        'device_hash': deviceHash,
        'incident_type_id': incidentTypeId,
        'description': description,
        'latitude': latitude,
        'longitude': longitude,
        if (gpsAccuracy != null) 'gps_accuracy': gpsAccuracy,
        if (motionLevel != null) 'motion_level': motionLevel,
        if (movementSpeed != null) 'movement_speed': movementSpeed,
        if (wasStationary != null) 'was_stationary': wasStationary,
        if (villageLocationId != null) 'village_location_id': villageLocationId,
      };
}
