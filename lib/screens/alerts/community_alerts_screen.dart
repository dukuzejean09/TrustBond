import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../models/alert_model.dart';

class CommunityAlertsScreen extends StatefulWidget {
  const CommunityAlertsScreen({super.key});

  @override
  State<CommunityAlertsScreen> createState() => _CommunityAlertsScreenState();
}

class _CommunityAlertsScreenState extends State<CommunityAlertsScreen> {
  String _filterDistance = 'all';
  String _filterCategory = 'all';
  String _sortBy = 'recent';

  List<AlertModel> get _filteredAlerts {
    List<AlertModel> alerts = MockAlerts.getAlerts();

    // Filter by distance
    if (_filterDistance != 'all') {
      final maxDistance = double.parse(_filterDistance);
      alerts = alerts.where((a) => a.distance <= maxDistance).toList();
    }

    // Filter by category
    if (_filterCategory != 'all') {
      alerts = alerts.where((a) => a.type.name == _filterCategory).toList();
    }

    // Sort
    switch (_sortBy) {
      case 'recent':
        alerts.sort((a, b) => b.createdAt.compareTo(a.createdAt));
        break;
      case 'distance':
        alerts.sort((a, b) => a.distance.compareTo(b.distance));
        break;
    }

    return alerts;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Community Alerts'),
        actions: [
          IconButton(
            onPressed: _showFilterSheet,
            icon: const Icon(Icons.filter_list),
          ),
        ],
      ),
      body: Column(
        children: [
          // Quick filters
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: Column(
              children: [
                // Distance filter
                SizedBox(
                  height: 40,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: [
                      _QuickFilterChip(
                        label: 'All Distances',
                        isSelected: _filterDistance == 'all',
                        onTap: () => setState(() => _filterDistance = 'all'),
                      ),
                      _QuickFilterChip(
                        label: '< 1 km',
                        isSelected: _filterDistance == '1',
                        onTap: () => setState(() => _filterDistance = '1'),
                      ),
                      _QuickFilterChip(
                        label: '< 3 km',
                        isSelected: _filterDistance == '3',
                        onTap: () => setState(() => _filterDistance = '3'),
                      ),
                      _QuickFilterChip(
                        label: '< 5 km',
                        isSelected: _filterDistance == '5',
                        onTap: () => setState(() => _filterDistance = '5'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Alerts list
          Expanded(
            child: _filteredAlerts.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.notifications_off_outlined,
                          size: 80,
                          color: AppTheme.textSecondary.withOpacity(0.5),
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'No alerts found',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Try adjusting your filters',
                          style: TextStyle(color: AppTheme.textLight),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _filteredAlerts.length,
                    itemBuilder: (context, index) {
                      final alert = _filteredAlerts[index];
                      return _AlertCard(
                        alert: alert,
                        onTap: () => _showAlertDetails(alert),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  void _showFilterSheet() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Filter & Sort',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      TextButton(
                        onPressed: () {
                          setModalState(() {
                            _filterDistance = 'all';
                            _filterCategory = 'all';
                            _sortBy = 'recent';
                          });
                          setState(() {});
                        },
                        child: const Text('Reset'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Category filter
                  const Text(
                    'Category',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: [
                      _FilterChipInSheet(
                        label: 'All',
                        isSelected: _filterCategory == 'all',
                        onTap: () {
                          setModalState(() => _filterCategory = 'all');
                          setState(() {});
                        },
                      ),
                      _FilterChipInSheet(
                        label: 'Incidents',
                        isSelected: _filterCategory == 'incident',
                        onTap: () {
                          setModalState(() => _filterCategory = 'incident');
                          setState(() {});
                        },
                      ),
                      _FilterChipInSheet(
                        label: 'Safety',
                        isSelected: _filterCategory == 'safety',
                        onTap: () {
                          setModalState(() => _filterCategory = 'safety');
                          setState(() {});
                        },
                      ),
                      _FilterChipInSheet(
                        label: 'Police',
                        isSelected: _filterCategory == 'police',
                        onTap: () {
                          setModalState(() => _filterCategory = 'police');
                          setState(() {});
                        },
                      ),
                      _FilterChipInSheet(
                        label: 'Warnings',
                        isSelected: _filterCategory == 'warning',
                        onTap: () {
                          setModalState(() => _filterCategory = 'warning');
                          setState(() {});
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Sort
                  const Text(
                    'Sort By',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: [
                      _FilterChipInSheet(
                        label: 'Most Recent',
                        isSelected: _sortBy == 'recent',
                        onTap: () {
                          setModalState(() => _sortBy = 'recent');
                          setState(() {});
                        },
                      ),
                      _FilterChipInSheet(
                        label: 'Nearest',
                        isSelected: _sortBy == 'distance',
                        onTap: () {
                          setModalState(() => _sortBy = 'distance');
                          setState(() {});
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Apply Filters'),
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _showAlertDetails(AlertModel alert) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.6,
          maxChildSize: 0.9,
          minChildSize: 0.4,
          expand: false,
          builder: (context, scrollController) {
            return SingleChildScrollView(
              controller: scrollController,
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Handle
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: AppTheme.dividerColor,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Type badge
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: alert.typeColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(alert.typeIcon, size: 16, color: alert.typeColor),
                        const SizedBox(width: 6),
                        Text(
                          alert.typeLabel,
                          style: TextStyle(
                            color: alert.typeColor,
                            fontWeight: FontWeight.w600,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Title
                  Text(
                    alert.title,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),

                  // Meta info
                  Row(
                    children: [
                      Icon(
                        Icons.access_time,
                        size: 16,
                        color: AppTheme.textSecondary,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        alert.timeAgo,
                        style: const TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Icon(
                        Icons.location_on,
                        size: 16,
                        color: AppTheme.textSecondary,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        alert.formattedDistance,
                        style: const TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Description
                  Text(
                    alert.description,
                    style: const TextStyle(
                      fontSize: 15,
                      height: 1.6,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Location
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.backgroundColor,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(
                            Icons.location_on,
                            color: AppTheme.primaryColor,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Location',
                                style: TextStyle(
                                  color: AppTheme.textSecondary,
                                  fontSize: 12,
                                ),
                              ),
                              Text(
                                alert.address,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Actions
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.map),
                          label: const Text('View on Map'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.share),
                          label: const Text('Share'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            );
          },
        );
      },
    );
  }
}

class _QuickFilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _QuickFilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (_) => onTap(),
        selectedColor: AppTheme.primaryColor,
        showCheckmark: false,
        labelStyle: TextStyle(
          color: isSelected ? Colors.white : AppTheme.textPrimary,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
        ),
      ),
    );
  }
}

class _FilterChipInSheet extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _FilterChipInSheet({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => onTap(),
      selectedColor: AppTheme.primaryColor,
      showCheckmark: false,
      labelStyle: TextStyle(
        color: isSelected ? Colors.white : AppTheme.textPrimary,
        fontSize: 13,
      ),
    );
  }
}

class _AlertCard extends StatelessWidget {
  final AlertModel alert;
  final VoidCallback onTap;

  const _AlertCard({
    required this.alert,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  // Type icon
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: alert.typeColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      alert.typeIcon,
                      color: alert.typeColor,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  // Type label and time
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          alert.typeLabel,
                          style: TextStyle(
                            color: alert.typeColor,
                            fontWeight: FontWeight.w600,
                            fontSize: 12,
                          ),
                        ),
                        Text(
                          alert.timeAgo,
                          style: const TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Distance
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppTheme.backgroundColor,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.location_on,
                          size: 12,
                          color: AppTheme.textSecondary,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          alert.formattedDistance,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Title
              Text(
                alert.title,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 8),
              // Description
              Text(
                alert.description,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 12),
              // Location
              Row(
                children: [
                  const Icon(
                    Icons.place,
                    size: 14,
                    color: AppTheme.textLight,
                  ),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      alert.address,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textLight,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
