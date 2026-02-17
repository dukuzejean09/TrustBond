/// Mirrors the backend `devices` table.
class DeviceInfo {
  final String? deviceId;
  final String deviceHash;
  final int totalReports;
  final int trustedReports;
  final int flaggedReports;
  final double deviceTrustScore;
  final DateTime? firstSeenAt;

  const DeviceInfo({
    this.deviceId,
    required this.deviceHash,
    this.totalReports = 0,
    this.trustedReports = 0,
    this.flaggedReports = 0,
    this.deviceTrustScore = 50.0,
    this.firstSeenAt,
  });

  factory DeviceInfo.fromJson(Map<String, dynamic> json) {
    return DeviceInfo(
      deviceId: json['device_id'] as String?,
      deviceHash: json['device_hash'] as String,
      totalReports: json['total_reports'] as int? ?? 0,
      trustedReports: json['trusted_reports'] as int? ?? 0,
      flaggedReports: json['flagged_reports'] as int? ?? 0,
      deviceTrustScore:
          (json['device_trust_score'] as num?)?.toDouble() ?? 50.0,
      firstSeenAt: json['first_seen_at'] != null
          ? DateTime.tryParse(json['first_seen_at'] as String)
          : null,
    );
  }
}
