import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

/// Generic HTTP client wrapper for the FastAPI backend.
class ApiService {
  final http.Client _client = http.Client();

  // ── GET ───────────────────────────────────────────────
  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path')
        .replace(queryParameters: query);
    final response = await _client
        .get(uri, headers: _headers())
        .timeout(ApiConfig.timeout);
    return _handleResponse(response);
  }

  // ── POST (JSON) ───────────────────────────────────────
  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path');
    final response = await _client
        .post(uri, headers: _headers(), body: jsonEncode(body))
        .timeout(ApiConfig.timeout);
    return _handleResponse(response);
  }

  // ── POST (Multipart — for evidence upload) ────────────
  Future<dynamic> postMultipart(
    String path, {
    required String filePath,
    required String fieldName,
    Map<String, String>? fields,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path');
    final request = http.MultipartRequest('POST', uri)
      ..headers.addAll(_headers(multipart: true))
      ..files.add(await http.MultipartFile.fromPath(fieldName, filePath));
    if (fields != null) request.fields.addAll(fields);

    final streamed = await _client.send(request).timeout(ApiConfig.timeout);
    final response = await http.Response.fromStream(streamed);
    return _handleResponse(response);
  }

  // ── Helpers ───────────────────────────────────────────
  Map<String, String> _headers({bool multipart = false}) {
    final h = <String, String>{};
    if (!multipart) h['Content-Type'] = 'application/json';
    h['Accept'] = 'application/json';
    return h;
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      return jsonDecode(response.body);
    }
    final detail = _tryParseError(response.body);
    throw ApiException(response.statusCode, detail);
  }

  String _tryParseError(String body) {
    try {
      final json = jsonDecode(body);
      return json['detail']?.toString() ?? body;
    } catch (_) {
      return body;
    }
  }

  void dispose() => _client.close();
}

/// Custom API exception.
class ApiException implements Exception {
  final int statusCode;
  final String message;
  const ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}
