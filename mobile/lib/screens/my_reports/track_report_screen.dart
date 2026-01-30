import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../providers/report_provider.dart';

class TrackReportScreen extends StatefulWidget {
  const TrackReportScreen({super.key});

  @override
  State<TrackReportScreen> createState() => _TrackReportScreenState();
}

class _TrackReportScreenState extends State<TrackReportScreen> {
  final TextEditingController _trackingCodeController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _trackingCodeController.dispose();
    super.dispose();
  }

  void _trackReport() async {
    if (!_formKey.currentState!.validate()) return;

    final reportProvider = context.read<ReportProvider>();
    final result = await reportProvider.trackReportByCode(
      _trackingCodeController.text.trim().toUpperCase(),
    );

    if (result == null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(reportProvider.error ?? 'Report not found'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final reportProvider = context.watch<ReportProvider>();
    final trackedStatus = reportProvider.trackedReportStatus;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Track Report'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppTheme.primaryColor,
                    AppTheme.primaryColor.withOpacity(0.8),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Row(
                children: [
                  Icon(
                    Icons.track_changes,
                    color: Colors.white,
                    size: 40,
                  ),
                  SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Track Your Report',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Enter your tracking code to check the status of your anonymous report',
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.white70,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Tracking Code Input
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Tracking Code',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: _trackingCodeController,
                    textCapitalization: TextCapitalization.characters,
                    decoration: InputDecoration(
                      hintText: 'e.g., ANON-A1B2C3D4',
                      prefixIcon: const Icon(Icons.vpn_key),
                      suffixIcon: IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _trackingCodeController.clear();
                          reportProvider.clearTrackedStatus();
                        },
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Please enter a tracking code';
                      }
                      if (!value.toUpperCase().startsWith('ANON-')) {
                        return 'Invalid tracking code format';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: reportProvider.isLoading ? null : _trackReport,
                      icon: reportProvider.isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.search),
                      label: Text(
                        reportProvider.isLoading ? 'Searching...' : 'Track Report',
                      ),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Results Section
            if (trackedStatus != null) ...[
              const SizedBox(height: 32),
              const Divider(),
              const SizedBox(height: 24),
              
              const Text(
                'Report Status',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),

              // Status Card
              Container(
                padding: const EdgeInsets.all(20),
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
                  children: [
                    _StatusInfoRow(
                      icon: Icons.confirmation_number,
                      label: 'Report Number',
                      value: trackedStatus['reportNumber'] ?? 'N/A',
                    ),
                    const Divider(height: 24),
                    _StatusInfoRow(
                      icon: Icons.category,
                      label: 'Category',
                      value: _formatCategory(trackedStatus['category']),
                    ),
                    const Divider(height: 24),
                    _StatusInfoRow(
                      icon: Icons.flag,
                      label: 'Status',
                      value: _formatStatus(trackedStatus['status']),
                      valueColor: _getStatusColor(trackedStatus['status']),
                    ),
                    const Divider(height: 24),
                    _StatusInfoRow(
                      icon: Icons.calendar_today,
                      label: 'Submitted On',
                      value: _formatDate(trackedStatus['createdAt']),
                    ),
                    if (trackedStatus['resolutionNotes'] != null) ...[
                      const Divider(height: 24),
                      _StatusInfoRow(
                        icon: Icons.notes,
                        label: 'Resolution Notes',
                        value: trackedStatus['resolutionNotes'],
                      ),
                    ],
                  ],
                ),
              ),

              // Status Timeline
              if (trackedStatus['statusHistory'] != null &&
                  (trackedStatus['statusHistory'] as List).isNotEmpty) ...[
                const SizedBox(height: 24),
                const Text(
                  'Status History',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                ...((trackedStatus['statusHistory'] as List).map((history) {
                  return _StatusTimelineItem(
                    status: _formatStatus(history['status']),
                    date: _formatDate(history['timestamp']),
                    note: history['note'],
                    isLast: trackedStatus['statusHistory'].last == history,
                  );
                })),
              ],
            ],
          ],
        ),
      ),
    );
  }

  String _formatCategory(String? category) {
    if (category == null) return 'N/A';
    return category.replaceAll('_', ' ').split(' ').map((word) {
      return word.isNotEmpty
          ? '${word[0].toUpperCase()}${word.substring(1)}'
          : '';
    }).join(' ');
  }

  String _formatStatus(String? status) {
    if (status == null) return 'N/A';
    switch (status) {
      case 'pending':
        return 'Pending Review';
      case 'under_review':
        return 'Under Review';
      case 'investigating':
        return 'Investigating';
      case 'resolved':
        return 'Resolved';
      case 'closed':
        return 'Closed';
      case 'rejected':
        return 'Rejected';
      default:
        return status.replaceAll('_', ' ').split(' ').map((word) {
          return word.isNotEmpty
              ? '${word[0].toUpperCase()}${word.substring(1)}'
              : '';
        }).join(' ');
    }
  }

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'pending':
        return Colors.orange;
      case 'under_review':
        return Colors.blue;
      case 'investigating':
        return AppTheme.accentColor;
      case 'resolved':
        return Colors.green;
      case 'closed':
        return Colors.teal;
      case 'rejected':
        return Colors.red;
      default:
        return AppTheme.textSecondary;
    }
  }

  String _formatDate(String? dateStr) {
    if (dateStr == null) return 'N/A';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year} at ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr;
    }
  }
}

class _StatusInfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _StatusInfoRow({
    required this.icon,
    required this.label,
    required this.value,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: AppTheme.textSecondary),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.textSecondary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: valueColor ?? AppTheme.textPrimary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StatusTimelineItem extends StatelessWidget {
  final String status;
  final String date;
  final String? note;
  final bool isLast;

  const _StatusTimelineItem({
    required this.status,
    required this.date,
    this.note,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor,
                  shape: BoxShape.circle,
                ),
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 2,
                    color: AppTheme.primaryColor.withOpacity(0.3),
                  ),
                ),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    status,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    date,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  if (note != null && note!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      note!,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
