import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../config/routes.dart';
import '../../providers/report_provider.dart';
import '../../models/report_model.dart';

class OfflineReportsScreen extends StatelessWidget {
  const OfflineReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Offline Reports'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => _showInfoDialog(context),
          ),
        ],
      ),
      body: Consumer<ReportProvider>(
        builder: (context, reportProvider, _) {
          final offlineReports = reportProvider.offlineReports;

          if (offlineReports.isEmpty) {
            return _buildEmptyState(context);
          }

          return Column(
            children: [
              // Status Banner
              Container(
                padding: const EdgeInsets.all(16),
                color: AppTheme.warningColor.withOpacity(0.1),
                child: Row(
                  children: [
                    const Icon(
                      Icons.cloud_off,
                      color: AppTheme.warningColor,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Saved Offline',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: AppTheme.warningColor,
                            ),
                          ),
                          Text(
                            '${offlineReports.length} report(s) waiting to be submitted',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppTheme.warningColor.withOpacity(0.8),
                            ),
                          ),
                        ],
                      ),
                    ),
                    OutlinedButton(
                      onPressed: offlineReports.isNotEmpty
                          ? () => _submitAllReports(context, reportProvider)
                          : null,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.warningColor,
                        side: const BorderSide(color: AppTheme.warningColor),
                      ),
                      child: const Text('Submit All'),
                    ),
                  ],
                ),
              ),

              // Reports List
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: offlineReports.length,
                  itemBuilder: (context, index) {
                    return _OfflineReportCard(
                      report: offlineReports[index],
                      onEdit: () => _editReport(context, reportProvider, offlineReports[index]),
                      onSubmit: () => _submitReport(context, reportProvider, offlineReports[index]),
                      onDelete: () => _deleteReport(context, reportProvider, offlineReports[index]),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppTheme.successColor.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.cloud_done,
                size: 64,
                color: AppTheme.successColor,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'No Offline Reports',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'All your reports have been submitted!\nSaved reports will appear here when you have no internet connection.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppTheme.textSecondary,
              ),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.pushNamed(context, AppRoutes.reportIncident);
              },
              icon: const Icon(Icons.add),
              label: const Text('Create New Report'),
            ),
          ],
        ),
      ),
    );
  }

  void _showInfoDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.info, color: AppTheme.primaryColor),
            SizedBox(width: 8),
            Text('Offline Mode'),
          ],
        ),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'How it works:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text('• Reports are saved locally when you have no internet'),
            SizedBox(height: 4),
            Text('• They can be edited before submission'),
            SizedBox(height: 4),
            Text('• Submit individually or all at once when online'),
            SizedBox(height: 4),
            Text('• Delete unwanted reports anytime'),
            SizedBox(height: 16),
            Text(
              'Note: Evidence files are also saved locally.',
              style: TextStyle(
                fontSize: 13,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  void _editReport(BuildContext context, ReportProvider provider, ReportModel report) {
    // In a real app, this would navigate to edit screen
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Editing report: ${report.incidentType.name}'),
        duration: const Duration(seconds: 1),
      ),
    );
  }

  void _submitReport(BuildContext context, ReportProvider provider, ReportModel report) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Submit Report'),
        content: Text(
          'Submit this ${report.incidentType.name} report now?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              // Simulate submission
              provider.submitOfflineReport(report.id);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Report submitted successfully!'),
                  backgroundColor: AppTheme.successColor,
                ),
              );
            },
            child: const Text('Submit'),
          ),
        ],
      ),
    );
  }

  void _submitAllReports(BuildContext context, ReportProvider provider) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Submit All Reports'),
        content: Text(
          'Submit all ${provider.offlineReports.length} offline reports now?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              // Simulate submitting all
              for (var report in [...provider.offlineReports]) {
                provider.submitOfflineReport(report.id);
              }
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('All reports submitted successfully!'),
                  backgroundColor: AppTheme.successColor,
                ),
              );
            },
            child: const Text('Submit All'),
          ),
        ],
      ),
    );
  }

  void _deleteReport(BuildContext context, ReportProvider provider, ReportModel report) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.delete, color: AppTheme.accentColor),
            SizedBox(width: 8),
            Text('Delete Report'),
          ],
        ),
        content: const Text(
          'Are you sure you want to delete this report? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              provider.deleteOfflineReport(report.id);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Report deleted'),
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

class _OfflineReportCard extends StatelessWidget {
  final ReportModel report;
  final VoidCallback onEdit;
  final VoidCallback onSubmit;
  final VoidCallback onDelete;

  const _OfflineReportCard({
    required this.report,
    required this.onEdit,
    required this.onSubmit,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.warningColor.withOpacity(0.1),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppTheme.warningColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.save,
                    color: AppTheme.warningColor,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        report.incidentType.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      Text(
                        'Saved ${_formatDate(report.submittedAt)}',
                        style: TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: AppTheme.warningColor,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'DRAFT',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Content
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Description
                if (report.description.isNotEmpty) ...[
                  Text(
                    report.description,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 12),
                ],

                // Location
                Row(
                  children: [
                    const Icon(
                      Icons.location_on,
                      size: 16,
                      color: AppTheme.textSecondary,
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        report.address.isNotEmpty ? report.address : 'Location captured',
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // Evidence count
                if (report.evidenceList.isNotEmpty)
                  Row(
                    children: [
                      const Icon(
                        Icons.attachment,
                        size: 16,
                        color: AppTheme.textSecondary,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${report.evidenceList.length} evidence file(s)',
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ),

          // Actions
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: TextButton.icon(
                    onPressed: onEdit,
                    icon: const Icon(Icons.edit, size: 18),
                    label: const Text('Edit'),
                  ),
                ),
                Expanded(
                  child: TextButton.icon(
                    onPressed: onDelete,
                    icon: const Icon(
                      Icons.delete,
                      size: 18,
                      color: AppTheme.accentColor,
                    ),
                    label: const Text(
                      'Delete',
                      style: TextStyle(color: AppTheme.accentColor),
                    ),
                  ),
                ),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: onSubmit,
                    icon: const Icon(Icons.cloud_upload, size: 18),
                    label: const Text('Submit'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.successColor,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) {
      return 'just now';
    } else if (diff.inHours < 1) {
      return '${diff.inMinutes}m ago';
    } else if (diff.inDays < 1) {
      return '${diff.inHours}h ago';
    } else if (diff.inDays < 7) {
      return '${diff.inDays}d ago';
    } else {
      return '${date.day}/${date.month}/${date.year}';
    }
  }
}
