import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/report_provider.dart';

class LocationScreen extends StatefulWidget {
  const LocationScreen({super.key});

  @override
  State<LocationScreen> createState() => _LocationScreenState();
}

class _LocationScreenState extends State<LocationScreen> {
  bool _isLoading = false;
  double _latitude = -1.9403;
  double _longitude = 29.8739;
  String _address = 'Kigali, Rwanda';

  @override
  void initState() {
    super.initState();
    final reportProvider = context.read<ReportProvider>();
    if (reportProvider.latitude != null) {
      _latitude = reportProvider.latitude!;
      _longitude = reportProvider.longitude!;
      _address = reportProvider.address;
    }
  }

  Future<void> _redetectLocation() async {
    setState(() => _isLoading = true);
    
    // Simulate GPS detection
    await Future.delayed(const Duration(seconds: 2));
    
    setState(() {
      _latitude = -1.9403 + (DateTime.now().millisecond / 10000);
      _longitude = 29.8739 + (DateTime.now().millisecond / 10000);
      _address = 'KN 5 Rd, Nyarugenge, Kigali';
      _isLoading = false;
    });
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
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.touch_app, color: Colors.white, size: 16),
                          SizedBox(width: 8),
                          Text(
                            'Drag pin to adjust location',
                            style: TextStyle(color: Colors.white, fontSize: 12),
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
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.gps_fixed,
                      color: AppTheme.successColor,
                      size: 20,
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
                          onPressed: _isLoading ? null : _redetectLocation,
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
