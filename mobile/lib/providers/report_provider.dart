import 'package:flutter/foundation.dart';
import 'dart:math' as math;
import '../config/api_config.dart';
import '../models/incident_type.dart';
import '../models/report.dart';
import '../models/location.dart';
import '../services/api_service.dart';

/// Manages report submission state and incident type fetching.
class ReportProvider extends ChangeNotifier {
  final ApiService _api;

  ReportProvider(this._api);

  // ── Incident Types ────────────────────────────────────
  List<IncidentType> _incidentTypes = [];
  List<IncidentType> get incidentTypes => _incidentTypes;

  bool _loadingTypes = false;
  bool get loadingTypes => _loadingTypes;

  Future<void> fetchIncidentTypes() async {
    _loadingTypes = true;
    notifyListeners();
    try {
      final data = await _api.get(ApiConfig.incidentTypes);
      _incidentTypes = (data as List)
          .map((e) => IncidentType.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      debugPrint('Failed to fetch incident types: $e');
    } finally {
      _loadingTypes = false;
      notifyListeners();
    }
  }

  // ── Locations (auto-detection) ───────────────────────
  List<Location> _locations = [];
  List<Location> get locations => _locations;

  bool _loadingLocations = false;
  bool get loadingLocations => _loadingLocations;

  /// Fetch locations from backend (optional filters).
  Future<void> fetchLocations({String? locationType, int? parentLocationId}) async {
    _loadingLocations = true;
    notifyListeners();
    try {
      final query = <String, String>{};
      if (locationType != null) query['location_type'] = locationType;
      if (parentLocationId != null) query['parent_location_id'] = parentLocationId.toString();
      final data = await _api.get(ApiConfig.locations, query: query.isEmpty ? null : query);
      _locations = (data as List)
          .map((e) => Location.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      debugPrint('Failed to fetch locations: $e');
    } finally {
      _loadingLocations = false;
      notifyListeners();
    }
  }

  double _deg2rad(double deg) => deg * (math.pi / 180.0);

  double _haversineDistanceMeters(double lat1, double lon1, double lat2, double lon2) {
    const R = 6371000.0; // metres
    final dLat = _deg2rad(lat2 - lat1);
    final dLon = _deg2rad(lon2 - lon1);
    final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(_deg2rad(lat1)) * math.cos(_deg2rad(lat2)) *
            math.sin(dLon / 2) * math.sin(dLon / 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    return R * c;
  }

  /// Reverse-geocode (server-side) then fallback to centroid lookup.
  Future<Location?> findNearestLocation(double lat, double lon, {String locationType = 'village'}) async {
    // 1) Ask backend to reverse-geocode (preferred)
    try {
      final data = await _api.get('${ApiConfig.locations}/reverse', query: {
        'lat': lat.toString(),
        'lon': lon.toString(),
        'location_type': locationType,
      });
      if (data != null && data is Map<String, dynamic>) {
        return Location.fromJson(data);
      }
    } catch (e) {
      debugPrint('Backend reverse-geocode failed: $e');
      // fall through to client-side centroid lookup
    }

    // 2) Fallback — client-side centroid search
    if (_locations.isEmpty || (_locations.isNotEmpty && _locations.first.locationType != locationType)) {
      await fetchLocations(locationType: locationType);
    }
    Location? best;
    var bestDist = double.infinity;
    for (final loc in _locations) {
      if (loc.centroidLat == null || loc.centroidLong == null) continue;
      final d = _haversineDistanceMeters(lat, lon, loc.centroidLat!, loc.centroidLong!);
      if (d < bestDist) {
        bestDist = d;
        best = loc;
      }
    }
    return best;
  }

  // ── Report Submission ─────────────────────────────────
  bool _submitting = false;
  bool get submitting => _submitting;

  String? _lastError;
  String? get lastError => _lastError;

  bool _submitted = false;
  bool get submitted => _submitted;

  Future<bool> submitReport(Report report) async {
    _submitting = true;
    _lastError = null;
    _submitted = false;
    notifyListeners();
    try {
      await _api.post(ApiConfig.reports, body: report.toSubmitJson());
      _submitted = true;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _lastError = e.message;
      notifyListeners();
      return false;
    } catch (e) {
      _lastError = 'Connection error. Please check your network.';
      notifyListeners();
      return false;
    } finally {
      _submitting = false;
      notifyListeners();
    }
  }

  /// Reset submission state for a new report.
  void reset() {
    _submitted = false;
    _lastError = null;
    notifyListeners();
  }

  // ── Report History ────────────────────────────────────
  List<Report> _history = [];
  List<Report> get history => _history;

  bool _loadingHistory = false;
  bool get loadingHistory => _loadingHistory;

  Future<void> fetchHistory(String deviceHash) async {
    _loadingHistory = true;
    notifyListeners();
    try {
      final data = await _api.get(ApiConfig.reports, query: {'device_hash': deviceHash});
      final items = data is List ? data : (data['items'] as List?) ?? [];
      _history = items
          .map((e) => Report.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      debugPrint('Failed to fetch history: $e');
    } finally {
      _loadingHistory = false;
      notifyListeners();
    }
  }
}
