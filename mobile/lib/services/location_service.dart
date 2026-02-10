import 'dart:async';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

/// Service for handling GPS location operations.
/// 
/// This service provides:
/// - Real GPS location detection
/// - Address reverse geocoding
/// - Location permission handling
/// - Musanze/Rwanda boundary validation
class LocationService {
  // Rwanda bounds for validation
  static const double rwandaMinLat = -2.85;
  static const double rwandaMaxLat = -1.05;
  static const double rwandaMinLng = 28.85;
  static const double rwandaMaxLng = 30.90;
  
  // Musanze district approximate bounds
  static const double musanzeMinLat = -1.60;
  static const double musanzeMaxLat = -1.40;
  static const double musanzeMinLng = 29.40;
  static const double musanzeMaxLng = 29.70;
  
  // Musanze district center (for fallback)
  static const double musanzeCenterLat = -1.4999;
  static const double musanzeCenterLng = 29.6349;
  
  /// Check if location services are enabled and permissions granted.
  Future<LocationPermissionStatus> checkPermissions() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return LocationPermissionStatus.serviceDisabled;
    }
    
    LocationPermission permission = await Geolocator.checkPermission();
    
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return LocationPermissionStatus.denied;
      }
    }
    
    if (permission == LocationPermission.deniedForever) {
      return LocationPermissionStatus.deniedForever;
    }
    
    return LocationPermissionStatus.granted;
  }
  
  /// Request location permission from user.
  Future<bool> requestPermission() async {
    LocationPermission permission = await Geolocator.requestPermission();
    return permission == LocationPermission.always || 
           permission == LocationPermission.whileInUse;
  }
  
  /// Get the current GPS position.
  /// 
  /// Returns the device's current location with high accuracy.
  /// Throws an exception if location services are unavailable.
  Future<Position> getCurrentPosition({
    Duration timeout = const Duration(seconds: 15),
  }) async {
    final status = await checkPermissions();
    
    if (status != LocationPermissionStatus.granted) {
      throw LocationException(
        'Location permission not granted',
        status: status,
      );
    }
    
    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: timeout,
      );
      
      return position;
    } on TimeoutException {
      throw LocationException('Location request timed out');
    } catch (e) {
      throw LocationException('Failed to get location: $e');
    }
  }
  
  /// Get the last known position (faster but may be outdated).
  Future<Position?> getLastKnownPosition() async {
    return await Geolocator.getLastKnownPosition();
  }
  
  /// Convert coordinates to a human-readable address.
  Future<String> getAddressFromCoordinates(
    double latitude,
    double longitude,
  ) async {
    try {
      List<Placemark> placemarks = await placemarkFromCoordinates(
        latitude,
        longitude,
      );
      
      if (placemarks.isEmpty) {
        return _generateGenericAddress(latitude, longitude);
      }
      
      Placemark place = placemarks.first;
      
      // Build address string
      List<String> parts = [];
      
      if (place.street != null && place.street!.isNotEmpty) {
        parts.add(place.street!);
      }
      if (place.subLocality != null && place.subLocality!.isNotEmpty) {
        parts.add(place.subLocality!);
      }
      if (place.locality != null && place.locality!.isNotEmpty) {
        parts.add(place.locality!);
      }
      if (place.administrativeArea != null && place.administrativeArea!.isNotEmpty) {
        parts.add(place.administrativeArea!);
      }
      
      if (parts.isEmpty) {
        return _generateGenericAddress(latitude, longitude);
      }
      
      return parts.join(', ');
    } catch (e) {
      return _generateGenericAddress(latitude, longitude);
    }
  }
  
  /// Generate a generic address based on coordinates.
  String _generateGenericAddress(double lat, double lng) {
    if (isInMusanze(lat, lng)) {
      return 'Musanze District, Northern Province';
    } else if (isInRwanda(lat, lng)) {
      return 'Rwanda';
    } else {
      return '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
    }
  }
  
  /// Check if coordinates are within Rwanda.
  bool isInRwanda(double latitude, double longitude) {
    return latitude >= rwandaMinLat &&
           latitude <= rwandaMaxLat &&
           longitude >= rwandaMinLng &&
           longitude <= rwandaMaxLng;
  }
  
  /// Check if coordinates are within Musanze district.
  bool isInMusanze(double latitude, double longitude) {
    return latitude >= musanzeMinLat &&
           latitude <= musanzeMaxLat &&
           longitude >= musanzeMinLng &&
           longitude <= musanzeMaxLng;
  }
  
  /// Get the district name based on coordinates.
  /// 
  /// Returns the Rwanda district name for the given coordinates.
  /// For now, focuses on Musanze as the primary target area.
  String getDistrictFromCoordinates(double latitude, double longitude) {
    if (isInMusanze(latitude, longitude)) {
      return 'Musanze';
    }
    
    // Approximate district detection for other areas
    // This is simplified - a full implementation would use GeoJSON boundaries
    if (latitude > -1.5 && longitude < 29.5) {
      return 'Rubavu';
    } else if (latitude < -1.8 && longitude > 29.5) {
      return 'Kigali';
    } else if (latitude > -1.4 && longitude > 29.5) {
      return 'Burera';
    }
    
    return 'Unknown District';
  }
  
  /// Calculate distance between two points in kilometers.
  double calculateDistance(
    double startLat,
    double startLng,
    double endLat,
    double endLng,
  ) {
    return Geolocator.distanceBetween(
      startLat,
      startLng,
      endLat,
      endLng,
    ) / 1000; // Convert to km
  }
  
  /// Stream location updates.
  /// 
  /// Returns a stream of position updates for real-time tracking.
  Stream<Position> getPositionStream({
    int distanceFilter = 10, // meters
  }) {
    return Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: distanceFilter,
      ),
    );
  }
  
  /// Open location settings.
  Future<bool> openLocationSettings() async {
    return await Geolocator.openLocationSettings();
  }
  
  /// Open app settings for permissions.
  Future<bool> openAppSettings() async {
    return await Geolocator.openAppSettings();
  }
}

/// Status of location permission.
enum LocationPermissionStatus {
  granted,
  denied,
  deniedForever,
  serviceDisabled,
}

/// Custom exception for location errors.
class LocationException implements Exception {
  final String message;
  final LocationPermissionStatus? status;
  
  LocationException(this.message, {this.status});
  
  @override
  String toString() => 'LocationException: $message';
}

/// Location data model for reports.
class LocationData {
  final double latitude;
  final double longitude;
  final String address;
  final String district;
  final double? accuracy;
  final DateTime timestamp;
  final bool isValid;
  final String? validationMessage;
  
  LocationData({
    required this.latitude,
    required this.longitude,
    required this.address,
    required this.district,
    this.accuracy,
    DateTime? timestamp,
    this.isValid = true,
    this.validationMessage,
  }) : timestamp = timestamp ?? DateTime.now();
  
  Map<String, dynamic> toJson() => {
    'latitude': latitude,
    'longitude': longitude,
    'address': address,
    'district': district,
    'accuracy': accuracy,
    'timestamp': timestamp.toIso8601String(),
    'is_valid': isValid,
  };
  
  factory LocationData.fromPosition(
    Position position,
    String address,
    String district,
  ) {
    return LocationData(
      latitude: position.latitude,
      longitude: position.longitude,
      address: address,
      district: district,
      accuracy: position.accuracy,
      timestamp: position.timestamp,
    );
  }
}
