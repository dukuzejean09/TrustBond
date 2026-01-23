import 'package:flutter/material.dart';
import '../screens/splash_screen.dart';
import '../screens/onboarding_screen.dart';
import '../screens/main_navigation.dart';
import '../screens/home/home_screen.dart';
import '../screens/report/report_incident_screen.dart';
import '../screens/report/incident_type_screen.dart';
import '../screens/report/location_screen.dart';
import '../screens/report/evidence_screen.dart';
import '../screens/report/review_screen.dart';
import '../screens/report/success_screen.dart';
import '../screens/my_reports/my_reports_screen.dart';
import '../screens/my_reports/report_details_screen.dart';
import '../screens/alerts/community_alerts_screen.dart';
import '../screens/notifications/notifications_screen.dart';
import '../screens/help/help_screen.dart';
import '../screens/settings/settings_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../screens/offline/offline_reports_screen.dart';

class AppRoutes {
  static const String splash = '/splash';
  static const String onboarding = '/onboarding';
  static const String main = '/main';
  static const String home = '/home';
  static const String reportIncident = '/report-incident';
  static const String incidentType = '/incident-type';
  static const String location = '/location';
  static const String evidence = '/evidence';
  static const String reviewReport = '/review-report';
  static const String success = '/success';
  static const String myReports = '/my-reports';
  static const String reportDetails = '/report-details';
  static const String communityAlerts = '/community-alerts';
  static const String notifications = '/notifications';
  static const String help = '/help';
  static const String settings = '/settings';
  static const String profile = '/profile';
  static const String offlineReports = '/offline-reports';

  static Map<String, WidgetBuilder> get routes {
    return {
      splash: (context) => const SplashScreen(),
      onboarding: (context) => const OnboardingScreen(),
      main: (context) => const MainNavigation(),
      home: (context) => const HomeScreen(),
      reportIncident: (context) => const ReportIncidentScreen(),
      incidentType: (context) => const IncidentTypeScreen(),
      location: (context) => const LocationScreen(),
      evidence: (context) => const EvidenceScreen(),
      reviewReport: (context) => const ReviewScreen(),
      success: (context) => const SuccessScreen(),
      myReports: (context) => const MyReportsScreen(),
      reportDetails: (context) => const ReportDetailsScreen(),
      communityAlerts: (context) => const CommunityAlertsScreen(),
      notifications: (context) => const NotificationsScreen(),
      help: (context) => const HelpScreen(),
      settings: (context) => const SettingsScreen(),
      profile: (context) => const ProfileScreen(),
      offlineReports: (context) => const OfflineReportsScreen(),
    };
  }
}
