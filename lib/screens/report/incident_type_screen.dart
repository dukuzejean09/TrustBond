import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../models/incident_type.dart';
import '../../providers/report_provider.dart';

class IncidentTypeScreen extends StatefulWidget {
  const IncidentTypeScreen({super.key});

  @override
  State<IncidentTypeScreen> createState() => _IncidentTypeScreenState();
}

class _IncidentTypeScreenState extends State<IncidentTypeScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';
  IncidentCategory? _selectedCategory;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<IncidentType> get _filteredTypes {
    List<IncidentType> types = IncidentType.allTypes;
    
    if (_selectedCategory != null) {
      types = IncidentType.getByCategory(_selectedCategory!);
    }
    
    if (_searchQuery.isNotEmpty) {
      types = IncidentType.search(_searchQuery);
    }
    
    return types;
  }

  Map<IncidentCategory, List<IncidentType>> get _groupedTypes {
    final Map<IncidentCategory, List<IncidentType>> grouped = {};
    for (final type in _filteredTypes) {
      grouped.putIfAbsent(type.category, () => []);
      grouped[type.category]!.add(type);
    }
    return grouped;
  }

  void _selectType(IncidentType type) {
    context.read<ReportProvider>().setIncidentType(type);
    Navigator.pop(context, type);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Incident Type'),
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search incident type...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _searchQuery = '');
                        },
                      )
                    : null,
                filled: true,
                fillColor: Colors.white,
              ),
              onChanged: (value) {
                setState(() => _searchQuery = value);
              },
            ),
          ),
          
          // Category Filter
          SizedBox(
            height: 50,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              children: [
                _CategoryChip(
                  label: 'All',
                  icon: Icons.apps,
                  isSelected: _selectedCategory == null,
                  onTap: () {
                    setState(() => _selectedCategory = null);
                  },
                ),
                ...IncidentCategory.values.map((category) {
                  return _CategoryChip(
                    label: IncidentType.getCategoryName(category).split(' ').first,
                    icon: IncidentType.getCategoryIcon(category),
                    isSelected: _selectedCategory == category,
                    onTap: () {
                      setState(() {
                        _selectedCategory = _selectedCategory == category 
                            ? null 
                            : category;
                      });
                    },
                  );
                }),
              ],
            ),
          ),
          const SizedBox(height: 8),
          
          // Types List
          Expanded(
            child: _searchQuery.isNotEmpty || _selectedCategory != null
                ? _buildFlatList()
                : _buildGroupedList(),
          ),
        ],
      ),
    );
  }

  Widget _buildFlatList() {
    final types = _filteredTypes;
    
    if (types.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.search_off,
              size: 64,
              color: AppTheme.textSecondary.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            const Text(
              'No matching incident types',
              style: TextStyle(
                fontSize: 16,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      );
    }
    
    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: 0.9,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: types.length,
      itemBuilder: (context, index) {
        return _IncidentTypeCard(
          type: types[index],
          onTap: () => _selectType(types[index]),
        );
      },
    );
  }

  Widget _buildGroupedList() {
    final grouped = _groupedTypes;
    
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: grouped.length,
      itemBuilder: (context, index) {
        final category = grouped.keys.elementAt(index);
        final types = grouped[category]!;
        
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: types.first.color.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      IncidentType.getCategoryIcon(category),
                      color: types.first.color,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    IncidentType.getCategoryName(category),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 0.9,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: types.length,
              itemBuilder: (context, typeIndex) {
                return _IncidentTypeCard(
                  type: types[typeIndex],
                  onTap: () => _selectType(types[typeIndex]),
                );
              },
            ),
            const SizedBox(height: 16),
          ],
        );
      },
    );
  }
}

class _CategoryChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _CategoryChip({
    required this.label,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: FilterChip(
        label: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 16,
              color: isSelected ? Colors.white : AppTheme.textSecondary,
            ),
            const SizedBox(width: 4),
            Text(label),
          ],
        ),
        selected: isSelected,
        onSelected: (_) => onTap(),
        selectedColor: AppTheme.primaryColor,
        labelStyle: TextStyle(
          color: isSelected ? Colors.white : AppTheme.textPrimary,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
        ),
        checkmarkColor: Colors.white,
        showCheckmark: false,
      ),
    );
  }
}

class _IncidentTypeCard extends StatelessWidget {
  final IncidentType type;
  final VoidCallback onTap;

  const _IncidentTypeCard({
    required this.type,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: type.color.withOpacity(0.3)),
          boxShadow: [
            BoxShadow(
              color: type.color.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: type.color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                type.icon,
                color: type.color,
                size: 28,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              type.name,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
