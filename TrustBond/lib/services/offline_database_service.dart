import 'dart:io';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'offline_database_schema.dart';

class OfflineDatabaseService {
  static final OfflineDatabaseService _instance =
      OfflineDatabaseService._internal();
  factory OfflineDatabaseService() => _instance;
  OfflineDatabaseService._internal();

  Database? _database;
  static const String _databaseName = 'trustbond_offline.db';
  static const int _databaseVersion = 1;

  Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final documentsDirectory = await getApplicationDocumentsDirectory();
    final path = join(documentsDirectory.path, _databaseName);

    return await openDatabase(
      path,
      version: _databaseVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await OfflineDatabaseSchema.initializeDatabase(db);
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Handle database upgrades in future versions
    if (oldVersion < newVersion) {
      // Add migration logic here when needed
    }
  }

  // Reports Queue Operations
  Future<String> insertReport(Map<String, dynamic> reportData) async {
    final db = await database;
    final queueId = reportData['queue_id'] as String;

    await db.insert(
      'reports_queue',
      reportData,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );

    return queueId;
  }

  Future<List<Map<String, dynamic>>> getPendingReports({int? limit}) async {
    final db = await database;

    String query = '''
      SELECT * FROM reports_queue 
      WHERE sync_status IN ('queued', 'error')
      ORDER BY sync_priority DESC, created_at ASC
    ''';

    if (limit != null) {
      query += ' LIMIT $limit';
    }

    return await db.rawQuery(query);
  }

  Future<Map<String, dynamic>?> getReportByQueueId(String queueId) async {
    final db = await database;

    final results = await db.query(
      'reports_queue',
      where: 'queue_id = ?',
      whereArgs: [queueId],
    );

    return results.isNotEmpty ? results.first : null;
  }

  Future<void> updateReportStatus(
    String queueId,
    String status, {
    String? error,
  }) async {
    final db = await database;

    final updateData = {
      'sync_status': status,
      'updated_at': DateTime.now().toIso8601String(),
    };

    if (error != null) {
      updateData['error_message'] = error;
    }

    await db.update(
      'reports_queue',
      updateData,
      where: 'queue_id = ?',
      whereArgs: [queueId],
    );
  }

  Future<void> updateReportWithServerData(
    String queueId,
    Map<String, dynamic> serverData,
  ) async {
    final db = await database;

    final updateData = {
      'updated_at': DateTime.now().toIso8601String(),
      ...serverData,
    };

    await db.update(
      'reports_queue',
      updateData,
      where: 'queue_id = ?',
      whereArgs: [queueId],
    );
  }

  Future<void> deleteReport(String queueId) async {
    final db = await database;

    await db.delete(
      'reports_queue',
      where: 'queue_id = ?',
      whereArgs: [queueId],
    );
  }

  // Evidence Queue Operations
  Future<String> insertEvidence(Map<String, dynamic> evidenceData) async {
    final db = await database;
    final evidenceId = evidenceData['evidence_id'] as String;

    await db.insert(
      'evidence_queue',
      evidenceData,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );

    return evidenceId;
  }

  Future<List<Map<String, dynamic>>> getPendingEvidence(String queueId) async {
    final db = await database;

    return await db.query(
      'evidence_queue',
      where: 'queue_id = ? AND sync_status IN (?, ?)',
      whereArgs: [queueId, 'pending', 'error'],
      orderBy: 'created_at ASC',
    );
  }

  Future<void> updateEvidenceStatus(
    String evidenceId,
    String status, {
    String? error,
  }) async {
    final db = await database;

    final updateData = {
      'sync_status': status,
      'updated_at': DateTime.now().toIso8601String(),
    };

    if (error != null) {
      updateData['error_message'] = error;
    }

    await db.update(
      'evidence_queue',
      updateData,
      where: 'evidence_id = ?',
      whereArgs: [evidenceId],
    );
  }

  Future<void> updateEvidenceWithServerData(
    String evidenceId,
    Map<String, dynamic> serverData,
  ) async {
    final db = await database;

    final updateData = {
      'updated_at': DateTime.now().toIso8601String(),
      ...serverData,
    };

    await db.update(
      'evidence_queue',
      updateData,
      where: 'evidence_id = ?',
      whereArgs: [evidenceId],
    );
  }

