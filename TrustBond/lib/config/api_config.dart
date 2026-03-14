import 'package:flutter/foundation.dart';

/// API base URL. Change via --dart-define when running, or edit the default below.
///
/// **Production:** Uses Render-hosted backend (auto-deployed from GitHub).
/// **Override:** flutter run --dart-define=API_BASE_URL=https://YOUR_URL/api/v1
class ApiConfig {
  /// Backend URL selection strategy:
  /// - API_BASE_URL (dart-define) when provided
  /// - release/profile default: Render backend
  /// - debug default: local Docker backend via Android emulator loopback
  static String get baseUrl {
    const overridden = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (overridden.isNotEmpty) return _url(overridden);
    if (!kDebugMode) {
      return 'https://trustbond-backend.onrender.com/api/v1';
    }
    return 'http://10.0.2.2:8000/api/v1';
  }

  static String get devicesUrl => _url('$baseUrl/devices');
  static String get reportsUrl => _url('$baseUrl/reports');
  static String get incidentTypesUrl => _url('$baseUrl/incident-types');

  static String _url(String url) {
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    return 'http://$url';
  }

  static String evidenceFileUrl(String fileUrl) {
    if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://')) {
      return fileUrl;
    }
    final u = Uri.tryParse(baseUrl);
    final origin = (u != null && u.hasScheme)
        ? u.origin
        : 'http://${baseUrl.split('/').first}';
    return origin + (fileUrl.startsWith('/') ? fileUrl : '/$fileUrl');
  }
}
