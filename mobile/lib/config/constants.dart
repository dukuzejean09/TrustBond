import 'package:flutter/foundation.dart' show kIsWeb;

class AppConstants {
  // App Info
  static const String appName = 'Crime Report';
  static const String appVersion = '1.0.0';
  
  // API Configuration
  // For Web: 'http://localhost:5000/api'
  // For Android emulator: 'http://10.0.2.2:5000/api'
  // For iOS simulator: 'http://localhost:5000/api'
  // For physical device: use your machine's IP, e.g., 'http://192.168.1.x:5000/api'
  // For production: 'https://api.trustbond.rw/api'
  static String get apiBaseUrl {
    if (kIsWeb) {
      return 'http://localhost:5000/api';
    }
    // Android emulator uses 10.0.2.2 to access host machine's localhost
    return 'http://10.0.2.2:5000/api';
  }
  
  // Storage Keys
  static const String keyIsFirstTime = 'isFirstTime';
  static const String keyIsDarkMode = 'isDarkMode';
  static const String keyIsAnonymous = 'isAnonymous';
  static const String keyLanguage = 'language';
  static const String keyNotifications = 'notifications';
  static const String keyOfflineReports = 'offlineReports';
  static const String keyUserProfile = 'userProfile';
  static const String keyAuthToken = 'authToken';
  
  // Default Values
  static const bool defaultAnonymous = true;
  static const String defaultLanguage = 'en';
  static const bool defaultNotifications = true;
  
  // Validation
  static const int minDescriptionLength = 10;
  static const int maxDescriptionLength = 1000;
  static const int maxEvidenceFiles = 10;
  static const int maxVideoSeconds = 60;
  static const int maxAudioSeconds = 120;
  
  // Map
  static const double defaultLatitude = -1.9403;
  static const double defaultLongitude = 29.8739;
  static const double defaultZoom = 15.0;
  
  // Report Status
  static const String statusSubmitted = 'submitted';
  static const String statusUnderReview = 'under_review';
  static const String statusVerified = 'verified';
  static const String statusClosed = 'closed';
}
