import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../models/report_model.dart';

class ReportDetailsScreen extends StatelessWidget {
  final ReportModel? report;

  const ReportDetailsScreen({super.key, this.report});

  @override
  Widget build(BuildContext context) {
    // If report is passed via arguments
    final ReportModel? displayReport =
        report ?? ModalRoute.of(context)?.settings.arguments as ReportModel?;

    if (displayReport == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Report Details')),
        body: const Center(child: Text('Report not found')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Details'),
        actions: [
          if (displayReport.status == ReportStatus.submitted ||
              displayReport.status == ReportStatus.draft)
            PopupMenuButton(
              icon: const Icon(Icons.more_vert),
              itemBuilder: (context) => [
                const PopupMenuItem(
                  value: 'add_evidence',
                  child: Row(
                    children: [
                      Icon(Icons.attach_file, size: 20),
                      SizedBox(width: 12),
                      Text('Add Evidence'),
                    ],
                  ),
                ),
                const PopupMenuItem(
                  value: 'delete',
                  child: Row(
                    children: [
                      Icon(Icons.delete, size: 20, color: AppTheme.errorColor),
                      SizedBox(width: 12),
                      Text('Delete', style: TextStyle(color: AppTheme.errorColor)),
                    ],
                  ),
                ),
              ],
              onSelected: (value) {
                if (value == 'delete') {
                  _showDeleteDialog(context);
                }
              },
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Report ID & Status Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    displayReport.statusColor,
                    displayReport.statusColor.withOpacity(0.8),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      displayReport.statusIcon,
                      color: Colors.white,
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Report ID',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                          ),
                        ),
                        Text(
                          displayReport.id,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      displayReport.statusLabel,
                      style: TextStyle(
                        color: displayReport.statusColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Status Timeline
            _buildStatusTimeline(displayReport),
            const SizedBox(height: 24),

            // Incident Type
            _DetailSection(
              title: 'Incident Type',
              icon: Icons.category,
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: displayReport.incidentType.color.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      displayReport.incidentType.icon,
                      color: displayReport.incidentType.color,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          displayReport.incidentType.name,
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          displayReport.incidentType.description,
                          style: const TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Description
            _DetailSection(
              title: 'Description',
              icon: Icons.description,
              child: Text(
                displayReport.description,
                style: const TextStyle(
                  height: 1.6,
                  fontSize: 15,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Location
            _DetailSection(
              title: 'Location',
              icon: Icons.location_on,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Mini map
                  Container(
                    height: 150,
                    decoration: BoxDecoration(
                      color: AppTheme.backgroundColor,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Stack(
                      children: [
                        CustomPaint(
                          size: const Size(double.infinity, 150),
                          painter: _MapGridPainter(),
                        ),
                        const Center(
                          child: Icon(
                            Icons.location_on,
                            color: AppTheme.accentColor,
                            size: 40,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.place, size: 18, color: AppTheme.textSecondary),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          displayReport.address,
                          style: const TextStyle(fontWeight: FontWeight.w500),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Lat: ${displayReport.latitude.toStringAsFixed(6)}, Lng: ${displayReport.longitude.toStringAsFixed(6)}',
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Date & Time
            _DetailSection(
              title: 'Date & Time',
              icon: Icons.access_time,
              child: Row(
                children: [
                  Expanded(
                    child: _InfoCard(
                      icon: Icons.calendar_today,
                      label: 'Date',
                      value: displayReport.formattedDate,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _InfoCard(
                      icon: Icons.schedule,
                      label: 'Time',
                      value: displayReport.formattedTime,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Evidence
            _DetailSection(
              title: 'Evidence (${displayReport.evidenceList.length})',
              icon: Icons.attach_file,
              child: displayReport.evidenceList.isEmpty
                  ? Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: AppTheme.backgroundColor,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.attach_file, color: AppTheme.textLight),
                          SizedBox(width: 8),
                          Text(
                            'No evidence attached',
                            style: TextStyle(color: AppTheme.textSecondary),
                          ),
                        ],
                      ),
                    )
                  : Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: displayReport.evidenceList.map((evidence) {
                        return Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: AppTheme.backgroundColor,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(evidence.icon, style: const TextStyle(fontSize: 28)),
                              const SizedBox(height: 4),
                              Text(
                                evidence.typeLabel,
                                style: const TextStyle(
                                  fontSize: 11,
                                  color: AppTheme.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
            ),
            const SizedBox(height: 16),

            // Privacy
            _DetailSection(
              title: 'Privacy',
              icon: Icons.shield,
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: displayReport.isAnonymous
                          ? AppTheme.successColor.withOpacity(0.1)
                          : AppTheme.warningColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      displayReport.isAnonymous
                          ? Icons.visibility_off
                          : Icons.visibility,
                      color: displayReport.isAnonymous
                          ? AppTheme.successColor
                          : AppTheme.warningColor,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    displayReport.isAnonymous
                        ? 'Anonymous Report'
                        : 'Non-Anonymous Report',
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Action Buttons
            if (displayReport.status == ReportStatus.submitted ||
                displayReport.status == ReportStatus.underReview)
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () {
                    // Add more evidence
                  },
                  icon: const Icon(Icons.add_a_photo),
                  label: const Text('Add More Evidence'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusTimeline(ReportModel report) {
    final statuses = [
      {'status': 'Submitted', 'icon': Icons.send, 'done': true},
      {
        'status': 'Under Review',
        'icon': Icons.pending,
        'done': report.status == ReportStatus.underReview ||
            report.status == ReportStatus.verified ||
            report.status == ReportStatus.closed
      },
      {
        'status': 'Verified',
        'icon': Icons.verified,
        'done': report.status == ReportStatus.verified ||
            report.status == ReportStatus.closed
      },
      {'status': 'Closed', 'icon': Icons.check_circle, 'done': report.status == ReportStatus.closed},
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.timeline, size: 18, color: AppTheme.primaryColor),
              SizedBox(width: 8),
              Text(
                'Status Timeline',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: statuses.asMap().entries.map((entry) {
              final index = entry.key;
              final status = entry.value;
              final isDone = status['done'] as bool;
              final isLast = index == statuses.length - 1;

              return Expanded(
                child: Row(
                  children: [
                    Column(
                      children: [
                        Container(
                          width: 32,
                          height: 32,
                          decoration: BoxDecoration(
                            color: isDone
                                ? AppTheme.successColor
                                : AppTheme.backgroundColor,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            status['icon'] as IconData,
                            size: 16,
                            color: isDone ? Colors.white : AppTheme.textLight,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          status['status'] as String,
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: isDone ? FontWeight.w600 : FontWeight.normal,
                            color: isDone
                                ? AppTheme.textPrimary
                                : AppTheme.textLight,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                    if (!isLast)
                      Expanded(
                        child: Container(
                          height: 2,
                          margin: const EdgeInsets.only(bottom: 20),
                          color: isDone
                              ? AppTheme.successColor
                              : AppTheme.dividerColor,
                        ),
                      ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  void _showDeleteDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Report?'),
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
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.errorColor,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}

class _DetailSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final Widget child;

  const _DetailSection({
    required this.title,
    required this.icon,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: AppTheme.primaryColor),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoCard({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppTheme.textSecondary),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppTheme.textSecondary,
                ),
              ),
              Text(
                value,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MapGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.primaryColor.withOpacity(0.1)
      ..strokeWidth = 1;

    const spacing = 20.0;
    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
