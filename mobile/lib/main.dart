import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/theme.dart';
import 'providers/device_provider.dart';
import 'providers/report_provider.dart';
import 'services/api_service.dart';
import 'services/device_service.dart';
import 'screens/onboarding_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const TrustBondApp());
}

class TrustBondApp extends StatelessWidget {
  const TrustBondApp({super.key});

  @override
  Widget build(BuildContext context) {
    final apiService = ApiService();
    final deviceService = DeviceService();

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => DeviceProvider(deviceService)..initialize(),
        ),
        ChangeNotifierProvider(
          create: (_) => ReportProvider(apiService),
        ),
      ],
      child: MaterialApp(
        title: 'TrustBond',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const OnboardingScreen(),
      ),
    );
  }
}
