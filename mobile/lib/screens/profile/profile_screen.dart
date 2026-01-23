import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/app_provider.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final appProvider = Provider.of<AppProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          TextButton(
            onPressed: _saveProfile,
            child: const Text('Save'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Profile Avatar
              Center(
                child: Stack(
                  children: [
                    CircleAvatar(
                      radius: 60,
                      backgroundColor: AppTheme.primaryColor.withOpacity(0.1),
                      child: appProvider.isAnonymous
                          ? const Icon(
                              Icons.person_off,
                              size: 60,
                              color: AppTheme.textSecondary,
                            )
                          : const Icon(
                              Icons.person,
                              size: 60,
                              color: AppTheme.primaryColor,
                            ),
                    ),
                    if (!appProvider.isAnonymous)
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryColor,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: InkWell(
                            onTap: () {
                              // Change photo
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Photo picker would open here'),
                                  duration: Duration(seconds: 1),
                                ),
                              );
                            },
                            child: const Icon(
                              Icons.camera_alt,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Anonymous Mode Card
              Card(
                color: appProvider.isAnonymous
                    ? AppTheme.accentColor.withOpacity(0.1)
                    : null,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            appProvider.isAnonymous
                                ? Icons.visibility_off
                                : Icons.visibility,
                            color: appProvider.isAnonymous
                                ? AppTheme.accentColor
                                : AppTheme.primaryColor,
                          ),
                          const SizedBox(width: 12),
                          const Expanded(
                            child: Text(
                              'Anonymous Mode',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                          ),
                          Switch(
                            value: appProvider.isAnonymous,
                            onChanged: (value) {
                              appProvider.setAnonymous(value);
                            },
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        appProvider.isAnonymous
                            ? 'Your identity is hidden. Reports will be submitted anonymously.'
                            : 'Your profile information may be associated with your reports.',
                        style: TextStyle(
                          color: appProvider.isAnonymous
                              ? AppTheme.accentColor
                              : AppTheme.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Personal Information Section
              const Text(
                'Personal Information',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                appProvider.isAnonymous
                    ? 'Not visible when anonymous mode is enabled'
                    : 'Optional - helps us serve you better',
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 16),

              // Name field
              TextFormField(
                controller: _nameController,
                enabled: !appProvider.isAnonymous,
                decoration: InputDecoration(
                  labelText: 'Full Name',
                  hintText: 'Enter your name (optional)',
                  prefixIcon: const Icon(Icons.person_outline),
                  filled: appProvider.isAnonymous,
                  fillColor: appProvider.isAnonymous
                      ? Colors.grey.withOpacity(0.1)
                      : null,
                ),
              ),
              const SizedBox(height: 16),

              // Email field
              TextFormField(
                controller: _emailController,
                enabled: !appProvider.isAnonymous,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  labelText: 'Email Address',
                  hintText: 'Enter your email (optional)',
                  prefixIcon: const Icon(Icons.email_outlined),
                  filled: appProvider.isAnonymous,
                  fillColor: appProvider.isAnonymous
                      ? Colors.grey.withOpacity(0.1)
                      : null,
                ),
                validator: (value) {
                  if (value != null && value.isNotEmpty) {
                    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
                    if (!emailRegex.hasMatch(value)) {
                      return 'Please enter a valid email';
                    }
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // Phone field
              TextFormField(
                controller: _phoneController,
                enabled: !appProvider.isAnonymous,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(
                  labelText: 'Phone Number',
                  hintText: 'Enter your phone (optional)',
                  prefixIcon: const Icon(Icons.phone_outlined),
                  prefixText: '+250 ',
                  filled: appProvider.isAnonymous,
                  fillColor: appProvider.isAnonymous
                      ? Colors.grey.withOpacity(0.1)
                      : null,
                ),
                validator: (value) {
                  if (value != null && value.isNotEmpty) {
                    if (value.length < 9) {
                      return 'Please enter a valid phone number';
                    }
                  }
                  return null;
                },
              ),
              const SizedBox(height: 32),

              // Privacy notice
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.infoColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: AppTheme.infoColor.withOpacity(0.3),
                  ),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.shield,
                      color: AppTheme.infoColor,
                      size: 20,
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Privacy Notice',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: AppTheme.infoColor,
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            'Your personal information is securely stored and will never be shared without your consent. '
                            'You can use the app completely anonymously.',
                            style: TextStyle(
                              fontSize: 13,
                              height: 1.4,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // Notification Preferences
              const Text(
                'Notification Preferences',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),

              _NotificationTile(
                title: 'Report Status Updates',
                subtitle: 'Get notified when your report status changes',
                value: appProvider.notificationsEnabled,
                onChanged: (value) {
                  appProvider.setNotificationsEnabled(value);
                },
              ),
              _NotificationTile(
                title: 'Community Alerts',
                subtitle: 'Receive alerts about incidents in your area',
                value: true,
                onChanged: (value) {},
              ),
              _NotificationTile(
                title: 'Safety Tips',
                subtitle: 'Get safety tips and recommendations',
                value: true,
                onChanged: (value) {},
              ),
              const SizedBox(height: 32),

              // Statistics
              const Text(
                'Your Statistics',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),

              Row(
                children: [
                  Expanded(
                    child: _StatCard(
                      icon: Icons.description,
                      value: '5',
                      label: 'Total Reports',
                      color: AppTheme.primaryColor,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _StatCard(
                      icon: Icons.verified,
                      value: '3',
                      label: 'Verified',
                      color: AppTheme.successColor,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _StatCard(
                      icon: Icons.pending,
                      value: '2',
                      label: 'Pending',
                      color: AppTheme.warningColor,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // Delete Account Button
              Center(
                child: TextButton.icon(
                  onPressed: () => _showDeleteAccountDialog(context),
                  icon: const Icon(Icons.delete_forever, color: AppTheme.accentColor),
                  label: const Text(
                    'Delete Account',
                    style: TextStyle(color: AppTheme.accentColor),
                  ),
                ),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  void _saveProfile() {
    if (_formKey.currentState!.validate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Profile saved successfully'),
          backgroundColor: AppTheme.successColor,
        ),
      );
      Navigator.pop(context);
    }
  }

  void _showDeleteAccountDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning, color: AppTheme.accentColor),
            SizedBox(width: 8),
            Text('Delete Account'),
          ],
        ),
        content: const Text(
          'Are you sure you want to delete your account? This action cannot be undone. '
          'All your data and report history will be permanently deleted.',
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
                  content: Text('Account deletion would be processed here'),
                  backgroundColor: AppTheme.accentColor,
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.accentColor,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _NotificationTile({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: SwitchListTile(
        title: Text(title),
        subtitle: Text(
          subtitle,
          style: const TextStyle(fontSize: 13),
        ),
        value: value,
        onChanged: onChanged,
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _StatCard({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: color.withOpacity(0.8),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
