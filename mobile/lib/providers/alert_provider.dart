import 'package:flutter/foundation.dart';
import '../models/alert_model.dart';
import '../services/api_service.dart';

class AlertProvider extends ChangeNotifier {
  List<AlertModel> _alerts = [];
  bool _isLoading = false;
  String? _error;

  List<AlertModel> get alerts => _alerts;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Filter getters
  List<AlertModel> getFilteredAlerts({
    String? filterDistance,
    String? filterCategory,
    String sortBy = 'recent',
  }) {
    List<AlertModel> filtered = List.from(_alerts);

    // Filter by distance
    if (filterDistance != null && filterDistance != 'all') {
      final maxDistance = double.tryParse(filterDistance) ?? 100;
      filtered = filtered.where((a) => a.distance <= maxDistance).toList();
    }

    // Filter by category
    if (filterCategory != null && filterCategory != 'all') {
      filtered = filtered.where((a) => a.type.name == filterCategory).toList();
    }

    // Sort
    switch (sortBy) {
      case 'recent':
        filtered.sort((a, b) => b.createdAt.compareTo(a.createdAt));
        break;
      case 'distance':
        filtered.sort((a, b) => a.distance.compareTo(b.distance));
        break;
    }

    return filtered;
  }

  // Fetch alerts from API
  Future<void> fetchAlerts() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await ApiService.getAlerts();

      _isLoading = false;

      if (result['success']) {
        final alertsData = result['data']['alerts'] as List;
        _alerts = alertsData.map((data) => _mapAlertFromApi(data)).toList();
        notifyListeners();
      } else {
        _error = result['error'] ?? 'Failed to fetch alerts';
        notifyListeners();
      }
    } catch (e) {
      _isLoading = false;
      _error = 'Failed to fetch alerts: $e';
      notifyListeners();
    }
  }

  AlertModel _mapAlertFromApi(Map<String, dynamic> data) {
    return AlertModel(
      id: data['id'].toString(),
      title: data['title'] ?? '',
      description: data['message'] ?? data['description'] ?? '',
      type: _mapAlertType(data['alertType']),
      latitude: (data['latitude'] ?? -1.9403).toDouble(),
      longitude: (data['longitude'] ?? 29.8739).toDouble(),
      address: data['district'] ?? data['province'] ?? 'Rwanda',
      createdAt: data['createdAt'] != null
          ? DateTime.parse(data['createdAt'])
          : DateTime.now(),
      distance: _calculateDistance(data['latitude'], data['longitude']),
      isRead: false,
    );
  }

  AlertType _mapAlertType(String? type) {
    switch (type) {
      case 'emergency':
        return AlertType.incident;
      case 'safety':
        return AlertType.safety;
      case 'police':
        return AlertType.police;
      case 'weather':
      case 'warning':
        return AlertType.warning;
      case 'community':
        return AlertType.safety;
      default:
        return AlertType.safety;
    }
  }

  // Simple distance calculation (placeholder - in real app use geolocator)
  double _calculateDistance(double? lat, double? lng) {
    // Default to random distance for now
    // In real app, calculate from user's current location
    if (lat == null || lng == null) return 5.0;
    return (lat.abs() + lng.abs()) % 10 + 0.5;
  }

  // Mark alert as read
  void markAsRead(String alertId) {
    final index = _alerts.indexWhere((a) => a.id == alertId);
    if (index != -1) {
      final alert = _alerts[index];
      _alerts[index] = AlertModel(
        id: alert.id,
        title: alert.title,
        description: alert.description,
        type: alert.type,
        latitude: alert.latitude,
        longitude: alert.longitude,
        address: alert.address,
        createdAt: alert.createdAt,
        distance: alert.distance,
        isRead: true,
      );
      notifyListeners();
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
