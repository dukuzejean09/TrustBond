/// API configuration constants.
class ApiConfig {
  ApiConfig._();

  /// Your machine's local IP — both the phone and PC must be on the same Wi-Fi.
  /// Find it with `ipconfig` (Windows) and update if your IP changes.
  static const String baseUrl = 'http://192.168.31.62:8000/api/v1';

  static const Duration timeout = Duration(seconds: 30);

  // ── Endpoint paths ───────────────────────────────────
  static const String login = '/auth/login';
  static const String devices = '/devices';
  static const String reports = '/reports';
  static const String incidentTypes = '/incident-types';
  static const String locations = '/locations';
  static const String evidence = '/evidence'; // appended to report path
}
