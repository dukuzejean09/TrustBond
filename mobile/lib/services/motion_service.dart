import 'dart:async';
import 'dart:math';
import 'package:sensors_plus/sensors_plus.dart';
import '../config/constants.dart';

/// Captures accelerometer data and classifies motion level.
class MotionService {
  StreamSubscription<AccelerometerEvent>? _sub;
  final List<double> _magnitudes = [];

  /// Sample accelerometer for [duration] and return motion summary.
  Future<MotionData> capture({Duration duration = const Duration(seconds: 3)}) async {
    _magnitudes.clear();

    final completer = Completer<MotionData>();

    _sub = accelerometerEventStream(
      samplingPeriod: const Duration(milliseconds: 100),
    ).listen((event) {
      final mag = sqrt(event.x * event.x + event.y * event.y + event.z * event.z);
      // subtract gravity (~9.8) to get user acceleration
      _magnitudes.add((mag - 9.8).abs());
    });

    await Future.delayed(duration);
    await _sub?.cancel();

    if (_magnitudes.isEmpty) {
      return const MotionData(motionLevel: 'low', movementSpeed: 0.0, wasStationary: true);
    }

    final avg = _magnitudes.reduce((a, b) => a + b) / _magnitudes.length;
    final maxVal = _magnitudes.reduce(max);

    String level;
    if (avg < AppConstants.lowMotionThreshold) {
      level = 'low';
    } else if (avg < AppConstants.highMotionThreshold) {
      level = 'medium';
    } else {
      level = 'high';
    }

    return MotionData(
      motionLevel: level,
      movementSpeed: double.parse(avg.toStringAsFixed(2)),
      wasStationary: level == 'low' && maxVal < AppConstants.lowMotionThreshold * 2,
    );
  }

  void dispose() => _sub?.cancel();
}

/// Simple data class for motion capture results.
class MotionData {
  final String motionLevel;   // low | medium | high
  final double movementSpeed;
  final bool wasStationary;

  const MotionData({
    required this.motionLevel,
    required this.movementSpeed,
    required this.wasStationary,
  });
}
