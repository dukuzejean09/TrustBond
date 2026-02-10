import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../config/theme.dart';
import '../../models/notification_model.dart';
import '../../providers/report_provider.dart';
import '../../services/api_service.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen>
    with SingleTickerProviderStateMixin {
  List<NotificationModel> _notifications = [];
  List<NotificationModel> _policeAlerts = [];
  Set<String> _readNotificationIds = {};
  bool _isLoading = false;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadReadNotifications();
    _loadAllNotifications();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadReadNotifications() async {
    final prefs = await SharedPreferences.getInstance();
    final readIds = prefs.getStringList('read_notification_ids') ?? [];
    setState(() {
      _readNotificationIds = readIds.toSet();
    });
  }

  Future<void> _saveReadNotifications() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
        'read_notification_ids', _readNotificationIds.toList());
  }

  Future<void> _loadAllNotifications() async {
    setState(() => _isLoading = true);

    // Load police alerts from API
    await _loadPoliceAlerts();

    // Load report notifications
    _loadReportNotifications();

    setState(() => _isLoading = false);
  }

  Future<void> _loadPoliceAlerts() async {
    try {
      final result = await ApiService.getAlerts(perPage: 50);
      if (result['success'] && result['data'] != null) {
        final alertsData = result['data']['alerts'] as List? ?? [];
        setState(() {
          _policeAlerts = alertsData
              .map((alert) => NotificationModel.fromAlert(alert))
              .map((notification) => NotificationModel(
                    id: notification.id,
                    title: notification.title,
                    message: notification.message,
                    type: notification.type,
                    createdAt: notification.createdAt,
                    isRead: _readNotificationIds.contains(notification.id),
                    alertType: notification.alertType,
                    isNationwide: notification.isNationwide,
                    district: notification.district,
                  ))
              .toList();
        });
      }
    } catch (e) {
      debugPrint('Error loading police alerts: $e');
    }
  }

  void _loadReportNotifications() {
    final reportProvider = context.read<ReportProvider>();
    final reports = reportProvider.myReports;

    _notifications = reports.map((report) {
      String statusMessage;
      NotificationType type;

      switch (report.status.name) {
        case 'submitted':
          statusMessage =
              'Your report has been submitted successfully and is pending review.';
          type = NotificationType.statusUpdate;
          break;
        case 'underReview':
          statusMessage =
              'Your report is now under review by the authorities.';
          type = NotificationType.statusUpdate;
          break;
        case 'verified':
          statusMessage =
              'Your report has been verified and action is being taken.';
          type = NotificationType.announcement;
          break;
        case 'closed':
          statusMessage = 'Your report has been resolved and closed.';
          type = NotificationType.announcement;
          break;
        default:
          statusMessage = 'Your report status has been updated.';
          type = NotificationType.statusUpdate;
      }

      return NotificationModel(
        id: 'NOT_${report.id}',
        title: 'Report #${report.id} - ${report.status.name.toUpperCase()}',
        message: statusMessage,
        type: type,
        createdAt: report.submittedAt,
        isRead: _readNotificationIds.contains('NOT_${report.id}'),
        reportId: report.id,
      );
    }).toList();

    _notifications.sort((a, b) => b.createdAt.compareTo(a.createdAt));
  }

  void _markAsRead(String id) {
    setState(() {
      _readNotificationIds.add(id);
      _loadReportNotifications();
      _policeAlerts = _policeAlerts
          .map((n) => n.id == id
              ? NotificationModel(
                  id: n.id,
                  title: n.title,
                  message: n.message,
                  type: n.type,
                  createdAt: n.createdAt,
                  isRead: true,
                  alertType: n.alertType,
                  isNationwide: n.isNationwide,
                  district: n.district,
                )
              : n)
          .toList();
    });
    _saveReadNotifications();
  }

  void _markAllAsRead() {
    setState(() {
      _readNotificationIds.addAll(_notifications.map((n) => n.id));
      _readNotificationIds.addAll(_policeAlerts.map((n) => n.id));
      _loadReportNotifications();
      _policeAlerts = _policeAlerts
          .map((n) => NotificationModel(
                id: n.id,
                title: n.title,
                message: n.message,
                type: n.type,
                createdAt: n.createdAt,
                isRead: true,
                alertType: n.alertType,
                isNationwide: n.isNationwide,
                district: n.district,
              ))
          .toList();
    });
    _saveReadNotifications();
  }

  int get _totalUnreadCount {
    return _notifications.where((n) => !n.isRead).length +
        _policeAlerts.where((n) => !n.isRead).length;
  }

  int get _alertsUnreadCount {
    return _policeAlerts.where((n) => !n.isRead).length;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          tabs: [
            Tab(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.campaign, size: 20),
                  const SizedBox(width: 8),
                  const Text('Police Alerts'),
                  if (_alertsUnreadCount > 0) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.red,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '$_alertsUnreadCount',
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const Tab(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.update, size: 20),
                  SizedBox(width: 8),
                  Text('My Reports'),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: _loadAllNotifications,
            icon: const Icon(Icons.refresh),
          ),
          if (_totalUnreadCount > 0)
            TextButton(
              onPressed: _markAllAsRead,
              child: const Text(
                'Mark all read',
                style: TextStyle(color: Colors.white),
              ),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // Police Alerts Tab
                _buildPoliceAlertsTab(),
                // My Reports Tab
                _buildReportsTab(),
              ],
            ),
    );
  }

  Widget _buildPoliceAlertsTab() {
    if (_policeAlerts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.campaign_outlined,
              size: 80,
              color: AppTheme.textSecondary.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            const Text(
              'No police alerts',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppTheme.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Stay safe! No active alerts in your area.',
              style: TextStyle(color: AppTheme.textLight),
            ),
            const SizedBox(height: 24),
            OutlinedButton.icon(
              onPressed: _loadPoliceAlerts,
              icon: const Icon(Icons.refresh),
              label: const Text('Refresh'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadPoliceAlerts,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _policeAlerts.length,
        itemBuilder: (context, index) {
          final notification = _policeAlerts[index];
          return _PoliceAlertCard(
            notification: notification,
            onTap: () {
              _markAsRead(notification.id);
              _showAlertDetails(notification);
            },
          );
        },
      ),
    );
  }

  Widget _buildReportsTab() {
    return Consumer<ReportProvider>(
      builder: (context, reportProvider, child) {
        if (reportProvider.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        if (_notifications.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.notifications_none,
                  size: 80,
                  color: AppTheme.textSecondary.withOpacity(0.5),
                ),
                const SizedBox(height: 16),
                const Text(
                  'No report updates',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textSecondary,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Submit a report to receive status updates',
                  style: TextStyle(color: AppTheme.textLight),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: _notifications.length,
          itemBuilder: (context, index) {
            final notification = _notifications[index];
            return _NotificationCard(
              notification: notification,
              onTap: () {
                _markAsRead(notification.id);
                _showNotificationDetails(notification);
              },
              onDismiss: () {
                setState(() {
                  _notifications.removeAt(index);
                });
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: const Text('Notification dismissed'),
                    action: SnackBarAction(
                      label: 'Undo',
                      onPressed: () {
                        setState(() {
                          _loadReportNotifications();
                        });
                      },
                    ),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  void _showAlertDetails(NotificationModel notification) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppTheme.dividerColor,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Alert type badge
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: notification.alertColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                      color: notification.alertColor.withOpacity(0.3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(notification.alertIcon,
                        color: notification.alertColor, size: 18),
                    const SizedBox(width: 8),
                    Text(
                      notification.alertTypeLabel,
                      style: TextStyle(
                        color: notification.alertColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Title
              Text(
                notification.title,
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),

              // Location & Time
              Row(
                children: [
                  Icon(Icons.access_time,
                      size: 14, color: AppTheme.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    notification.timeAgo,
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Icon(Icons.location_on,
                      size: 14, color: AppTheme.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    notification.isNationwide
                        ? 'Nationwide'
                        : notification.district ?? 'All Areas',
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Message
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  notification.message,
                  style: const TextStyle(
                    fontSize: 15,
                    height: 1.6,
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Safety tips
              if (notification.alertType == 'emergency' ||
                  notification.alertType == 'warning') ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.orange.withOpacity(0.3)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.lightbulb_outline,
                          color: Colors.orange, size: 20),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Stay vigilant and report any suspicious activity to the police immediately.',
                          style: TextStyle(fontSize: 13, color: Colors.orange),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Close button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Got it'),
                ),
              ),
              const SizedBox(height: 12),
            ],
          ),
        );
      },
    );
  }

  void _showNotificationDetails(NotificationModel notification) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppTheme.dividerColor,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Type icon
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: notification.typeColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  notification.typeIcon,
                  color: notification.typeColor,
                  size: 28,
                ),
              ),
              const SizedBox(height: 16),

              // Title
              Text(
                notification.title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),

              // Time
              Text(
                notification.timeAgo,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 16),

              // Message
              Text(
                notification.message,
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 20),

              // Action button
              if (notification.reportId != null)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      // Navigate to report details
                    },
                    child: const Text('View Report'),
                  ),
                ),
              const SizedBox(height: 12),
            ],
          ),
        );
      },
    );
  }
}

