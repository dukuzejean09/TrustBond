import 'package:flutter/material.dart';
import '../models/report_model.dart';
import '../models/incident_type.dart';
import '../models/evidence_model.dart';

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

  // Submit report (mock)
  ReportModel submitReport() {
    final report = ReportModel(
      id: 'RPT${DateTime.now().millisecondsSinceEpoch}',
      incidentType: _selectedIncidentType!,
      description: _description,
      isAnonymous: _isAnonymous,
      latitude: _latitude!,
      longitude: _longitude!,
      address: _address,
      incidentDate: _incidentDate,
      incidentTime: _incidentTime,
      evidenceList: List.from(_evidenceList),
      status: ReportStatus.submitted,
      submittedAt: DateTime.now(),
    );

    _myReports.insert(0, report);
    resetCurrentReport();
    notifyListeners();
    return report;
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
    notifyListeners();
  }

  // Check if report is valid
  bool get isReportValid {
    return _selectedIncidentType != null &&
        _description.isNotEmpty &&
        _latitude != null &&
        _longitude != null;
  }

  // Load mock data for demo
  void loadMockData() {
    _myReports = [
      ReportModel(
        id: 'RPT001',
        incidentType: IncidentType.assault,
        description: 'Witnessed an assault near the market area. Two individuals were involved.',
        isAnonymous: true,
        latitude: -1.9403,
        longitude: 29.8739,
        address: 'KN 5 Rd, Kigali',
        incidentDate: DateTime.now().subtract(const Duration(days: 2)),
        incidentTime: const TimeOfDay(hour: 14, minute: 30),
        evidenceList: [],
        status: ReportStatus.underReview,
        submittedAt: DateTime.now().subtract(const Duration(days: 2)),
      ),
      ReportModel(
        id: 'RPT002',
        incidentType: IncidentType.theft,
        description: 'Phone stolen at the bus station.',
        isAnonymous: false,
        latitude: -1.9456,
        longitude: 29.8790,
        address: 'Nyabugogo Bus Station, Kigali',
        incidentDate: DateTime.now().subtract(const Duration(days: 5)),
        incidentTime: const TimeOfDay(hour: 9, minute: 15),
        evidenceList: [],
        status: ReportStatus.verified,
        submittedAt: DateTime.now().subtract(const Duration(days: 5)),
      ),
      ReportModel(
        id: 'RPT003',
        incidentType: IncidentType.noiseDisturbance,
        description: 'Loud music from neighboring building late at night.',
        isAnonymous: true,
        latitude: -1.9380,
        longitude: 29.8700,
        address: 'Kimironko, Kigali',
        incidentDate: DateTime.now().subtract(const Duration(days: 7)),
        incidentTime: const TimeOfDay(hour: 23, minute: 45),
        evidenceList: [],
        status: ReportStatus.closed,
        submittedAt: DateTime.now().subtract(const Duration(days: 7)),
      ),
    ];

    // Add mock offline reports for demo
    _offlineReports = [
      ReportModel(
        id: 'OFF001',
        incidentType: IncidentType.suspiciousPerson,
        description: 'Unknown person loitering around the neighborhood.',
        isAnonymous: true,
        latitude: -1.9420,
        longitude: 29.8750,
        address: 'Nyarutarama, Kigali',
        incidentDate: DateTime.now().subtract(const Duration(hours: 3)),
        incidentTime: const TimeOfDay(hour: 16, minute: 20),
        evidenceList: [],
        status: ReportStatus.draft,
        submittedAt: DateTime.now().subtract(const Duration(hours: 3)),
      ),
    ];

    notifyListeners();
  }

  // Submit offline report
  void submitOfflineReport(String id) {
    final index = _offlineReports.indexWhere((r) => r.id == id);
    if (index != -1) {
      final report = _offlineReports[index];
      final submittedReport = ReportModel(
        id: 'RPT${DateTime.now().millisecondsSinceEpoch}',
        incidentType: report.incidentType,
        description: report.description,
        isAnonymous: report.isAnonymous,
        latitude: report.latitude,
        longitude: report.longitude,
        address: report.address,
        incidentDate: report.incidentDate,
        incidentTime: report.incidentTime,
        evidenceList: report.evidenceList,
        status: ReportStatus.submitted,
        submittedAt: DateTime.now(),
      );
      _myReports.insert(0, submittedReport);
      _offlineReports.removeAt(index);
      notifyListeners();
    }
  }
}
