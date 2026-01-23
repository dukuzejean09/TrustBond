import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../config/routes.dart';
import '../../providers/app_provider.dart';
import '../../providers/report_provider.dart';
import '../notifications/notifications_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final appProvider = context.watch<AppProvider>();
    final reportProvider = context.watch<ReportProvider>();
    
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            // App Bar
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Crime Report',
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(
                              appProvider.isGpsActive
                                  ? Icons.location_on
                                  : Icons.location_off,
                              size: 16,
                              color: appProvider.isGpsActive
                                  ? AppTheme.successColor
                                  : AppTheme.textSecondary,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              appProvider.isGpsActive ? 'GPS Active' : 'GPS Inactive',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                            const SizedBox(width: 12),
                            Icon(
                              appProvider.isOnline
                                  ? Icons.wifi
                                  : Icons.wifi_off,
                              size: 16,
                              color: appProvider.isOnline
                                  ? AppTheme.successColor
                                  : AppTheme.textSecondary,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              appProvider.isOnline ? 'Online' : 'Offline',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        // Notification button
                        Stack(
                          children: [
                            IconButton(
                              onPressed: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => const NotificationsScreen(),
                                  ),
                                );
                              },
                              icon: const Icon(Icons.notifications_outlined),
                              style: IconButton.styleFrom(
                                backgroundColor: Colors.white,
                                padding: const EdgeInsets.all(12),
                              ),
                            ),
                            Positioned(
                              right: 8,
                              top: 8,
                              child: Container(
                                width: 10,
                                height: 10,
                                decoration: const BoxDecoration(
                                  color: AppTheme.accentColor,
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(width: 8),
                        // Settings button
                        IconButton(
                          onPressed: () {
                            Navigator.pushNamed(context, AppRoutes.settings);
                          },
                          icon: const Icon(Icons.settings_outlined),
                          style: IconButton.styleFrom(
                            backgroundColor: Colors.white,
                            padding: const EdgeInsets.all(12),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            // Main Report Button
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: InkWell(
                  onTap: () {
                    Navigator.pushNamed(context, AppRoutes.reportIncident);
                  },
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppTheme.accentColor, Color(0xFFFF8E8E)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.accentColor.withOpacity(0.3),
                          blurRadius: 15,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: const Icon(
                            Icons.emergency,
                            size: 40,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(width: 20),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                '🚨 Report Incident',
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Tap to report a crime or suspicious activity',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.white.withOpacity(0.9),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const Icon(
                          Icons.arrow_forward_ios,
                          color: Colors.white,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: 24)),
            // Quick Actions
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Quick Actions',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: _QuickActionCard(
                            icon: Icons.description,
                            title: 'My Reports',
                            subtitle: '${reportProvider.myReports.length} reports',
                            color: AppTheme.primaryColor,
                            onTap: () {
                              Navigator.pushNamed(context, AppRoutes.myReports);
                            },
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: _QuickActionCard(
                            icon: Icons.notifications_active,
                            title: 'Alerts',
                            subtitle: 'View community alerts',
                            color: AppTheme.warningColor,
                            onTap: () {
                              Navigator.pushNamed(context, AppRoutes.communityAlerts);
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: _QuickActionCard(
                            icon: Icons.help_outline,
                            title: 'Help',
                            subtitle: 'FAQ & Support',
                            color: AppTheme.infoColor,
                            onTap: () {
                              Navigator.pushNamed(context, AppRoutes.help);
                            },
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: _QuickActionCard(
                            icon: Icons.cloud_off,
                            title: 'Offline',
                            subtitle: '${reportProvider.offlineReports.length} saved',
                            color: AppTheme.textSecondary,
                            onTap: () {
                              Navigator.pushNamed(context, AppRoutes.offlineReports);
                            },
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: 24)),
            // Recent Activity
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Recent Reports',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    TextButton(
                      onPressed: () {
                        Navigator.pushNamed(context, AppRoutes.myReports);
                      },
                      child: const Text('View All'),
                    ),
                  ],
                ),
              ),
            ),
            // Recent Reports List
            if (reportProvider.myReports.isEmpty)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Container(
                    padding: const EdgeInsets.all(32),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Column(
                      children: [
                        Icon(
                          Icons.inbox_outlined,
                          size: 64,
                          color: AppTheme.textSecondary.withOpacity(0.5),
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'No reports yet',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Your submitted reports will appear here',
                          style: TextStyle(
                            color: AppTheme.textLight,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    if (index >= 3) return null;
                    final report = reportProvider.myReports[index];
                    return Padding(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
                      child: Card(
                        child: ListTile(
                          contentPadding: const EdgeInsets.all(16),
                          leading: Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: report.incidentType.color.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Icon(
                              report.incidentType.icon,
                              color: report.incidentType.color,
                            ),
                          ),
                          title: Text(
                            report.incidentType.name,
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 4),
                              Text(
                                report.description,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: report.statusColor.withOpacity(0.1),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      report.statusLabel,
                                      style: TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w500,
                                        color: report.statusColor,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    report.formattedDate,
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                ],
                              ),
                            ],
                          ),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () {
                            Navigator.pushNamed(
                              context,
                              AppRoutes.reportDetails,
                              arguments: report,
                            );
                          },
                        ),
                      ),
                    );
                  },
                  childCount: reportProvider.myReports.length.clamp(0, 3),
                ),
              ),
            const SliverToBoxAdapter(child: SizedBox(height: 100)),
          ],
        ),
      ),
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