class _PoliceAlertCard extends StatelessWidget {
  final NotificationModel notification;
  final VoidCallback onTap;

  const _PoliceAlertCard({
    required this.notification,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isEmergency = notification.alertType == 'emergency';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: notification.isRead
          ? null
          : notification.alertColor.withOpacity(0.05),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: isEmergency && !notification.isRead
            ? BorderSide(color: notification.alertColor.withOpacity(0.5), width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with type badge
              Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: notification.alertColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(notification.alertIcon,
                            color: notification.alertColor, size: 14),
                        const SizedBox(width: 4),
                        Text(
                          notification.alertTypeLabel,
                          style: TextStyle(
                            color: notification.alertColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  if (!notification.isRead)
                    Container(
                      width: 10,
                      height: 10,
                      decoration: BoxDecoration(
                        color: notification.alertColor,
                        shape: BoxShape.circle,
                      ),
                    ),
                  const SizedBox(width: 8),
                  Text(
                    notification.timeAgo,
                    style: const TextStyle(
                      color: AppTheme.textLight,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Title
              Text(
                notification.title,
                style: TextStyle(
                  fontWeight:
                      notification.isRead ? FontWeight.w500 : FontWeight.bold,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 6),

              // Message preview
              Text(
                notification.message,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: notification.isRead
                      ? AppTheme.textLight
                      : AppTheme.textSecondary,
                  fontSize: 13,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 10),

              // Footer with location
              Row(
                children: [
                  Icon(Icons.location_on, size: 14, color: AppTheme.textLight),
                  const SizedBox(width: 4),
                  Text(
                    notification.isNationwide
                        ? 'Nationwide Alert'
                        : notification.district ?? 'All Areas',
                    style: const TextStyle(
                      color: AppTheme.textLight,
                      fontSize: 12,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    'Tap to read more →',
                    style: TextStyle(
                      color: notification.alertColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationCard extends StatelessWidget {
  final NotificationModel notification;
  final VoidCallback onTap;
  final VoidCallback onDismiss;

  const _NotificationCard({
    required this.notification,
    required this.onTap,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: Key(notification.id),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => onDismiss(),
      background: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: AppTheme.errorColor,
          borderRadius: BorderRadius.circular(16),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        child: const Icon(Icons.delete, color: Colors.white),
      ),
      child: Card(
        margin: const EdgeInsets.only(bottom: 12),
        color: notification.isRead
            ? null
            : notification.typeColor.withOpacity(0.05),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Icon
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: notification.typeColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    notification.typeIcon,
                    color: notification.typeColor,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                // Content
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              notification.title,
                              style: TextStyle(
                                fontWeight: notification.isRead
                                    ? FontWeight.normal
                                    : FontWeight.w600,
                                fontSize: 15,
                              ),
                            ),
                          ),
                          if (!notification.isRead)
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: notification.typeColor,
                                shape: BoxShape.circle,
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        notification.message,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: notification.isRead
                              ? AppTheme.textLight
                              : AppTheme.textSecondary,
                          fontSize: 13,
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        notification.timeAgo,
                        style: const TextStyle(
                          color: AppTheme.textLight,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
