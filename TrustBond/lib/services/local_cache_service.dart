import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class LocalCacheService {
  static const String _incidentTypesKey = 'tb_cached_incident_types_v1';
  static const String _reportsKeyPrefix = 'tb_cached_reports_v1_';

  String _reportsKey(String deviceId) => '$_reportsKeyPrefix$deviceId';

  Future<void> cacheIncidentTypes(List<dynamic> incidentTypes) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_incidentTypesKey, jsonEncode(incidentTypes));
  }

  Future<List<Map<String, dynamic>>> getCachedIncidentTypes() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_incidentTypesKey);
    if (raw == null || raw.trim().isEmpty) return [];

    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return [];
      return decoded
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList(growable: false);
    } catch (_) {
      return [];
    }
  }

  Future<void> cacheReports(String deviceId, List<dynamic> reports) async {
    if (deviceId.trim().isEmpty) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_reportsKey(deviceId), jsonEncode(reports));
  }

  Future<List<Map<String, dynamic>>> getCachedReports(String deviceId) async {
    if (deviceId.trim().isEmpty) return [];
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_reportsKey(deviceId));
    if (raw == null || raw.trim().isEmpty) return [];

    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return [];
      return decoded
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList(growable: false);
    } catch (_) {
      return [];
    }
  }

  Future<void> clearAll() async {
    final prefs = await SharedPreferences.getInstance();
    final keysToRemove = prefs
        .getKeys()
        .where((key) => key == _incidentTypesKey || key.startsWith(_reportsKeyPrefix))
        .toList(growable: false);

    for (final key in keysToRemove) {
      await prefs.remove(key);
    }
  }
}