  // Device Cache Operations
  Future<void> cacheDeviceData(
    String deviceHash,
    Map<String, dynamic> deviceData,
  ) async {
    final db = await database;

    final cacheData = {
      'device_hash': deviceHash,
      'updated_at': DateTime.now().toIso8601String(),
      'is_registered': 1,
      ...deviceData,
    };

    await db.insert(
      'device_cache',
      cacheData,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<Map<String, dynamic>?> getCachedDevice(String deviceHash) async {
    final db = await database;

    final results = await db.query(
      'device_cache',
      where: 'device_hash = ?',
      whereArgs: [deviceHash],
    );

    return results.isNotEmpty ? results.first : null;
  }

  // Incident Types Cache Operations
  Future<void> cacheIncidentTypes(
    List<Map<String, dynamic>> incidentTypes,
  ) async {
    final db = await database;
    final batch = db.batch();

    // Clear existing cache
    batch.delete('incident_types_cache');

    // Insert new data with expiration (24 hours)
    final expiresAt = DateTime.now()
        .add(const Duration(hours: 24))
        .toIso8601String();
    final now = DateTime.now().toIso8601String();

    for (final incident in incidentTypes) {
      batch.insert('incident_types_cache', {
        ...incident,
        'cached_at': now,
        'expires_at': expiresAt,
      });
    }

    await batch.commit(noResult: true);
  }

  Future<List<Map<String, dynamic>>> getCachedIncidentTypes() async {
    final db = await database;
    final now = DateTime.now().toIso8601String();

    return await db.query(
      'incident_types_cache',
      where: 'expires_at > ?',
      whereArgs: [now],
      orderBy: 'incident_type_id',
    );
  }

  // Sync Status Operations
  Future<void> updateSyncStatus(Map<String, dynamic> statusData) async {
    final db = await database;

    final updateData = {
      'updated_at': DateTime.now().toIso8601String(),
      ...statusData,
    };

    await db.update('sync_status', updateData, where: 'id = ?', whereArgs: [1]);
  }

  Future<Map<String, dynamic>?> getSyncStatus() async {
    final db = await database;

    final results = await db.query(
      'sync_status',
      where: 'id = ?',
      whereArgs: [1],
    );

    return results.isNotEmpty ? results.first : null;
  }

  // Statistics
  Future<Map<String, int>> getQueueStats() async {
    final db = await database;

    final reportsResult = await db.rawQuery('''
      SELECT 
        COUNT(CASE WHEN sync_status = 'queued' THEN 1 END) as queued_reports,
        COUNT(CASE WHEN sync_status = 'error' THEN 1 END) as failed_reports,
        COUNT(CASE WHEN sync_status = 'completed' THEN 1 END) as completed_reports
      FROM reports_queue
    ''');

    final evidenceResult = await db.rawQuery('''
      SELECT 
        COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_evidence,
        COUNT(CASE WHEN sync_status = 'error' THEN 1 END) as failed_evidence,
        COUNT(CASE WHEN sync_status = 'completed' THEN 1 END) as completed_evidence
      FROM evidence_queue
    ''');

    final reports = reportsResult.first;
    final evidence = evidenceResult.first;

    return {
      'queued_reports': reports['queued_reports'] as int,
      'failed_reports': reports['failed_reports'] as int,
      'completed_reports': reports['completed_reports'] as int,
      'pending_evidence': evidence['pending_evidence'] as int,
      'failed_evidence': evidence['failed_evidence'] as int,
      'completed_evidence': evidence['completed_evidence'] as int,
    };
  }

  // Cleanup Operations
  Future<void> cleanupOldCompletedItems({int daysOld = 7}) async {
    final db = await database;
    final cutoffDate = DateTime.now()
        .subtract(Duration(days: daysOld))
        .toIso8601String();

    await db.delete(
      'reports_queue',
      where: 'sync_status = ? AND updated_at < ?',
      whereArgs: ['completed', cutoffDate],
    );

    await db.delete(
      'evidence_queue',
      where: 'sync_status = ? AND updated_at < ?',
      whereArgs: ['completed', cutoffDate],
    );
  }

  Future<void> closeDatabase() async {
    if (_database != null) {
      await _database!.close();
      _database = null;
    }
  }

  Future<void> clearAllData() async {
    final db = await database;
    await db.transaction((txn) async {
      await txn.delete('evidence_queue');
      await txn.delete('reports_queue');
      await txn.delete('device_cache');
      await txn.delete('incident_types_cache');
      await txn.update(
        'sync_status',
        {
          'last_sync_at': null,
          'last_successful_sync_at': null,
          'pending_reports': 0,
          'failed_reports': 0,
          'pending_evidence': 0,
          'failed_evidence': 0,
          'total_synced_reports': 0,
          'total_synced_evidence': 0,
          'network_status': 'unknown',
          'updated_at': DateTime.now().toIso8601String(),
        },
        where: 'id = ?',
        whereArgs: [1],
      );
    });
  }
}
