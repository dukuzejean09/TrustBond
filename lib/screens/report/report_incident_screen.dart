import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../config/theme.dart';
import '../../providers/report_provider.dart';
import '../../providers/app_provider.dart';
import 'incident_type_screen.dart';
import 'location_screen.dart';
import 'evidence_screen.dart';

class ReportIncidentScreen extends StatefulWidget {
  const ReportIncidentScreen({super.key});

  @override
  State<ReportIncidentScreen> createState() => _ReportIncidentScreenState();
}

class _ReportIncidentScreenState extends State<ReportIncidentScreen> {
  final TextEditingController _descriptionController = TextEditingController();
  final FocusNode _descriptionFocus = FocusNode();

  @override
  void initState() {
    super.initState();
    // Initialize with current location
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeReport();
    });
  }

  void _initializeReport() {
    final reportProvider = context.read<ReportProvider>();
    final appProvider = context.read<AppProvider>();
    
    // Set default location (Kigali)
    reportProvider.setLocation(-1.9403, 29.8739, 'Kigali, Rwanda');
    appProvider.setGpsActive(true);
    
    // Set anonymous mode from app settings
    reportProvider.setAnonymous(appProvider.isAnonymousMode);
    
    // Pre-fill description if exists
    if (reportProvider.description.isNotEmpty) {
      _descriptionController.text = reportProvider.description;
    }
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _descriptionFocus.dispose();
    super.dispose();
  }

  void _selectIncidentType() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const IncidentTypeScreen()),
    );
    if (result != null && mounted) {
      setState(() {});
    }
  }

  void _confirmLocation() async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const LocationScreen()),
    );
    if (mounted) setState(() {});
  }

  void _addEvidence() async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const EvidenceScreen()),
    );
    if (mounted) setState(() {});
  }

  void _proceedToReview() {
    final reportProvider = context.read<ReportProvider>();
    
    // Validation
    if (reportProvider.selectedIncidentType == null) {
      _showError('Please select an incident type');
      return;
    }
    
    if (_descriptionController.text.trim().length < 10) {
      _showError('Please provide a description (at least 10 characters)');
      return;
    }
    
    reportProvider.setDescription(_descriptionController.text.trim());
    
    Navigator.pushNamed(context, '/review-report');
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppTheme.errorColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  void _cancelReport() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Report?'),
        content: const Text('Are you sure you want to cancel? All entered information will be lost.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('No, Continue'),
          ),
          ElevatedButton(
            onPressed: () {
              context.read<ReportProvider>().resetCurrentReport();
              Navigator.pop(context);
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.errorColor,
            ),
            child: const Text('Yes, Cancel'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final reportProvider = context.watch<ReportProvider>();
    final dateFormat = DateFormat('EEE, MMM d, yyyy');
    final timeFormat = DateFormat('hh:mm a');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Incident'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: _cancelReport,
        ),
        actions: [
          if (reportProvider.selectedIncidentType != null)
            TextButton(
              onPressed: _proceedToReview,
              child: const Text(
                'Next',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Auto-captured info
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppTheme.infoColor.withOpacity(0.08),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: AppTheme.infoColor.withOpacity(0.25),
                  width: 1.5,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.info_outline, color: AppTheme.infoColor, size: 24),
                      const SizedBox(width: 10),
                      Text(
                        'Auto-captured Information',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.infoColor,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _AutoInfoRow(
                    icon: Icons.location_on,
                    label: 'Location',
                    value: reportProvider.address.isNotEmpty 
                        ? reportProvider.address 
                        : 'Detecting...',
                    onTap: _confirmLocation,
                  ),
                  const SizedBox(height: 12),
                  _AutoInfoRow(
                    icon: Icons.calendar_today,
                    label: 'Date',
                    value: dateFormat.format(reportProvider.incidentDate),
                    onTap: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: reportProvider.incidentDate,
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now(),
                      );
                      if (date != null) {
                        reportProvider.setIncidentDate(date);
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  _AutoInfoRow(
                    icon: Icons.access_time,
                    label: 'Time',
                    value: timeFormat.format(DateTime(
                      2024, 1, 1,
                      reportProvider.incidentTime.hour,
                      reportProvider.incidentTime.minute,
                    )),
                    onTap: () async {
                      final time = await showTimePicker(
                        context: context,
                        initialTime: reportProvider.incidentTime,
                      );
                      if (time != null) {
                        reportProvider.setIncidentTime(time);
                      }
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // Incident Type Selection
            Text(
              'Incident Type *',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 16),
            InkWell(
              onTap: _selectIncidentType,
              borderRadius: BorderRadius.circular(16),
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: reportProvider.selectedIncidentType != null
                        ? reportProvider.selectedIncidentType!.color
                        : AppTheme.dividerColor,
                    width: reportProvider.selectedIncidentType != null ? 2.5 : 1.5,
                  ),
                  boxShadow: [
                    if (reportProvider.selectedIncidentType != null)
                      BoxShadow(
                        color: reportProvider.selectedIncidentType!.color.withOpacity(0.15),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                  ],
                ),
                child: Row(
                  children: [
                    if (reportProvider.selectedIncidentType != null) ...[
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: reportProvider.selectedIncidentType!.color.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(
                          reportProvider.selectedIncidentType!.icon,
                          color: reportProvider.selectedIncidentType!.color,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              reportProvider.selectedIncidentType!.name,
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 16,
                              ),
                            ),
                            Text(
                              reportProvider.selectedIncidentType!.description,
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                    ] else ...[
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppTheme.backgroundColor,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(
                          Icons.category_outlined,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'Select incident type',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ],
                    const Icon(Icons.chevron_right, color: AppTheme.textSecondary),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Description
            Text(
              'Description *',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descriptionController,
              focusNode: _descriptionFocus,
              maxLines: 5,
              maxLength: 1000,
              decoration: InputDecoration(
                hintText: 'Describe what happened in detail...',
                alignLabelWithHint: true,
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onChanged: (value) {
                reportProvider.setDescription(value);
              },
            ),
            const SizedBox(height: 24),

            // Anonymous Toggle
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: reportProvider.isAnonymous
                          ? AppTheme.successColor.withOpacity(0.1)
                          : AppTheme.backgroundColor,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      reportProvider.isAnonymous
                          ? Icons.visibility_off
                          : Icons.visibility,
                      color: reportProvider.isAnonymous
                          ? AppTheme.successColor
                          : AppTheme.textSecondary,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Anonymous Report',
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          reportProvider.isAnonymous
                              ? 'Your identity will be protected'
                              : 'Your identity may be visible',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  Switch(
                    value: reportProvider.isAnonymous,
                    onChanged: reportProvider.setAnonymous,
                    activeColor: AppTheme.successColor,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Evidence Section
            Text(
              'Add Evidence (Optional)',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _EvidenceButton(
                    icon: Icons.camera_alt,
                    label: 'Photo',
                    count: reportProvider.evidenceList
                        .where((e) => e.type.name == 'photo')
                        .length,
                    onTap: _addEvidence,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _EvidenceButton(
                    icon: Icons.videocam,
                    label: 'Video',
                    count: reportProvider.evidenceList
                        .where((e) => e.type.name == 'video')
                        .length,
                    onTap: _addEvidence,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _EvidenceButton(
                    icon: Icons.mic,
                    label: 'Audio',
                    count: reportProvider.evidenceList
                        .where((e) => e.type.name == 'audio')
                        .length,
                    onTap: _addEvidence,
                  ),
                ),
              ],
            ),
            
            // Evidence preview
            if (reportProvider.evidenceList.isNotEmpty) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '${reportProvider.evidenceList.length} file(s) attached',
                          style: const TextStyle(fontWeight: FontWeight.w500),
                        ),
                        TextButton(
                          onPressed: _addEvidence,
                          child: const Text('Manage'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: reportProvider.evidenceList.map((e) {
                        return Chip(
                          avatar: Text(e.icon),
                          label: Text(e.typeLabel),
                          deleteIcon: const Icon(Icons.close, size: 16),
                          onDeleted: () {
                            reportProvider.removeEvidence(
                              reportProvider.evidenceList.indexOf(e),
                            );
                          },
                        );
                      }).toList(),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 32),

            // Action Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _cancelReport,
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  flex: 2,
                  child: ElevatedButton(
                    onPressed: _proceedToReview,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: const Text('Next'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

class _AutoInfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final VoidCallback onTap;

  const _AutoInfoRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        child: Row(
          children: [
            Icon(icon, size: 22, color: AppTheme.primaryColor.withOpacity(0.8)),
            const SizedBox(width: 12),
            Text(
              '$label: ',
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 15,
                fontWeight: FontWeight.w500,
              ),
            ),
            Expanded(
              child: Text(
                value,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                  color: AppTheme.textPrimary,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const Icon(Icons.edit, size: 20, color: AppTheme.primaryColor),
          ],
        ),
      ),
    );
  }
}

class _EvidenceButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final int count;
  final VoidCallback onTap;

  const _EvidenceButton({
    required this.icon,
    required this.label,
    required this.count,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: count > 0
              ? Border.all(color: AppTheme.primaryColor, width: 2.5)
              : Border.all(color: AppTheme.dividerColor, width: 1.5),
          boxShadow: [
            if (count > 0)
              BoxShadow(
                color: AppTheme.primaryColor.withOpacity(0.12),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
          ],
        ),
        child: Column(
          children: [
            Stack(
              children: [
                Icon(icon, size: 34, color: AppTheme.primaryColor),
                if (count > 0)
                  Positioned(
                    right: -6,
                    top: -6,
                    child: Container(
                      padding: const EdgeInsets.all(6),
                      decoration: const BoxDecoration(
                        color: AppTheme.accentColor,
                        shape: BoxShape.circle,
                      ),
                      child: Text(
                        count.toString(),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
