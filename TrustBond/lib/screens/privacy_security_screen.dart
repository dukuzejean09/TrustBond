import 'package:flutter/material.dart';
import '../config/theme.dart';

class PrivacySecurityScreen extends StatelessWidget {
  const PrivacySecurityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      child: Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.chevron_left),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Privacy & Security', style: TextStyle(fontSize: 16)),
        backgroundColor: AppColors.surface,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.security, size: 48, color: AppColors.accent),
            const SizedBox(height: 24),
            const Text(
              'Your Data is Protected',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildSection(
              'Pseudonymous Reporting',
              'Reports are tied to a local device identity so TrustBond can score reliability without asking for your name or public profile. Your identity is pseudonymous: it is not shared publicly, but the device token is stored to prevent spam and enable trust scoring.',
            ),
            _buildSection(
              'Data Encryption',
              'Reports and evidence are protected during transfer using HTTPS and stored on secured backend services. Access is limited to authorised TrustBond and police workflows.',
            ),
            _buildSection(
              'Location Privacy',
              'Your location is captured when you submit a report so it can be routed, clustered, and investigated correctly. TrustBond does not continuously track your live movement.',
            ),
            _buildSection(
              'AI-Assisted Verification',
              'Submitted reports are scored by a machine-learning credibility model and rules engine. High-confidence reports may be verified automatically; others are queued for police review. The AI assists, but human officers retain final authority.',
            ),
            _buildSection(
              'Your Rights',
              'You can clear all locally stored data at any time from Settings → Clear All Data. You can also export your locally stored report history as a JSON file from Settings → Export My Data.',
            ),
          ],
        ),
      ),
    ),
    );
  }

  Widget _buildSection(String title, String content) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.accent2)),
          const SizedBox(height: 8),
          Text(content, style: const TextStyle(fontSize: 14, color: AppColors.muted, height: 1.5)),
        ],
      ),
    );
  }
}
