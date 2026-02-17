/// App-wide constants.
class AppConstants {
  AppConstants._();

  static const String appName = 'TrustBond';
  static const String appTagline = 'Report Safely. Stay Anonymous.';

  // ── Rwanda / Musanze geographic bounds ────────────────
  static const double rwandaMinLat = -2.85;
  static const double rwandaMaxLat = -1.05;
  static const double rwandaMinLng = 28.85;
  static const double rwandaMaxLng = 30.90;

  static const double musanzeMinLat = -1.60;
  static const double musanzeMaxLat = -1.45;
  static const double musanzeMinLng = 29.50;
  static const double musanzeMaxLng = 29.70;

  // ── Motion thresholds ─────────────────────────────────
  static const double lowMotionThreshold = 1.0;
  static const double highMotionThreshold = 5.0;

  // ── Local DB ──────────────────────────────────────────
  static const String localDbName = 'trustbond_offline.db';
  static const int localDbVersion = 1;
}
