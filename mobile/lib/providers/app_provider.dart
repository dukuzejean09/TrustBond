import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppProvider extends ChangeNotifier {
  bool _isFirstTime;
  bool _isAnonymousMode = true;
  bool _notificationsEnabled = true;
  String _language = 'en';
  bool _isOnline = true;
  bool _isGpsActive = false;

  AppProvider(this._isFirstTime);

  // Getters
  bool get isFirstTime => _isFirstTime;
  bool get isAnonymousMode => _isAnonymousMode;
  bool get isAnonymous => _isAnonymousMode;
  bool get notificationsEnabled => _notificationsEnabled;
  String get language => _language;
  bool get isOnline => _isOnline;
  bool get isGpsActive => _isGpsActive;

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
}
