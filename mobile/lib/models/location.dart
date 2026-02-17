/// Location model returned from backend `/locations`.
class Location {
  final int locationId;
  final String locationType;
  final String locationName;
  final int? parentLocationId;
  final double? centroidLat;
  final double? centroidLong;
  final bool isActive;

  const Location({
    required this.locationId,
    required this.locationType,
    required this.locationName,
    this.parentLocationId,
    this.centroidLat,
    this.centroidLong,
    required this.isActive,
  });

  factory Location.fromJson(Map<String, dynamic> json) {
    return Location(
      locationId: json['location_id'] as int,
      locationType: json['location_type'] as String,
      locationName: json['location_name'] as String,
      parentLocationId: json['parent_location_id'] as int?,
      centroidLat: (json['centroid_lat'] as num?)?.toDouble(),
      centroidLong: (json['centroid_long'] as num?)?.toDouble(),
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  @override
  String toString() => locationName;
}
