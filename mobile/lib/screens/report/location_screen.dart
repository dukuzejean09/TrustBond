import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart';
import '../../config/theme.dart';
import '../../providers/report_provider.dart';
import '../../services/location_service.dart';

class LocationScreen extends StatefulWidget {
  const LocationScreen({super.key});

  @override
  State<LocationScreen> createState() => _LocationScreenState();
}

class _LocationScreenState extends State<LocationScreen> {
  final LocationService _locationService = LocationService();
  bool _isLoading = false;
  bool _hasError = false;
  String _errorMessage = '';
  double _latitude = -1.4999; // Musanze center
  double _longitude = 29.6349;
  String _address = 'Musanze, Northern Province';
  String _district = 'Musanze';
  double? _accuracy;
  bool _isInRwanda = true;

  @override
  void initState() {
    super.initState();
    _initializeLocation();
  }

  Future<void> _initializeLocation() async {
    final reportProvider = context.read<ReportProvider>();
    if (reportProvider.latitude != null) {
      setState(() {
        _latitude = reportProvider.latitude!;
        _longitude = reportProvider.longitude!;
        _address = reportProvider.address;
      });
    } else {
      // Auto-detect location on first load
      await _detectLocation();
    }
  }

  Future<void> _detectLocation() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      // Check permissions
      final status = await _locationService.checkPermissions();
      
      if (status == LocationPermissionStatus.serviceDisabled) {
        _showLocationServiceDialog();
        setState(() {
          _isLoading = false;
          _hasError = true;
          _errorMessage = 'Location services are disabled';
        });
        return;
      }
      
      if (status == LocationPermissionStatus.denied) {
        final granted = await _locationService.requestPermission();
        if (!granted) {
          setState(() {
            _isLoading = false;
            _hasError = true;
            _errorMessage = 'Location permission denied';
          });
          return;
        }
      }
      
      if (status == LocationPermissionStatus.deniedForever) {
        _showPermissionSettingsDialog();
        setState(() {
          _isLoading = false;
          _hasError = true;
          _errorMessage = 'Location permission permanently denied';
        });
        return;
      }

      // Get current position
      final position = await _locationService.getCurrentPosition();
      
      // Validate location is in Rwanda
      _isInRwanda = _locationService.isInRwanda(
        position.latitude,
        position.longitude,
      );
      
      // Get address
      final address = await _locationService.getAddressFromCoordinates(
        position.latitude,
        position.longitude,
      );
      
      // Get district
      final district = _locationService.getDistrictFromCoordinates(
        position.latitude,
        position.longitude,
      );

      setState(() {
        _latitude = position.latitude;
        _longitude = position.longitude;
        _address = address;
        _district = district;
        _accuracy = position.accuracy;
        _isLoading = false;
      });

