import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class AppProvider extends ChangeNotifier {
  bool _isFirstTime;
  bool _isAnonymousMode = true;
  bool _notificationsEnabled = true;
  String _language = 'en';
  bool _isOnline = true;
  bool _isGpsActive = false;
  
  // Public stats from API
  Map<String, dynamic>? _publicStats;
  List<Map<String, dynamic>>? _emergencyContacts;
  Map<String, dynamic>? _appConfig;
  bool _isLoadingStats = false;

  AppProvider(this._isFirstTime);

  // Getters
  bool get isFirstTime => _isFirstTime;
  bool get isAnonymousMode => _isAnonymousMode;
  bool get isAnonymous => _isAnonymousMode;
  bool get notificationsEnabled => _notificationsEnabled;
  String get language => _language;
  bool get isOnline => _isOnline;
  bool get isGpsActive => _isGpsActive;
  Map<String, dynamic>? get publicStats => _publicStats;
  List<Map<String, dynamic>>? get emergencyContacts => _emergencyContacts;
  Map<String, dynamic>? get appConfig => _appConfig;
  bool get isLoadingStats => _isLoadingStats;

  // Setters
  Future<void> setFirstTimeComplete() async {
    _isFirstTime = false;
    notifyListeners();
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isFirstTime', false);
  }

  Future<void> setAnonymousMode(bool value) async {
    _isAnonymousMode = value;
    notifyListeners();
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isAnonymous', value);
  }

  Future<void> setAnonymous(bool value) async {
    await setAnonymousMode(value);
  }

  Future<void> setNotifications(bool value) async {
    _notificationsEnabled = value;
    notifyListeners();
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('notifications', value);
  }

  Future<void> setNotificationsEnabled(bool value) async {
    await setNotifications(value);
  }

  Future<void> setLanguage(String value) async {
    _language = value;
    notifyListeners();
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('language', value);
  }

  void setOnlineStatus(bool value) {
    _isOnline = value;
    notifyListeners();
  }

  void setGpsActive(bool value) {
    _isGpsActive = value;
    notifyListeners();
  }

  Future<void> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    _isAnonymousMode = prefs.getBool('isAnonymous') ?? true;
    _notificationsEnabled = prefs.getBool('notifications') ?? true;
    _language = prefs.getString('language') ?? 'en';
    notifyListeners();
  }

  /// Check API connectivity
  Future<bool> checkConnectivity() async {
    final result = await ApiService.checkHealth();
    _isOnline = result['success'] == true;
    notifyListeners();
    return _isOnline;
  }

  /// Load public stats from API
  Future<void> loadPublicStats() async {
    _isLoadingStats = true;
    notifyListeners();

    try {
      final result = await ApiService.getPublicStats();
      if (result['success'] == true) {
        _publicStats = result['data']['stats'];
        _isOnline = true;
      }
    } catch (e) {
      debugPrint('Failed to load stats: $e');
    }

    _isLoadingStats = false;
    notifyListeners();
  }

  /// Load emergency contacts from API
  Future<void> loadEmergencyContacts() async {
    try {
      final result = await ApiService.getEmergencyContacts();
      if (result['success'] == true) {
        _emergencyContacts = List<Map<String, dynamic>>.from(
          result['data']['contacts'],
        );
      }
    } catch (e) {
      debugPrint('Failed to load emergency contacts: $e');
    }
    notifyListeners();
  }

  /// Load app config from API
  Future<void> loadAppConfig() async {
    try {
      final result = await ApiService.getAppConfig();
      if (result['success'] == true) {
        _appConfig = result['data']['config'];
      }
    } catch (e) {
      debugPrint('Failed to load app config: $e');
    }
    notifyListeners();
  }

  /// Initialize all data from API
  Future<void> initializeFromApi() async {
    await Future.wait([
      loadPublicStats(),
      loadEmergencyContacts(),
      loadAppConfig(),
    ]);
  }
}
