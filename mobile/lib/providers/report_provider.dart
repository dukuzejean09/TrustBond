import 'package:flutter/material.dart';
import '../models/report_model.dart';
import '../models/incident_type.dart';
import '../models/evidence_model.dart';
import '../services/api_service.dart';

class ReportProvider extends ChangeNotifier {
  // Current Report being created
  IncidentType? _selectedIncidentType;
  String _description = '';
  bool _isAnonymous = true;
  double? _latitude;
  double? _longitude;
  String _address = '';
  DateTime _incidentDate = DateTime.now();
  TimeOfDay _incidentTime = TimeOfDay.now();
  List<EvidenceModel> _evidenceList = [];

  // Saved Reports
  List<ReportModel> _myReports = [];
  List<ReportModel> _offlineReports = [];
  
  // Tracking
  String? _lastTrackingCode;
  Map<String, dynamic>? _trackedReportStatus;
  
  // Loading state
  bool _isLoading = false;
  String? _error;

  // Getters
  IncidentType? get selectedIncidentType => _selectedIncidentType;
  String get description => _description;
  bool get isAnonymous => _isAnonymous;
  double? get latitude => _latitude;
  double? get longitude => _longitude;
  String get address => _address;
  DateTime get incidentDate => _incidentDate;
  TimeOfDay get incidentTime => _incidentTime;
  List<EvidenceModel> get evidenceList => _evidenceList;
  List<ReportModel> get myReports => _myReports;
  List<ReportModel> get offlineReports => _offlineReports;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String? get lastTrackingCode => _lastTrackingCode;
  Map<String, dynamic>? get trackedReportStatus => _trackedReportStatus;

  // Setters for current report
  void setIncidentType(IncidentType type) {
    _selectedIncidentType = type;
    notifyListeners();
  }

  void setDescription(String value) {
    _description = value;
    notifyListeners();
  }

  void setAnonymous(bool value) {
    _isAnonymous = value;
    notifyListeners();
  }

  void setLocation(double lat, double lng, String addr) {
    _latitude = lat;
    _longitude = lng;
    _address = addr;
    notifyListeners();
  }

  void setIncidentDate(DateTime date) {
    _incidentDate = date;
    notifyListeners();
  }

  void setIncidentTime(TimeOfDay time) {
    _incidentTime = time;
    notifyListeners();
  }

  void addEvidence(EvidenceModel evidence) {
    _evidenceList.add(evidence);
    notifyListeners();
  }

  void removeEvidence(int index) {
    if (index >= 0 && index < _evidenceList.length) {
      _evidenceList.removeAt(index);
      notifyListeners();
    }
  }

  void clearEvidence() {
    _evidenceList.clear();
    notifyListeners();
  }

  // Map incident type to API category
  String _mapIncidentTypeToCategory(IncidentType type) {
    switch (type.category) {
      case IncidentCategory.crimeAgainstPerson:
        if (type.id == 'assault') return 'assault';
        if (type.id == 'domestic_disturbance') return 'domestic_violence';
        return 'assault';
      case IncidentCategory.propertyTheft:
        if (type.id == 'robbery') return 'robbery';
        return 'theft';
      case IncidentCategory.fraudFinancial:
        return 'fraud';
      case IncidentCategory.suspiciousActivity:
        return 'other';
      case IncidentCategory.publicOrder:
        return 'vandalism';
      case IncidentCategory.trafficRoad:
        return 'traffic_violation';
      case IncidentCategory.infrastructureEnvironment:
        return 'other';
      default:
        return 'other';
    }
  }

