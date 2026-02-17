/// Mirrors the backend `incident_types` table.
class IncidentType {
  final String incidentTypeId;
  final String typeName;
  final double severityWeight;
  final bool isActive;

  const IncidentType({
    required this.incidentTypeId,
    required this.typeName,
    required this.severityWeight,
    required this.isActive,
  });

  factory IncidentType.fromJson(Map<String, dynamic> json) {
    return IncidentType(
      incidentTypeId: json['incident_type_id'] as String,
      typeName: json['type_name'] as String,
      severityWeight: (json['severity_weight'] as num).toDouble(),
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
        'incident_type_id': incidentTypeId,
        'type_name': typeName,
        'severity_weight': severityWeight,
        'is_active': isActive,
      };

  @override
  String toString() => typeName;
}
