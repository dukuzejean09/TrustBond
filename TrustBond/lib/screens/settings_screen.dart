import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import '../config/theme.dart';
import '../services/device_service.dart';
import '../services/local_cache_service.dart';
import '../services/offline_database_service.dart';
import '../services/offline_report_queue.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _anonymousMode = true;
  bool _locationSharing = true;
  bool _dataEncryption = true;
  bool _pushNotif = true;
  bool _hotspotAlerts = true;
  bool _reportUpdates = true;
  bool _clearing = false;
  bool _exporting = false;

  final _deviceService = DeviceService();
  final _cacheService = LocalCacheService();
  final _offlineQueue = OfflineReportQueue();
  final _offlineDatabase = OfflineDatabaseService();

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      child: Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                children: [
                  _section('Privacy'),
                  _toggle('Pseudonymous Mode', 'Use a rotating local device identity instead of personal account details',
                      _anonymousMode, (v) => setState(() => _anonymousMode = v)),
                  _toggle('Location Sharing', 'Share GPS when submitting reports',
                      _locationSharing, (v) => setState(() => _locationSharing = v)),
                  _toggle('Data Encryption', 'Protect report data during storage and secure transfer',
                      _dataEncryption, (v) => setState(() => _dataEncryption = v)),
                  _section('Notifications'),
                  _toggle('Push Notifications', 'Report status updates',
                      _pushNotif, (v) => setState(() => _pushNotif = v)),
                  _toggle('Hotspot Alerts', 'New danger zone notifications',
                      _hotspotAlerts, (v) => setState(() => _hotspotAlerts = v)),
                  _toggle('Report Updates', 'When your report status changes',
                      _reportUpdates, (v) => setState(() => _reportUpdates = v)),
                  _section('About'),
                  _infoRow('Version', '2.1.0'),
                  _infoRow('Build', '2024.12.01'),
                  _infoRow('Verification', 'Rules + AI scoring'),
                  const SizedBox(height: 24),
                  _buildDangerActions(),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
    );
  }

  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 20, 4),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.chevron_left, size: 28),
          ),
          const Expanded(
            child: Text('Settings',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }

  Widget _section(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 20, bottom: 8),
      child: Text(title,
          style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppColors.muted,
              letterSpacing: 0.5)),
    );
  }

  Widget _toggle(String title, String sub, bool value, ValueChanged<bool> onChanged) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.card,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(
                        fontSize: 13, fontWeight: FontWeight.w600)),
                Text(sub,
                    style:
                        const TextStyle(fontSize: 10, color: AppColors.muted)),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeThumbColor: AppColors.accent,
            activeTrackColor: AppColors.accent.withValues(alpha: 0.3),
            inactiveThumbColor: AppColors.muted,
            inactiveTrackColor: AppColors.surface3,
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      decoration: BoxDecoration(
        color: AppColors.card,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Text(label,
              style: const TextStyle(fontSize: 12, color: AppColors.muted)),
          const Spacer(),
          Text(value,
              style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  fontFamily: 'monospace')),
        ],
      ),
    );
  }

  Widget _buildDangerActions() {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          height: 44,
          child: OutlinedButton.icon(
            onPressed: _exporting ? null : _showExportNotice,
            icon: _exporting
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.download, size: 16),
            label: Text(
              _exporting ? 'Exporting...' : 'Export My Data',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            ),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: AppColors.border),
              foregroundColor: AppColors.text,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          height: 44,
          child: OutlinedButton.icon(
            onPressed: _clearing ? null : _showClearDialog,
            icon: const Icon(Icons.delete_outline, size: 16),
            label: Text(
              _clearing ? 'Clearing Local Data...' : 'Clear All Data',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            ),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: AppColors.danger),
              foregroundColor: AppColors.danger,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
      ],
    );
  }

  void _showClearDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Clear All Data?',
            style: TextStyle(fontWeight: FontWeight.w700)),
        content: const Text(
          'This will erase all local data including your device identity. This cannot be undone.',
          style: TextStyle(fontSize: 13, color: AppColors.muted),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel',
                style: TextStyle(color: AppColors.muted)),
          ),
          TextButton(
            onPressed: _clearing
                ? null
                : () {
              Navigator.of(ctx).pop();
              _clearAllData();
            },
            child: const Text('Clear',
                style: TextStyle(color: AppColors.danger)),
          ),
        ],
      ),
    );
  }

  void _showExportNotice() {
    _exportMyData();
  }

  Future<void> _exportMyData() async {
    if (_exporting) return;
    setState(() => _exporting = true);
    try {
      final deviceId = await _deviceService.getDeviceId();
      final deviceHash = await _deviceService.getDeviceHash();
      final cachedReports = deviceId != null
          ? await _cacheService.getCachedReports(deviceId)
          : <Map<String, dynamic>>[];
      final pendingItems = await _offlineQueue.getPendingItems();
      final queuedReports = pendingItems.map((item) => {
        'queue_id': item.queueId,
        'status': item.status,
        'report_id': item.reportId,
        'attempts': item.attempts,
        'evidence_count': item.evidenceCount,
        'created_at': item.createdAt?.toIso8601String(),
      }).toList();

      final exportData = {
        'exported_at': DateTime.now().toUtc().toIso8601String(),
        'app_version': '2.1.0',
        'device_id': deviceId,
        'device_hash_prefix': deviceHash.length >= 8 ? '${deviceHash.substring(0, 8)}...' : deviceHash,
        'cached_reports_count': cachedReports.length,
        'queued_offline_reports_count': queuedReports.length,
        'cached_reports': cachedReports,
        'queued_offline_reports': queuedReports,
      };

      final dir = await getApplicationDocumentsDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final file = File('${dir.path}/trustbond_export_$timestamp.json');
      await file.writeAsString(
        const JsonEncoder.withIndent('  ').convert(exportData),
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Data exported to: ${file.path}',
            style: const TextStyle(fontSize: 12),
          ),
          duration: const Duration(seconds: 6),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Export failed. Please try again.'),
        ),
      );
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  Future<void> _clearAllData() async {
    if (_clearing) return;

    setState(() => _clearing = true);
    try {
      await Future.wait([
        _deviceService.clearLocalIdentity(),
        _cacheService.clearAll(),
        _offlineQueue.clearAll(),
        _offlineDatabase.clearAllData(),
      ]);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Local TrustBond data was cleared from this device.'),
        ),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not clear all local data. Please try again.'),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _clearing = false);
      }
    }
  }
}
