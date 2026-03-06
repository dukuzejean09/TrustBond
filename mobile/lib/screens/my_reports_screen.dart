import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../widgets/shared_widgets.dart';
import '../services/api_service.dart';
import '../services/device_service.dart';
import '../models/report_model.dart';
import 'report_detail_screen.dart';

class MyReportsScreen extends StatefulWidget {
  const MyReportsScreen({super.key});

  @override
  State<MyReportsScreen> createState() => _MyReportsScreenState();
}

class _MyReportsScreenState extends State<MyReportsScreen>
    with SingleTickerProviderStateMixin {
  final _apiService = ApiService();
  final _deviceService = DeviceService();

  String? _deviceId;
  List<ReportListItem> _reports = [];
  bool _loading = true;
  int _filterIndex = 0;

  static const _filters = ['All', 'Pending', 'Verified', 'Rejected'];

  late TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: _filters.length, vsync: this);
    _tabCtrl.addListener(() {
      if (!_tabCtrl.indexIsChanging) {
        setState(() => _filterIndex = _tabCtrl.index);
      }
    });
    _load();
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final deviceId = await _deviceService.getDeviceId();
    if (deviceId == null || deviceId.isEmpty) {
      setState(() {
        _loading = false;
        _deviceId = null;
      });
      return;
    }
    _deviceId = deviceId;
    try {
      final list = await _apiService.getMyReports(deviceId);
      setState(() {
        _reports = list
            .map((e) => ReportListItem.fromJson(e as Map<String, dynamic>))
            .toList();
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  List<ReportListItem> get _filtered {
    if (_filterIndex == 0) return _reports;
    final key = _filters[_filterIndex].toLowerCase();
    return _reports.where((r) {
      final s = r.ruleStatus.toLowerCase();
      if (key == 'pending') return s == 'pending' || s == 'processing';
      if (key == 'verified') {
        return s == 'confirmed' || s == 'verified' || s == 'trusted' || s == 'passed';
      }
      if (key == 'rejected') return s == 'rejected' || s == 'flagged';
      return true;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildTabs(),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
      child: Row(
        children: [
          const Text('My Reports',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
          const Spacer(),
          Text('${_reports.length} total',
              style: const TextStyle(fontSize: 11, color: AppColors.muted)),
        ],
      ),
    );
  }

  Widget _buildTabs() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      height: 36,
      decoration: BoxDecoration(
        color: AppColors.surface2,
        borderRadius: BorderRadius.circular(10),
      ),
      child: TabBar(
        controller: _tabCtrl,
        indicator: BoxDecoration(
          color: AppColors.accent.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.accent.withValues(alpha: 0.35)),
        ),
        indicatorSize: TabBarIndicatorSize.tab,
        labelColor: AppColors.accent,
        unselectedLabelColor: AppColors.muted,
        labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        unselectedLabelStyle: const TextStyle(fontSize: 12),
        dividerHeight: 0,
        tabs: _filters.map((f) => Tab(text: f)).toList(),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(
          child: CircularProgressIndicator(color: AppColors.accent));
    }
    final items = _filtered;
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.assignment_outlined,
                size: 48, color: AppColors.muted.withValues(alpha: 0.5)),
            const SizedBox(height: 12),
            const Text('No reports found',
                style: TextStyle(color: AppColors.muted)),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      color: AppColors.accent,
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
        itemCount: items.length,
        itemBuilder: (context, index) {
          final r = items[index];
          return ReportItemCard(
            icon: iconForIncidentType(r.incidentTypeName ?? ''),
            iconBg: colorForIncidentType(r.incidentTypeName ?? '')
                .withValues(alpha: 0.1),
            typeName: r.incidentTypeName ?? 'Incident',
            description: r.description ?? 'No description',
            timeLabel: timeAgo(r.reportedAt),
            statusLabel: formatStatus(r.ruleStatus),
            statusType: badgeTypeFromStatus(r.ruleStatus),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => ReportDetailScreen(
                  reportId: r.reportId,
                  deviceId: _deviceId ?? '',
                ),
              ),
            ),
          );
        },
      ),
    );
  }

}
