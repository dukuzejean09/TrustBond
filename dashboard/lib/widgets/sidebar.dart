import 'package:flutter/material.dart';
import '../config/theme.dart';

class Sidebar extends StatelessWidget {
  final int selectedIndex;
  final Function(int) onItemSelected;

  const Sidebar({
    super.key,
    required this.selectedIndex,
    required this.onItemSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 260,
      color: AppTheme.primaryNavy,
      child: Column(
        children: [
          // Logo Section
          Container(
            padding: const EdgeInsets.all(24),
            child: Row(
              children: [
                Container(
                  width: 45,
                  height: 45,
                  decoration: const BoxDecoration(
                    color: AppTheme.accentGold,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.local_police,
                    color: AppTheme.primaryNavy,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                RichText(
                  text: const TextSpan(
                    children: [
                      TextSpan(
                        text: 'Trust',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      TextSpan(
                        text: 'Bond',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.accentGold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          const Divider(color: Colors.white24, height: 1),
          
          // Menu Items
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 16),
              children: [
                _buildMenuItem(0, Icons.dashboard_outlined, 'Dashboard'),
                _buildMenuItem(1, Icons.description_outlined, 'Reports'),
                _buildMenuItem(2, Icons.people_outline, 'Officers'),
                _buildMenuItem(3, Icons.location_on_outlined, 'Map View'),
                _buildMenuItem(4, Icons.notifications_outlined, 'Alerts'),
                _buildMenuItem(5, Icons.analytics_outlined, 'Analytics'),
                
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  child: Text(
                    'ADMINISTRATION',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.white38,
                      letterSpacing: 1.5,
                    ),
                  ),
                ),
                
                _buildMenuItem(6, Icons.admin_panel_settings_outlined, 'User Management'),
                _buildMenuItem(7, Icons.settings_outlined, 'Settings'),
              ],
            ),
          ),
          
          // Logout Button
          const Divider(color: Colors.white24, height: 1),
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {
                  Navigator.pushReplacementNamed(context, '/login');
                },
                icon: const Icon(Icons.logout, size: 20),
                label: const Text('Sign Out'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white70,
                  side: const BorderSide(color: Colors.white24),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem(int index, IconData icon, String title) {
    final isSelected = selectedIndex == index;
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
      decoration: BoxDecoration(
        color: isSelected ? AppTheme.accentGold.withOpacity(0.15) : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListTile(
        onTap: () => onItemSelected(index),
        leading: Icon(
          icon,
          color: isSelected ? AppTheme.accentGold : Colors.white60,
          size: 22,
        ),
        title: Text(
          title,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.white70,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
            fontSize: 15,
          ),
        ),
        trailing: isSelected
            ? Container(
                width: 4,
                height: 24,
                decoration: BoxDecoration(
                  color: AppTheme.accentGold,
                  borderRadius: BorderRadius.circular(2),
                ),
              )
            : null,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16),
      ),
    );
  }
}
