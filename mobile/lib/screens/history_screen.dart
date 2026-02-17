import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../config/theme.dart';
import '../providers/device_provider.dart';
import '../providers/report_provider.dart';

/// Shows the user's own (anonymized) report history.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final hash = context.read<DeviceProvider>().deviceHash;
      if (hash != null) {
        context.read<ReportProvider>().fetchHistory(hash);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final reportProv = context.watch<ReportProvider>();
    final df = DateFormat('dd MMM yyyy, HH:mm');

    return Scaffold(
      appBar: AppBar(title: const Text('My Reports')),
      body: reportProv.loadingHistory
          ? const Center(child: CircularProgressIndicator())
          : reportProv.history.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.inbox_outlined,
                          size: 64, color: AppTheme.textSecondary),
                      const SizedBox(height: 12),
                      Text('No reports yet',
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(color: AppTheme.textSecondary)),
                      const SizedBox(height: 4),
                      Text(
                        'Your submitted reports will appear here.',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () async {
                    final hash = context.read<DeviceProvider>().deviceHash;
                    if (hash != null) {
                      await context.read<ReportProvider>().fetchHistory(hash);
                    }
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: reportProv.history.length,
                    itemBuilder: (_, i) {
                      final r = reportProv.history[i];
                      return Card(
                        child: ListTile(
                          leading: _statusIcon(r.ruleStatus),
                          title: Text(
                            r.description,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text(
                            r.reportedAt != null
                                ? df.format(r.reportedAt!)
                                : '—',
                            style: const TextStyle(
                                fontSize: 12, color: AppTheme.textSecondary),
                          ),
                          trailing: _statusChip(r.ruleStatus),
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  Widget _statusIcon(String? status) {
    switch (status) {
      case 'passed':
        return const Icon(Icons.check_circle, color: AppTheme.success);
      case 'flagged':
        return const Icon(Icons.warning_amber, color: AppTheme.warning);
      case 'rejected':
        return const Icon(Icons.cancel, color: AppTheme.error);
      default:
        return const Icon(Icons.pending, color: AppTheme.textSecondary);
    }
  }

  Widget _statusChip(String? status) {
    final color = switch (status) {
      'passed' => AppTheme.success,
      'flagged' => AppTheme.warning,
      'rejected' => AppTheme.error,
      _ => AppTheme.textSecondary,
    };
    return Chip(
      label: Text(status ?? 'pending',
          style: TextStyle(color: color, fontSize: 11)),
      backgroundColor: color.withValues(alpha: 0.1),
      side: BorderSide.none,
      padding: EdgeInsets.zero,
      visualDensity: VisualDensity.compact,
    );
  }
}
