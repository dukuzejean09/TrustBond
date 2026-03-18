import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config/theme.dart';
import 'screens/splash_screen.dart';
import 'screens/main_shell.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF080C18),
    ),
  );
  runApp(const TrustBondApp());
}

class TrustBondApp extends StatelessWidget {
  const TrustBondApp({super.key});

  static const String _introCompletedKey = 'intro_completed';
  static const String _deviceIdKey = 'device_id';

  Future<bool> _shouldShowIntro() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(_introCompletedKey) ?? false) return false;

    // Existing users (pre-flag) already have a registered device_id.
    // Skip intro to avoid showing splash on every app launch after updates.
    final existingDeviceId = prefs.getString(_deviceIdKey);
    if (existingDeviceId != null && existingDeviceId.isNotEmpty) return false;

    return true;
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TrustBond',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: FutureBuilder<bool>(
        future: _shouldShowIntro(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }
          return snapshot.data! ? const SplashScreen() : const MainShell();
        },
      ),
    );
  }
}
