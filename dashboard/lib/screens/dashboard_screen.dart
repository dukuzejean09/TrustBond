import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../widgets/sidebar.dart';
import '../widgets/stats_card.dart';
import '../widgets/reports_table.dart';
import '../widgets/charts.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          Sidebar(
            selectedIndex: _selectedIndex,
            onItemSelected: (index) {
              setState(() => _selectedIndex = index);
            },
          ),
          
          // Main Content
          Expanded(
            child: Column(
              children: [
                // Top Bar
                _buildTopBar(),
                
                // Content Area
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    child: _buildContent(),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopBar() {
    return Container(
      height: 70,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          // Page Title
          const Text(
            'Dashboard Overview',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryNavy,
            ),
          ),
          
          const Spacer(),
          
          // Search
          SizedBox(
            width: 300,
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Search reports...',
                prefixIcon: const Icon(Icons.search),
                filled: true,
                fillColor: AppTheme.surfaceColor,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          
          const SizedBox(width: 16),
          
          // Notifications
          Stack(
            children: [
              IconButton(
                icon: const Icon(Icons.notifications_outlined),
                onPressed: () {},
                color: AppTheme.primaryNavy,
              ),
              Positioned(
                right: 8,
                top: 8,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Colors.red,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(width: 8),
          
          // User Profile
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: AppTheme.surfaceColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: AppTheme.primaryNavy,
                  child: const Text(
                    'JD',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'John Doe',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: AppTheme.primaryNavy,
                      ),
                    ),
                    Text(
                      'Supervisor',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(width: 8),
                Icon(Icons.arrow_drop_down, color: Colors.grey.shade600),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Stats Cards Row
        Row(
          children: [
            Expanded(
              child: StatsCard(
                title: 'Total Reports',
                value: '1,284',
                trend: '+12%',
                trendUp: true,
                icon: Icons.description_outlined,
                color: AppTheme.primaryNavy,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: StatsCard(
                title: 'Pending Review',
                value: '48',
                trend: '-5%',
                trendUp: false,
                icon: Icons.pending_outlined,
                color: AppTheme.statusPending,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: StatsCard(
                title: 'In Progress',
                value: '156',
                trend: '+8%',
                trendUp: true,
                icon: Icons.autorenew,
                color: AppTheme.statusInProgress,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: StatsCard(
                title: 'Resolved',
                value: '1,080',
                trend: '+15%',
                trendUp: true,
                icon: Icons.check_circle_outline,
                color: AppTheme.statusResolved,
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 24),
        
        // Charts Row
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Reports Trend Chart
            Expanded(
              flex: 2,
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Reports Trend',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryNavy,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: AppTheme.surfaceColor,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            children: [
                              const Text('Last 7 days'),
                              const SizedBox(width: 8),
                              Icon(Icons.arrow_drop_down, color: Colors.grey.shade600),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    const SizedBox(
                      height: 200,
                      child: ReportsTrendChart(),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(width: 16),
            
            // Reports by Type
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Reports by Type',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryNavy,
                      ),
                    ),
                    const SizedBox(height: 24),
                    const SizedBox(
                      height: 200,
                      child: ReportsByTypeChart(),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 24),
        
        // Recent Reports Table
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Recent Reports',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryNavy,
                    ),
                  ),
                  TextButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.arrow_forward),
                    label: const Text('View All'),
                    style: TextButton.styleFrom(
                      foregroundColor: AppTheme.primaryNavy,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const ReportsTable(),
            ],
          ),
        ),
      ],
    );
  }
}
