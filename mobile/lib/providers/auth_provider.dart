import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class UserModel {
  final int id;
  final String email;
  final String? firstName;
  final String? lastName;
  final String role;
  final String? phone;
  final bool isActive;

  UserModel({
    required this.id,
    required this.email,
    this.firstName,
    this.lastName,
    required this.role,
    this.phone,
    this.isActive = true,
  });

  String get fullName => '${firstName ?? ''} ${lastName ?? ''}'.trim();

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'],
      email: json['email'],
      firstName: json['firstName'],
      lastName: json['lastName'],
      role: json['role'],
      phone: json['phone'],
      isActive: json['isActive'] ?? true,
    );
  }
}

class AuthProvider extends ChangeNotifier {
  UserModel? _user;
  bool _isLoading = false;
  bool _isAuthenticated = false;
  String? _error;

  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _isAuthenticated;
  String? get error => _error;

  // Initialize - check if user is already logged in
  Future<void> initialize() async {
    _isLoading = true;
    notifyListeners();

    try {
      // First, load token from storage
      await ApiService.init();
      
      // Only try to get current user if we have a token
      if (!ApiService.isAuthenticated) {
        _isAuthenticated = false;
        _user = null;
        _isLoading = false;
        notifyListeners();
        return;
      }
      
      final result = await ApiService.getCurrentUser();
      
      if (result['success']) {
        _user = UserModel.fromJson(result['data']['user']);
        _isAuthenticated = true;
      } else {
        _isAuthenticated = false;
        _user = null;
      }
    } catch (e) {
      _isAuthenticated = false;
      _user = null;
    }

    _isLoading = false;
    notifyListeners();
  }

  // Register new user
  Future<bool> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
    String? nationalId,
    String? district,
    String? sector,
    String? cell,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await ApiService.register(
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
        phone: phone,
        nationalId: nationalId,
        district: district,
        sector: sector,
        cell: cell,
      );

      _isLoading = false;

      if (result['success']) {
        _user = UserModel.fromJson(result['data']['user']);
        _isAuthenticated = true;
        notifyListeners();
        return true;
      } else {
        _error = result['error'] ?? 'Registration failed';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _isLoading = false;
      _error = 'Registration failed: $e';
      notifyListeners();
      return false;
    }
  }

  // Login
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await ApiService.login(
        email: email,
        password: password,
      );

      _isLoading = false;

      if (result['success']) {
        _user = UserModel.fromJson(result['data']['user']);
        _isAuthenticated = true;
        notifyListeners();
        return true;
      } else {
        _error = result['error'] ?? 'Login failed';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _isLoading = false;
      _error = 'Login failed: $e';
      notifyListeners();
      return false;
    }
  }

  // Logout
  Future<void> logout() async {
    await ApiService.logout();
    _user = null;
    _isAuthenticated = false;
    notifyListeners();
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