  // Submit report to API (anonymous - no auth required)
  Future<ReportModel?> submitReport() async {
    if (!isReportValid) {
      _error = 'Please fill all required fields';
      notifyListeners();
      return null;
    }

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Format incident date and time
      final formattedDate = _incidentDate.toIso8601String();
      final formattedTime = '${_incidentTime.hour.toString().padLeft(2, '0')}:${_incidentTime.minute.toString().padLeft(2, '0')}';

      // Use anonymous endpoint - no authentication required
      final result = await ApiService.createAnonymousReport(
        title: '${_selectedIncidentType!.name} Report',
        description: _description,
        category: _mapIncidentTypeToCategory(_selectedIncidentType!),
        priority: 'medium',
        latitude: _latitude,
        longitude: _longitude,
        locationDescription: _address,
        incidentDate: formattedDate,
        incidentTime: formattedTime,
      );

      _isLoading = false;

      if (result['success']) {
        final reportData = result['data']['report'];
        final trackingCode = result['data']['trackingCode'];
        
        // Create local report model with tracking code
        final report = ReportModel(
          id: reportData['reportNumber'] ?? 'RPT${DateTime.now().millisecondsSinceEpoch}',
          incidentType: _selectedIncidentType!,
          description: _description,
          isAnonymous: true,  // Always anonymous
          latitude: _latitude!,
          longitude: _longitude!,
          address: _address,
          incidentDate: _incidentDate,
          incidentTime: _incidentTime,
          evidenceList: List.from(_evidenceList),
          status: ReportStatus.submitted,
          submittedAt: DateTime.now(),
          trackingCode: trackingCode,
        );

        _myReports.insert(0, report);
        _lastTrackingCode = trackingCode;  // Store for display
        resetCurrentReport();
        notifyListeners();
        return report;
      } else {
        _error = result['error'] ?? 'Failed to submit report';
        notifyListeners();
        return null;
      }
    } catch (e) {
      _isLoading = false;
      _error = 'Failed to submit report: $e';
      notifyListeners();
      return null;
    }
  }

  // Track anonymous report by tracking code
  Future<Map<String, dynamic>?> trackReportByCode(String trackingCode) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await ApiService.trackReport(trackingCode);
      
      _isLoading = false;

      if (result['success']) {
        _trackedReportStatus = result['data'];
        notifyListeners();
        return result['data'];
      } else {
        _error = result['error'] ?? 'Report not found';
        _trackedReportStatus = null;
        notifyListeners();
        return null;
      }
    } catch (e) {
      _isLoading = false;
      _error = 'Failed to track report: $e';
      _trackedReportStatus = null;
      notifyListeners();
      return null;
    }
  }

  // Clear tracked report status
  void clearTrackedStatus() {
    _trackedReportStatus = null;
    notifyListeners();
  }

  // Fetch reports from API (for local storage only, no server call for anonymous users)
  Future<void> fetchMyReports() async {
    // For anonymous users, we only show locally stored reports
    // Reports are stored locally when submitted
    notifyListeners();
  }

  IncidentType _getIncidentTypeFromCategory(String? category) {
    switch (category) {
      case 'theft':
        return IncidentType.theft;
      case 'assault':
        return IncidentType.assault;
      case 'robbery':
        return IncidentType.theft; // Map robbery to theft
      case 'fraud':
        return IncidentType.fraud;
      case 'vandalism':
        return IncidentType.vandalism;
      case 'domestic_violence':
        return IncidentType.domesticDisturbance;
      case 'traffic_violation':
        return IncidentType.recklessDriving;
      default:
        return IncidentType.other;
    }
  }

  TimeOfDay _parseTimeString(String? timeStr) {
    if (timeStr == null || timeStr.isEmpty) {
      return TimeOfDay.now();
    }
    try {
      final parts = timeStr.split(':');
      return TimeOfDay(
        hour: int.parse(parts[0]),
        minute: int.parse(parts[1]),
      );
    } catch (e) {
      return TimeOfDay.now();
    }
  }

  ReportStatus _parseStatus(String? status) {
    switch (status) {
      case 'pending':
        return ReportStatus.submitted;
      case 'under_review':
        return ReportStatus.underReview;
      case 'investigating':
        return ReportStatus.underReview;
      case 'resolved':
        return ReportStatus.verified;
      case 'closed':
        return ReportStatus.closed;
      default:
        return ReportStatus.submitted;
    }
  }

  // Save offline
  void saveOffline() {
    final report = ReportModel(
      id: 'OFF${DateTime.now().millisecondsSinceEpoch}',
      incidentType: _selectedIncidentType!,
      description: _description,
      isAnonymous: _isAnonymous,
      latitude: _latitude ?? 0,
      longitude: _longitude ?? 0,
      address: _address,
      incidentDate: _incidentDate,
      incidentTime: _incidentTime,
      evidenceList: List.from(_evidenceList),
      status: ReportStatus.draft,
      submittedAt: DateTime.now(),
    );

    _offlineReports.add(report);
    resetCurrentReport();
    notifyListeners();
  }

  // Delete offline report
  void deleteOfflineReport(String id) {
    _offlineReports.removeWhere((r) => r.id == id);
    notifyListeners();
  }

  // Reset current report
  void resetCurrentReport() {
    _selectedIncidentType = null;
    _description = '';
    _isAnonymous = true;
    _latitude = null;
    _longitude = null;
    _address = '';
    _incidentDate = DateTime.now();
    _incidentTime = TimeOfDay.now();
    _evidenceList = [];
    _error = null;
    notifyListeners();
  }

  // Check if report is valid
  bool get isReportValid {
    return _selectedIncidentType != null &&
        _description.isNotEmpty &&
        _latitude != null &&
        _longitude != null;
  }

  // Submit offline report
  Future<void> submitOfflineReport(String id) async {
    final index = _offlineReports.indexWhere((r) => r.id == id);
    if (index != -1) {
      final report = _offlineReports[index];
      
      // Set current report data from offline report
      _selectedIncidentType = report.incidentType;
      _description = report.description;
      _isAnonymous = report.isAnonymous;
      _latitude = report.latitude;
      _longitude = report.longitude;
      _address = report.address;
      _incidentDate = report.incidentDate;
      _incidentTime = report.incidentTime;
      _evidenceList = report.evidenceList;
      
      // Submit via API
      final submittedReport = await submitReport();
      
      if (submittedReport != null) {
        _offlineReports.removeAt(index);
        notifyListeners();
      }
    }
  }
}
