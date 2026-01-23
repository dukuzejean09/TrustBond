import 'package:flutter/material.dart';
import '../config/theme.dart';

class ReportsTable extends StatelessWidget {
  const ReportsTable({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowHeight: 56,
        dataRowMinHeight: 60,
        dataRowMaxHeight: 60,
        columnSpacing: 40,
        columns: const [
          DataColumn(label: Text('Report ID')),
          DataColumn(label: Text('Type')),
          DataColumn(label: Text('Location')),
          DataColumn(label: Text('Date')),
          DataColumn(label: Text('Status')),
          DataColumn(label: Text('Assigned To')),
          DataColumn(label: Text('Actions')),
        ],
        rows: _buildRows(),
      ),
    );
  }

  List<DataRow> _buildRows() {
    final reports = [
      {
        'id': 'RPT-2024-0048',
        'type': 'Theft',
        'location': 'Kigali, Nyarugenge',
        'date': '2024-01-15',
        'status': 'pending',
        'officer': 'Unassigned',
      },
      {
        'id': 'RPT-2024-0047',
        'type': 'Domestic Violence',
        'location': 'Kigali, Gasabo',
        'date': '2024-01-15',
        'status': 'investigating',
        'officer': 'Off. Mugabo J.',
      },
      {
        'id': 'RPT-2024-0046',
        'type': 'Fraud',
        'location': 'Kigali, Kicukiro',
        'date': '2024-01-14',
        'status': 'resolved',
        'officer': 'Off. Uwase M.',
      },
      {
        'id': 'RPT-2024-0045',
        'type': 'Traffic Accident',
        'location': 'Huye, Tumba',
        'date': '2024-01-14',
        'status': 'pending',
        'officer': 'Unassigned',
      },
      {
        'id': 'RPT-2024-0044',
        'type': 'Vandalism',
        'location': 'Musanze, Muhoza',
        'date': '2024-01-13',
        'status': 'investigating',
        'officer': 'Off. Habimana P.',
      },
    ];

    return reports.map((report) {
      return DataRow(
        cells: [
          DataCell(
            Text(
              report['id']!,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: AppTheme.primaryNavy,
              ),
            ),
          ),
          DataCell(_buildTypeChip(report['type']!)),
          DataCell(Text(report['location']!)),
          DataCell(Text(report['date']!)),
          DataCell(_buildStatusChip(report['status']!)),
          DataCell(Text(report['officer']!)),
          DataCell(
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.visibility_outlined, size: 20),
                  onPressed: () {},
                  color: AppTheme.primaryNavy,
                  tooltip: 'View Details',
                ),
                IconButton(
                  icon: const Icon(Icons.edit_outlined, size: 20),
                  onPressed: () {},
                  color: Colors.blue,
                  tooltip: 'Edit',
                ),
                IconButton(
                  icon: const Icon(Icons.person_add_outlined, size: 20),
                  onPressed: () {},
                  color: Colors.green,
                  tooltip: 'Assign Officer',
                ),
              ],
            ),
          ),
        ],
      );
    }).toList();
  }

  Widget _buildTypeChip(String type) {
    Color bgColor;
    switch (type.toLowerCase()) {
      case 'theft':
        bgColor = Colors.orange;
        break;
      case 'domestic violence':
        bgColor = Colors.red;
        break;
      case 'fraud':
        bgColor = Colors.purple;
        break;
      case 'traffic accident':
        bgColor = Colors.blue;
        break;
      default:
        bgColor = Colors.grey;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: bgColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: bgColor.withOpacity(0.3)),
      ),
      child: Text(
        type,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w500,
          color: bgColor.shade700,
        ),
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    Color color;
    String label;
    IconData icon;

    switch (status) {
      case 'pending':
        color = AppTheme.statusPending;
        label = 'Pending';
        icon = Icons.schedule;
        break;
      case 'investigating':
        color = AppTheme.statusInProgress;
        label = 'Investigating';
        icon = Icons.autorenew;
        break;
      case 'resolved':
        color = AppTheme.statusResolved;
        label = 'Resolved';
        icon = Icons.check_circle;
        break;
      default:
        color = Colors.grey;
        label = status;
        icon = Icons.info;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

extension ColorShade on Color {
  Color get shade700 {
    return Color.fromARGB(
      alpha,
      (red * 0.7).round(),
      (green * 0.7).round(),
      (blue * 0.7).round(),
    );
  }
}
