import 'package:flutter/material.dart';

class AppTheme {
  // RNP Official Colors
  static const Color primaryNavy = Color(0xFF0D1B4C);
  static const Color accentGold = Color(0xFFFFB800);
  static const Color lightNavy = Color(0xFF1E3A6E);
  static const Color darkNavy = Color(0xFF081230);
  static const Color surfaceColor = Color(0xFFF5F7FA);
  static const Color cardColor = Colors.white;
  
  // Status Colors
  static const Color statusPending = Color(0xFFFF9800);
  static const Color statusInProgress = Color(0xFF2196F3);
  static const Color statusResolved = Color(0xFF4CAF50);
  static const Color statusRejected = Color(0xFFF44336);

  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    primaryColor: primaryNavy,
    scaffoldBackgroundColor: surfaceColor,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primaryNavy,
      primary: primaryNavy,
      secondary: accentGold,
      surface: surfaceColor,
      brightness: Brightness.light,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: primaryNavy,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: Colors.white,
      ),
    ),
    cardTheme: CardTheme(
      color: cardColor,
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryNavy,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        textStyle: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: Colors.grey.shade300),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: Colors.grey.shade300),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: primaryNavy, width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    ),
    dataTableTheme: DataTableThemeData(
      headingRowColor: WidgetStateProperty.all(primaryNavy.withOpacity(0.05)),
      headingTextStyle: const TextStyle(
        fontWeight: FontWeight.w600,
        color: primaryNavy,
      ),
    ),
  );
}
