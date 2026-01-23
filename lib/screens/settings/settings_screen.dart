import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../config/routes.dart';
import '../../providers/app_provider.dart';
import '../../providers/theme_provider.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final appProvider = context.watch<AppProvider>();
    final themeProvider = context.watch<ThemeProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Privacy Section
            _SectionHeader(title: 'Privacy'),
            _SettingsTile(
              icon: Icons.visibility_off,
              title: 'Anonymous Mode Default',
              subtitle: 'Report anonymously by default',
              trailing: Switch(
                value: appProvider.isAnonymousMode,
                onChanged: appProvider.setAnonymousMode,
                activeColor: AppTheme.primaryColor,
              ),
            ),
            const SizedBox(height: 24),

            // Appearance Section
            _SectionHeader(title: 'Appearance'),
            _SettingsTile(
              icon: Icons.dark_mode,
              title: 'Dark Theme',
              subtitle: 'Switch between light and dark mode',
              trailing: Switch(
                value: themeProvider.isDarkMode,
                onChanged: (_) => themeProvider.toggleTheme(),
                activeColor: AppTheme.primaryColor,
              ),
            ),
            _SettingsTile(
              icon: Icons.language,
              title: 'Language',
              subtitle: _getLanguageName(appProvider.language),
              onTap: () => _showLanguageDialog(context, appProvider),
            ),
            const SizedBox(height: 24),

            // Notifications Section
            _SectionHeader(title: 'Notifications'),
            _SettingsTile(
              icon: Icons.notifications,
              title: 'Push Notifications',
              subtitle: 'Receive alerts and updates',
              trailing: Switch(
                value: appProvider.notificationsEnabled,
                onChanged: appProvider.setNotifications,
                activeColor: AppTheme.primaryColor,
              ),
            ),
            const SizedBox(height: 24),

            // Permissions Section
            _SectionHeader(title: 'Permissions'),
            _SettingsTile(
              icon: Icons.location_on,
              title: 'Location Services',
              subtitle: 'Required for accurate reporting',
              onTap: () => _showPermissionInfo(context, 'Location'),
            ),
            _SettingsTile(
              icon: Icons.camera_alt,
              title: 'Camera Access',
              subtitle: 'Required for evidence capture',
              onTap: () => _showPermissionInfo(context, 'Camera'),
            ),
            _SettingsTile(
              icon: Icons.mic,
              title: 'Microphone Access',
              subtitle: 'Required for audio recording',
              onTap: () => _showPermissionInfo(context, 'Microphone'),
            ),
            const SizedBox(height: 24),

            // Account Section
            _SectionHeader(title: 'Account'),
            _SettingsTile(
              icon: Icons.person,
              title: 'Profile',
              subtitle: 'Manage your profile information',
              onTap: () => Navigator.pushNamed(context, AppRoutes.profile),
            ),
            _SettingsTile(
              icon: Icons.cloud_off,
              title: 'Offline Reports',
              subtitle: 'View saved offline reports',
              onTap: () => Navigator.pushNamed(context, AppRoutes.offlineReports),
            ),
            const SizedBox(height: 24),

            // Support Section
            _SectionHeader(title: 'Support'),
            _SettingsTile(
              icon: Icons.help,
              title: 'Help & FAQ',
              subtitle: 'Get help and answers',
              onTap: () => Navigator.pushNamed(context, AppRoutes.help),
            ),
            _SettingsTile(
              icon: Icons.feedback,
              title: 'Send Feedback',
              subtitle: 'Help us improve the app',
              onTap: () => _showFeedbackDialog(context),
            ),
            _SettingsTile(
              icon: Icons.bug_report,
              title: 'Report a Bug',
              subtitle: 'Let us know about issues',
              onTap: () => _showBugReportDialog(context),
            ),
            const SizedBox(height: 24),

            // Legal Section
            _SectionHeader(title: 'Legal'),
            _SettingsTile(
              icon: Icons.privacy_tip,
              title: 'Privacy Policy',
              subtitle: 'How we handle your data',
              onTap: () => _showLegalDocument(context, 'Privacy Policy'),
            ),
            _SettingsTile(
              icon: Icons.description,
              title: 'Terms of Service',
              subtitle: 'App usage terms',
              onTap: () => _showLegalDocument(context, 'Terms of Service'),
            ),
            const SizedBox(height: 24),

            // App Info
            _SectionHeader(title: 'About'),
            _SettingsTile(
              icon: Icons.info,
              title: 'App Version',
              subtitle: '1.0.0',
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  String _getLanguageName(String code) {
    switch (code) {
      case 'en':
        return 'English';
      case 'rw':
        return 'Kinyarwanda';
      case 'fr':
        return 'French';
      default:
        return 'English';
    }
  }

  void _showLanguageDialog(BuildContext context, AppProvider appProvider) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Language'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _LanguageOption(
              title: 'English',
              isSelected: appProvider.language == 'en',
              onTap: () {
                appProvider.setLanguage('en');
                Navigator.pop(context);
              },
            ),
            _LanguageOption(
              title: 'Kinyarwanda',
              isSelected: appProvider.language == 'rw',
              onTap: () {
                appProvider.setLanguage('rw');
                Navigator.pop(context);
              },
            ),
            _LanguageOption(
              title: 'French',
              isSelected: appProvider.language == 'fr',
              onTap: () {
                appProvider.setLanguage('fr');
                Navigator.pop(context);
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showPermissionInfo(BuildContext context, String permission) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('$permission Permission'),
        content: Text(
          'This permission is required for the app to function properly. '
          'You can manage this permission in your device settings.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              // Open app settings
            },
            child: const Text('Open Settings'),
          ),
        ],
      ),
    );
  }

  void _showFeedbackDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Send Feedback'),
        content: TextField(
          controller: controller,
          maxLines: 5,
          decoration: const InputDecoration(
            hintText: 'Tell us what you think...',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Thank you for your feedback!'),
                ),
              );
            },
            child: const Text('Send'),
          ),
        ],
      ),
    );
  }

  void _showBugReportDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Report a Bug'),
        content: TextField(
          controller: controller,
          maxLines: 5,
          decoration: const InputDecoration(
            hintText: 'Describe the issue you encountered...',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Bug report submitted. Thank you!'),
                ),
              );
            },
            child: const Text('Submit'),
          ),
        ],
      ),
    );
  }

  void _showLegalDocument(BuildContext context, String title) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        expand: false,
        builder: (context, scrollController) => Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                controller: scrollController,
                padding: const EdgeInsets.all(16),
                child: Text(
                  _getLegalText(title),
                  style: const TextStyle(height: 1.6),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getLegalText(String title) {
    if (title == 'Privacy Policy') {
      return '''
Privacy Policy for Crime Report App

Last updated: January 2026

1. Information We Collect
We collect information you provide directly to us when you create reports, including location data, descriptions, and optional evidence files.

2. How We Use Your Information
Your information is used to:
- Process and track incident reports
- Improve our services
- Communicate with authorities when necessary

3. Anonymous Reporting
When you enable anonymous reporting, your personal identifying information is not stored with your report.

4. Data Security
We implement industry-standard security measures to protect your data.

5. Data Retention
Reports are retained as required by law and for service improvement purposes.

6. Your Rights
You have the right to access, correct, or delete your personal information.

7. Contact Us
For privacy concerns, contact us at privacy@crimereport.rw
''';
    } else {
      return '''
Terms of Service for Crime Report App

Last updated: January 2026

1. Acceptance of Terms
By using this app, you agree to these terms of service.

2. Use of Service
This app is intended for legitimate incident reporting only. Misuse may result in account termination.

3. User Responsibilities
- Provide accurate information
- Do not submit false reports
- Respect others' privacy

4. Prohibited Activities
- Submitting false reports
- Harassment or abuse
- Attempting to circumvent security measures

5. Limitation of Liability
We are not responsible for actions taken by authorities based on reports.

6. Changes to Terms
We may update these terms at any time. Continued use constitutes acceptance.

7. Contact
For questions, contact us at support@crimereport.rw
''';
    }
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;

  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: AppTheme.primaryColor.withOpacity(0.8),
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingsTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppTheme.primaryColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: AppTheme.primaryColor, size: 20),
        ),
        title: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        subtitle: Text(
          subtitle,
          style: const TextStyle(fontSize: 12),
        ),
        trailing: trailing ?? const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

class _LanguageOption extends StatelessWidget {
  final String title;
  final bool isSelected;
  final VoidCallback onTap;

  const _LanguageOption({
    required this.title,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(title),
      trailing: isSelected
          ? const Icon(Icons.check, color: AppTheme.primaryColor)
          : null,
      onTap: onTap,
    );
  }
}
