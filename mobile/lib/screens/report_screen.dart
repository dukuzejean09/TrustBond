import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../models/incident_type.dart';
import '../models/location.dart';
import '../models/report.dart';
import '../providers/device_provider.dart';
import '../providers/report_provider.dart';
import '../services/location_service.dart';
import '../services/motion_service.dart';

/// Report submission screen with incident type, description, auto-GPS & motion.
class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _descController = TextEditingController();

  IncidentType? _selectedType;
  double? _latitude;
  double? _longitude;
  double? _gpsAccuracy;
  String? _motionLevel;
  double? _movementSpeed;
  bool? _wasStationary;
  bool _capturingLocation = false;
  bool _capturingMotion = false;
  String? _locationError;

  // Auto-detected village from backend (nearest centroid)
  Location? _detectedVillage;
  bool _detectingVillage = false;

  final _locationService = LocationService();
  final _motionService = MotionService();

  @override
  void initState() {
    super.initState();
    // Fetch incident types on open
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ReportProvider>().fetchIncidentTypes();
      _captureLocationAndMotion();
    });
  }

  Future<void> _captureLocationAndMotion() async {
    // GPS
    setState(() {
      _capturingLocation = true;
      _locationError = null;
    });
    try {
      final pos = await _locationService.getCurrentPosition();
      if (pos != null) {
        setState(() {
          _latitude = pos.latitude;
          _longitude = pos.longitude;
          _gpsAccuracy = pos.accuracy;
        });

        // Attempt to auto-detect nearest village using backend locations
        try {
          setState(() => _detectingVillage = true);
          final loc = await context.read<ReportProvider>().findNearestLocation(_latitude!, _longitude!);
          if (loc != null) setState(() => _detectedVillage = loc);
        } catch (e) {
          debugPrint('Village detection failed: $e');
        } finally {
          setState(() => _detectingVillage = false);
        }
      } else {
        setState(() => _locationError = 'Could not get location. Check GPS permissions.');
      }
    } catch (e) {
      setState(() => _locationError = 'GPS error: $e');
    } finally {
      setState(() => _capturingLocation = false);
    }

    // Motion
    setState(() => _capturingMotion = true);
    try {
      final motion = await _motionService.capture();
      setState(() {
        _motionLevel = motion.motionLevel;
        _movementSpeed = motion.movementSpeed;
        _wasStationary = motion.wasStationary;
      });
    } catch (_) {
      // Sensor data is optional — silent fail
    } finally {
      setState(() => _capturingMotion = false);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedType == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select an incident type')),
      );
      return;
    }
    if (_latitude == null || _longitude == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Waiting for GPS location...')),
      );
      return;
    }

    final deviceHash = context.read<DeviceProvider>().deviceHash ?? '';
    final report = Report(
      deviceHash: deviceHash,
      incidentTypeId: _selectedType!.incidentTypeId,
      description: _descController.text.trim(),
      latitude: _latitude!,
      longitude: _longitude!,
      gpsAccuracy: _gpsAccuracy,
      motionLevel: _motionLevel,
      movementSpeed: _movementSpeed,
      wasStationary: _wasStationary,
      villageLocationId: _detectedVillage?.locationId.toString(),
    );

    final ok = await context.read<ReportProvider>().submitReport(report);
    if (!mounted) return;

    if (ok) {
      _showSuccessDialog();
    } else {
      final err = context.read<ReportProvider>().lastError;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(err ?? 'Submission failed'), backgroundColor: AppTheme.error),
      );
    }
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.check_circle, color: AppTheme.success, size: 28),
            SizedBox(width: 8),
            Text('Report Submitted'),
          ],
        ),
        content: const Text(
          'Thank you! Your report has been submitted anonymously and will be reviewed.',
        ),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop(); // close dialog
              Navigator.of(context).pop(); // back to home
            },
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _descController.dispose();
    _motionService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reportProv = context.watch<ReportProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('New Report')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Incident Type ─────────────────────────
              Text('Incident Type *',
                  style: Theme.of(context)
                      .textTheme
                      .titleSmall
                      ?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              reportProv.loadingTypes
                  ? const Center(child: CircularProgressIndicator())
                  : DropdownButtonFormField<IncidentType>(
                      decoration: const InputDecoration(
                        hintText: 'Select incident type',
                        prefixIcon: Icon(Icons.category_outlined),
                      ),
                      value: _selectedType,
                      items: reportProv.incidentTypes
                          .map((t) => DropdownMenuItem(
                              value: t, child: Text(t.typeName)))
                          .toList(),
                      onChanged: (v) => setState(() => _selectedType = v),
                      validator: (v) =>
                          v == null ? 'Select an incident type' : null,
                    ),

              const SizedBox(height: 20),

              // ── Description ───────────────────────────
              Text('Description *',
                  style: Theme.of(context)
                      .textTheme
                      .titleSmall
                      ?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              TextFormField(
                controller: _descController,
                maxLines: 4,
                decoration: const InputDecoration(
                  hintText: 'Describe the incident...',
                  prefixIcon: Padding(
                    padding: EdgeInsets.only(bottom: 48),
                    child: Icon(Icons.edit_note),
                  ),
                ),
                validator: (v) =>
                    v == null || v.trim().isEmpty ? 'Description is required' : null,
              ),

              const SizedBox(height: 20),

              // ── GPS Status ────────────────────────────
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            _latitude != null
                                ? Icons.location_on
                                : Icons.location_searching,
                            color: _latitude != null
                                ? AppTheme.success
                                : AppTheme.warning,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'GPS Location',
                            style: Theme.of(context)
                                .textTheme
                                .titleSmall
                                ?.copyWith(fontWeight: FontWeight.w600),
                          ),
                          const Spacer(),
                          if (_capturingLocation)
                            const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      if (_latitude != null)
                        Text(
                          'Lat: ${_latitude!.toStringAsFixed(6)}  •  Lng: ${_longitude!.toStringAsFixed(6)}\n'
                          'Accuracy: ${_gpsAccuracy?.toStringAsFixed(1) ?? '—'} m',
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: AppTheme.textSecondary),
                        )
                      else if (_locationError != null)
                        Text(_locationError!,
                            style: const TextStyle(
                                color: AppTheme.error, fontSize: 12))
                      else
                        const Text('Acquiring GPS...',
                            style: TextStyle(color: AppTheme.textSecondary)),
                    ],
                  ),
                ),
              ),

              // ── Auto-detected Village (from backend) ───
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Icon(Icons.public,
                          color: _detectedVillage != null ? AppTheme.success : AppTheme.warning),
                      const SizedBox(width: 8),
                      Expanded(
                        child: _detectingVillage
                            ? const Text('Detecting nearest village...',
                                style: TextStyle(color: AppTheme.textSecondary))
                            : _detectedVillage != null
                                ? Text('Detected village: ${_detectedVillage!.locationName}',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodySmall
                                        ?.copyWith(color: AppTheme.textSecondary))
                                : const Text('Village not detected',
                                    style: TextStyle(color: AppTheme.textSecondary)),
                      ),
                      if (_detectingVillage)
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 8),

              // ── Motion Status ─────────────────────────
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(
                        _motionLevel != null
                            ? Icons.directions_walk
                            : Icons.sensors,
                        color: _motionLevel != null
                            ? AppTheme.success
                            : AppTheme.warning,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Motion Sensor',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleSmall
                                  ?.copyWith(fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _capturingMotion
                                  ? 'Sampling motion...'
                                  : _motionLevel != null
                                      ? 'Level: $_motionLevel  •  Speed: $_movementSpeed  •  ${_wasStationary == true ? 'Stationary' : 'Moving'}'
                                      : 'No sensor data',
                              style: Theme.of(context)
                                  .textTheme
                                  .bodySmall
                                  ?.copyWith(color: AppTheme.textSecondary),
                            ),
                          ],
                        ),
                      ),
                      if (_capturingMotion)
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // ── Submit Button ─────────────────────────
              SizedBox(
                height: 52,
                child: ElevatedButton.icon(
                  onPressed: reportProv.submitting ? null : _submit,
                  icon: reportProv.submitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.send),
                  label: Text(
                      reportProv.submitting ? 'Submitting...' : 'Submit Report'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
