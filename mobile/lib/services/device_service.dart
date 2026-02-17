import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Generates and caches a pseudonymous device hash (SHA-256).
///
/// The hash is derived from stable device attributes so the same physical
/// device always produces the same identifier — no personal data is stored.
class DeviceService {
  static const _cacheKey = 'device_hash';
  String? _cachedHash;

  /// Returns the SHA-256 device hash, computing it only on first call.
  Future<String> getDeviceHash() async {
    if (_cachedHash != null) return _cachedHash!;

    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_cacheKey);
    if (stored != null) {
      _cachedHash = stored;
      return stored;
    }

    final hash = await _computeHash();
    await prefs.setString(_cacheKey, hash);
    _cachedHash = hash;
    return hash;
  }

  Future<String> _computeHash() async {
    final plugin = DeviceInfoPlugin();
    final String rawFingerprint;

    final android = await plugin.androidInfo;
    rawFingerprint = [
      android.brand,
      android.model,
      android.id,
      android.fingerprint,
      android.hardware,
    ].join('|');

    final bytes = utf8.encode(rawFingerprint);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }
}