      if (!_isInRwanda) {
        _showLocationWarning();
      }

    } on LocationException catch (e) {
      setState(() {
        _isLoading = false;
        _hasError = true;
        _errorMessage = e.message;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _hasError = true;
        _errorMessage = 'Failed to detect location';
      });
    }
  }

  void _showLocationServiceDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Location Services Disabled'),
        content: const Text(
          'Please enable location services to detect your current location accurately.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _locationService.openLocationSettings();
            },
            child: const Text('Open Settings'),
          ),
        ],
      ),
    );
  }

  void _showPermissionSettingsDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Permission Required'),
        content: const Text(
          'Location permission is required to detect your position. Please enable it in app settings.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _locationService.openAppSettings();
            },
            child: const Text('Open Settings'),
          ),
        ],
      ),
    );
  }

  void _showLocationWarning() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
          'Location appears to be outside Rwanda. Please verify.',
        ),
        backgroundColor: AppTheme.warningColor,
        action: SnackBarAction(
          label: 'OK',
          textColor: Colors.white,
          onPressed: () {},
        ),
      ),
    );
  }

  void _confirmLocation() {
    context.read<ReportProvider>().setLocation(_latitude, _longitude, _address);
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirm Location'),
      ),
      body: Column(
        children: [
          // Map placeholder
          Expanded(
            flex: 3,
            child: Stack(
              children: [
                // Mock map background
                Container(
                  decoration: BoxDecoration(
                    color: AppTheme.backgroundColor,
                    image: DecorationImage(
                      image: const NetworkImage(
                        'https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/-1.9403,29.8739,13,0/600x400?access_token=placeholder',
                      ),
                      fit: BoxFit.cover,
                      onError: (_, __) {},
                    ),
                  ),
                  child: Center(
                    child: Container(
                      width: double.infinity,
                      height: double.infinity,
                      color: AppTheme.primaryColor.withOpacity(0.05),
                      child: CustomPaint(
                        painter: _MapGridPainter(),
                      ),
                    ),
                  ),
                ),
                // Center pin
                Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.accentColor,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: AppTheme.accentColor.withOpacity(0.3),
                              blurRadius: 10,
                              spreadRadius: 2,
                            ),
                          ],
                        ),
                        child: const Icon(
                          Icons.location_on,
                          color: Colors.white,
                          size: 32,
                        ),
                      ),
                      Container(
                        width: 4,
                        height: 20,
                        decoration: BoxDecoration(
                          color: AppTheme.accentColor,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      Container(
                        width: 12,
                        height: 6,
                        decoration: BoxDecoration(
                          color: Colors.black26,
                          borderRadius: BorderRadius.circular(6),
                        ),
                      ),
                    ],
                  ),
                ),
                // Loading overlay
                if (_isLoading)
                  Container(
                    color: Colors.black26,
                    child: const Center(
                      child: CircularProgressIndicator(
                        color: Colors.white,
                      ),
                    ),
                  ),
                // Drag instruction
                Positioned(
                  top: 16,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.black87,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            _isInRwanda ? Icons.check_circle : Icons.warning,
                            color: _isInRwanda ? Colors.green : Colors.orange,
                            size: 16,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _isInRwanda 
                              ? 'Location: $_district' 
                              : 'Outside Rwanda boundaries',
                            style: const TextStyle(color: Colors.white, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                // GPS indicator
                Positioned(
                  top: 16,
                  right: 16,
                  child: GestureDetector(
                    onTap: _detectLocation,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        _hasError ? Icons.gps_off : Icons.gps_fixed,
                        color: _hasError ? AppTheme.errorColor : AppTheme.successColor,
                        size: 20,
                      ),
                    ),
                  ),
                ),
                // Accuracy indicator
                if (_accuracy != null)
                  Positioned(
                    bottom: 16,
                    left: 16,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.precision_manufacturing,
                            size: 14,
                            color: _accuracy! < 50 ? AppTheme.successColor : AppTheme.warningColor,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '±${_accuracy!.toStringAsFixed(0)}m',
                            style: const TextStyle(fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
          // Location details
          Expanded(
            flex: 2,
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black12,
                    blurRadius: 10,
                    offset: Offset(0, -5),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Address display
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.backgroundColor,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(
                            Icons.location_on,
                            color: AppTheme.primaryColor,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Selected Location',
                                style: TextStyle(
                                  color: AppTheme.textSecondary,
                                  fontSize: 12,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _address,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 16,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Coordinates
                  Row(
                    children: [
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppTheme.backgroundColor,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Latitude',
                                style: TextStyle(
                                  color: AppTheme.textSecondary,
                                  fontSize: 12,
                                ),
                              ),
                              Text(
                                _latitude.toStringAsFixed(6),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppTheme.backgroundColor,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Longitude',
                                style: TextStyle(
                                  color: AppTheme.textSecondary,
                                  fontSize: 12,
                                ),
                              ),
                              Text(
                                _longitude.toStringAsFixed(6),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  // Buttons
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _isLoading ? null : _detectLocation,
                          icon: const Icon(Icons.my_location),
                          label: const Text('Re-detect'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        flex: 2,
                        child: ElevatedButton.icon(
                          onPressed: _isLoading ? null : _confirmLocation,
                          icon: const Icon(Icons.check),
                          label: const Text('Confirm Location'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                        ),
                      ),
                    ],
                  ),
                  // Error message
                  if (_hasError)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        _errorMessage,
                        style: const TextStyle(
                          color: AppTheme.errorColor,
                          fontSize: 12,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MapGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.primaryColor.withOpacity(0.1)
      ..strokeWidth = 1;

    // Draw grid lines
    const spacing = 40.0;
    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }

    // Draw some mock roads
    final roadPaint = Paint()
      ..color = AppTheme.textSecondary.withOpacity(0.2)
      ..strokeWidth = 3;

    canvas.drawLine(
      Offset(0, size.height / 2),
      Offset(size.width, size.height / 2),
      roadPaint,
    );
    canvas.drawLine(
      Offset(size.width / 2, 0),
      Offset(size.width / 2, size.height),
      roadPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
