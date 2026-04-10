import 'offline_integration_guide.dart';
import 'offline_report_queue.dart';

class OfflineStatusSummary {
  final int legacyQueued;
  final int legacyFailed;
  final int pendingReports;
  final int failedReports;
  final int pendingEvidence;
  final int failedEvidence;
  final bool isSyncing;
  final String networkStatus;

  const OfflineStatusSummary({
    required this.legacyQueued,
    required this.legacyFailed,
    required this.pendingReports,
    required this.failedReports,
    required this.pendingEvidence,
    required this.failedEvidence,
    required this.isSyncing,
    required this.networkStatus,
  });

  const OfflineStatusSummary.empty()
      : legacyQueued = 0,
        legacyFailed = 0,
        pendingReports = 0,
        failedReports = 0,
        pendingEvidence = 0,
        failedEvidence = 0,
        isSyncing = false,
        networkStatus = 'unknown';

  int get totalPending => legacyQueued + pendingReports + pendingEvidence;
  int get totalFailed => legacyFailed + failedReports + failedEvidence;
  bool get hasItems => totalPending > 0 || totalFailed > 0;
}

class OfflineStatusService {
  final OfflineReportQueue _legacyQueue = OfflineReportQueue();
  final OfflineReportingIntegration _offlineIntegration =
      OfflineReportingIntegration();

  Future<OfflineStatusSummary> getStatusSummary() async {
    final results = await Future.wait([
      _legacyQueue.getStats(),
      _offlineIntegration.getQueueStatus(),
    ]);

    final legacy = results[0] as OfflineQueueStats;
    final modern = results[1] as OfflineQueueStatus;

    return OfflineStatusSummary(
      legacyQueued: legacy.queuedCount,
      legacyFailed: legacy.errorCount,
      pendingReports: modern.pendingReports,
      failedReports: modern.failedReports,
      pendingEvidence: modern.pendingEvidence,
      failedEvidence: modern.failedEvidence,
      isSyncing: modern.isSyncing,
      networkStatus: modern.networkStatus,
    );
  }

  Future<void> retryFailed() async {
    await Future.wait([
      _legacyQueue.retryAllFailedNow(),
      _offlineIntegration.retryFailedReports(),
    ]);
  }

  Future<void> syncNow() async {
    await Future.wait([
      _legacyQueue.syncIfNeeded(),
      _offlineIntegration.syncNow(),
    ]);
  }
}
