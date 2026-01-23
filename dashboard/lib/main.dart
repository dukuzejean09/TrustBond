import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'config/theme.dart';

void main() {
  runApp(const TrustBondDashboard());
}

class TrustBondDashboard extends StatelessWidget {
  const TrustBondDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TrustBond - Law Enforcement Dashboard',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/dashboard': (context) => const DashboardScreen(),
      },
    );
  }
}
