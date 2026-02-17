import 'package:flutter/foundation.dart';
import '../services/device_service.dart';

/// Manages device registration state.
class DeviceProvider extends ChangeNotifier {
  final DeviceService _deviceService;

  DeviceProvider(this._deviceService);

  String? _deviceHash;
  String? get deviceHash => _deviceHash;

  bool _initialized = false;
  bool get initialized => _initialized;

  /// Initialize (or retrieve cached) device hash.
  Future<void> initialize() async {
    if (_initialized) return;
    _deviceHash = await _deviceService.getDeviceHash();
    _initialized = true;
    notifyListeners();
  }
}
