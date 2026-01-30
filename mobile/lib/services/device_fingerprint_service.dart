import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import 'package:crypto/crypto.dart' as crypto;

/// Service for creating a pseudonymous device fingerprint.
/// 
/// This fingerprint is used to:
/// - Track device trust scores WITHOUT identifying the user
/// - Detect patterns across reports from the same device
/// - Enable the verification system while preserving privacy
/// 
/// PRIVACY GUARANTEES:
/// - No personal identifiable information (PII) is collected
/// - Fingerprint is hashed and cannot be reversed
/// - Device ID is randomly generated if hardware ID unavailable
/// - User can reset fingerprint at any time
class DeviceFingerprintService {
  static const String _fingerprintKey = 'device_fingerprint';
  static const String _installIdKey = 'install_id';
  static const String _createdAtKey = 'fingerprint_created_at';
  
  String? _cachedFingerprint;
  
  /// Get or generate the device fingerprint.
  /// 
  /// Returns a hashed fingerprint that is consistent across app sessions
  /// but cannot be used to identify the actual device.
  Future<String> getFingerprint() async {
    // Return cached value if available
    if (_cachedFingerprint != null) {
      return _cachedFingerprint!;
    }
    
    final prefs = await SharedPreferences.getInstance();
    
    // Check for existing fingerprint
    String? existingFingerprint = prefs.getString(_fingerprintKey);
    if (existingFingerprint != null) {
      _cachedFingerprint = existingFingerprint;
      return existingFingerprint;
    }
    
    // Generate new fingerprint
    String fingerprint = await _generateFingerprint();
    
    // Store fingerprint
    await prefs.setString(_fingerprintKey, fingerprint);
    await prefs.setString(_createdAtKey, DateTime.now().toIso8601String());
    
    _cachedFingerprint = fingerprint;
    return fingerprint;
  }
  
  /// Generate a new device fingerprint.
  /// 
  /// Creates a hash based on:
  /// - Random installation ID (generated once per install)
  /// - Platform information (iOS/Android)
  /// - Non-identifying device characteristics
  Future<String> _generateFingerprint() async {
    final prefs = await SharedPreferences.getInstance();
    
    // Get or create installation ID
    String installId = prefs.getString(_installIdKey) ?? '';
    if (installId.isEmpty) {
      installId = const Uuid().v4();
      await prefs.setString(_installIdKey, installId);
    }
    
    // Collect non-identifying characteristics
    List<String> characteristics = [
      installId,
      _getPlatformString(),
      _getLocaleString(),
      DateTime.now().timeZoneOffset.inHours.toString(),
    ];
    
    // Create hash using SHA-256
    String combined = characteristics.join('|');
    var bytes = utf8.encode(combined);
    var digest = crypto.sha256.convert(bytes);
    
    return digest.toString().substring(0, 32); // First 32 chars of hash
  }
  
  /// Get platform identification string.
  String _getPlatformString() {
    if (kIsWeb) return 'web';
    if (Platform.isAndroid) return 'android';
    if (Platform.isIOS) return 'ios';
    return 'unknown';
  }
  
  /// Get locale string (non-identifying).
  String _getLocaleString() {
    try {
      return Platform.localeName.split('_').first; // Just language, not full locale
    } catch (e) {
      return 'en';
    }
  }
  
  /// Reset the device fingerprint.
  /// 
  /// This generates a new fingerprint, effectively creating a "new device"
  /// from the system's perspective. This resets trust score history.
  Future<void> resetFingerprint() async {
    final prefs = await SharedPreferences.getInstance();
    
    // Remove existing fingerprint
    await prefs.remove(_fingerprintKey);
    await prefs.remove(_installIdKey);
    await prefs.remove(_createdAtKey);
    
    // Clear cache
    _cachedFingerprint = null;
    
    // Generate new fingerprint
    await getFingerprint();
  }
  
  /// Get metadata about the fingerprint (for debugging/user info).
  Future<Map<String, dynamic>> getFingerprintInfo() async {
    final prefs = await SharedPreferences.getInstance();
    
    return {
      'fingerprint_exists': prefs.containsKey(_fingerprintKey),
      'created_at': prefs.getString(_createdAtKey),
      'platform': _getPlatformString(),
      // Don't include actual fingerprint in info for security
    };
  }
  
  /// Check if this is a new installation.
  Future<bool> isNewInstallation() async {
    final prefs = await SharedPreferences.getInstance();
    return !prefs.containsKey(_fingerprintKey);
  }
  
  /// Get the fingerprint creation date.
  Future<DateTime?> getCreatedAt() async {
    final prefs = await SharedPreferences.getInstance();
    String? createdAt = prefs.getString(_createdAtKey);
    if (createdAt != null) {
      return DateTime.parse(createdAt);
    }
    return null;
  }
}
