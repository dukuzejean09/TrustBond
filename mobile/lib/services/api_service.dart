import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/constants.dart';
import 'device_fingerprint_service.dart';

class ApiService {
  static String? _authToken;
  static final DeviceFingerprintService _fingerprintService = DeviceFingerprintService();

  // Initialize token from storage
  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _authToken = prefs.getString(AppConstants.keyAuthToken);
    // Pre-initialize fingerprint
    await _fingerprintService.getFingerprint();
  }

  // Get device fingerprint for requests
  static Future<String> getDeviceFingerprint() async {
    return await _fingerprintService.getFingerprint();
  }

  // Set auth token
  static Future<void> setAuthToken(String token) async {
    _authToken = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.keyAuthToken, token);
  }

  // Clear auth token
  static Future<void> clearAuthToken() async {
    _authToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.keyAuthToken);
  }

  // Get auth token
  static String? get authToken => _authToken;

  // Check if authenticated
  static bool get isAuthenticated => _authToken != null;

  // Get headers
  static Map<String, String> get _headers {
    final headers = {
      'Content-Type': 'application/json',
    };
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  // Handle response
  static Map<String, dynamic> _handleResponse(http.Response response) {
    final body = jsonDecode(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return {
        'success': true,
        'data': body,
      };
    } else {
      return {
        'success': false,
        'error': body['error'] ?? 'An error occurred',
        'statusCode': response.statusCode,
      };
    }
  }

  // ==================== Authentication ====================

  static Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
    String? nationalId,
    String? province,
    String? district,
    String? sector,
    String? cell,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${AppConstants.apiBaseUrl}/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
          'firstName': firstName,
          'lastName': lastName,
          'phone': phone,
          'nationalId': nationalId,
          'province': province,
          'district': district,
          'sector': sector,
          'cell': cell,
        }),
      );
      final result = _handleResponse(response);
      if (result['success'] && result['data']['token'] != null) {
        await setAuthToken(result['data']['token']);
      }
      return result;
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${AppConstants.apiBaseUrl}/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );
      final result = _handleResponse(response);
      if (result['success'] && result['data']['token'] != null) {
        await setAuthToken(result['data']['token']);
      }
      return result;
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  static Future<Map<String, dynamic>> getCurrentUser() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/auth/me'),
        headers: _headers,
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  static Future<void> logout() async {
    await clearAuthToken();
  }

  // ==================== Reports ====================

  // Create anonymous report (no authentication required)
  static Future<Map<String, dynamic>> createAnonymousReport({
    required String title,
    required String description,
    required String category,
    String priority = 'medium',
    String? province,
    String? district,
    String? sector,
    String? cell,
    String? village,
    double? latitude,
    double? longitude,
    String? locationDescription,
    String? incidentDate,
    String? incidentTime,
    String? anonymousContact,
    List<String>? attachments,
  }) async {
    try {
      // Get device fingerprint for trust scoring
      final fingerprint = await getDeviceFingerprint();
      
      final response = await http.post(
        Uri.parse('${AppConstants.apiBaseUrl}/reports/anonymous'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'title': title,
          'description': description,
          'category': category,
          'priority': priority,
          'province': province,
          'district': district,
          'sector': sector,
          'cell': cell,
          'village': village,
          'latitude': latitude,
          'longitude': longitude,
          'locationDescription': locationDescription,
          'incidentDate': incidentDate,
          'incidentTime': incidentTime,
          'anonymousContact': anonymousContact,
          'attachments': attachments ?? [],
          'device_fingerprint': fingerprint,  // For trust scoring
        }),
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  // Track anonymous report by tracking code
  static Future<Map<String, dynamic>> trackReport(String trackingCode) async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/reports/track/$trackingCode'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  // Create authenticated report (requires login)
  static Future<Map<String, dynamic>> createReport({
    required String title,
    required String description,
    required String category,
    String priority = 'medium',
    String? province,
    String? district,
    String? sector,
    String? cell,
    String? village,
    double? latitude,
    double? longitude,
    String? locationDescription,
    String? incidentDate,
    String? incidentTime,
    bool isAnonymous = false,
    List<String>? attachments,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${AppConstants.apiBaseUrl}/reports'),
        headers: _headers,
        body: jsonEncode({
          'title': title,
          'description': description,
          'category': category,
          'priority': priority,
          'province': province,
          'district': district,
          'sector': sector,
          'cell': cell,
          'village': village,
          'latitude': latitude,
          'longitude': longitude,
          'locationDescription': locationDescription,
          'incidentDate': incidentDate,
          'incidentTime': incidentTime,
          'isAnonymous': isAnonymous,
          'attachments': attachments ?? [],
        }),
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  static Future<Map<String, dynamic>> getMyReports({
    int page = 1,
    int perPage = 20,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/reports/my-reports?page=$page&per_page=$perPage'),
        headers: _headers,
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  static Future<Map<String, dynamic>> getReport(int id) async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/reports/$id'),
        headers: _headers,
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  // ==================== Alerts ====================

  static Future<Map<String, dynamic>> getAlerts({
    int page = 1,
    int perPage = 20,
    String? district,
  }) async {
    try {
      String url = '${AppConstants.apiBaseUrl}/alerts?page=$page&per_page=$perPage';
      if (district != null) {
        url += '&district=$district';
      }
      final response = await http.get(
        Uri.parse(url),
        headers: _headers,
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  // ==================== Mobile-Specific Endpoints ====================

  /// Get public statistics for home screen
  static Future<Map<String, dynamic>> getPublicStats() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/mobile/stats'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Get emergency contacts
  static Future<Map<String, dynamic>> getEmergencyContacts() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/mobile/emergency-contacts'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Get nearby reports summary (anonymized)
  static Future<Map<String, dynamic>> getNearbyReports({
    required double latitude,
    required double longitude,
    double radius = 5.0,
  }) async {
    try {
      final response = await http.get(
        Uri.parse(
          '${AppConstants.apiBaseUrl}/mobile/nearby-reports?latitude=$latitude&longitude=$longitude&radius=$radius',
        ),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Get crime categories
  static Future<Map<String, dynamic>> getCrimeCategories() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/mobile/crime-categories'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Get Rwanda districts by province
  static Future<Map<String, dynamic>> getDistricts() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/mobile/districts'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Get app configuration
  static Future<Map<String, dynamic>> getAppConfig() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/mobile/app-config'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Get reporting tips
  static Future<Map<String, dynamic>> getReportTips() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/mobile/report-tips'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Get FAQs
  static Future<Map<String, dynamic>> getFaqs() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/mobile/faqs'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Check API health
  static Future<Map<String, dynamic>> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConstants.apiBaseUrl}/health'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 5));
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Server unreachable'};
    }
  }

  // ==================== File Uploads ====================

  /// Upload a single evidence file
  static Future<Map<String, dynamic>> uploadEvidence(File file) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${AppConstants.apiBaseUrl}/uploads/evidence'),
      );
      
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Upload failed: $e'};
    }
  }

  /// Upload multiple evidence files
  static Future<Map<String, dynamic>> uploadMultipleEvidence(List<File> files) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${AppConstants.apiBaseUrl}/uploads/evidence/multiple'),
      );
      
      for (var file in files) {
        request.files.add(await http.MultipartFile.fromPath('files', file.path));
      }
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Upload failed: $e'};
    }
  }

  /// Delete an uploaded evidence file
  static Future<Map<String, dynamic>> deleteEvidence(String filename) async {
    try {
      final response = await http.delete(
        Uri.parse('${AppConstants.apiBaseUrl}/uploads/evidence/$filename'),
        headers: {'Content-Type': 'application/json'},
      );
      return _handleResponse(response);
    } catch (e) {
      return {'success': false, 'error': 'Delete failed: $e'};
    }
  }
}
