import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smooth_page_indicator/smooth_page_indicator.dart';
import '../config/theme.dart';
import '../providers/app_provider.dart';
import 'main_navigation.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<OnboardingItem> _items = [
    OnboardingItem(
      icon: Icons.report_problem_rounded,
      title: 'Report Incidents Easily',
      description:
          'Quickly report any crime or suspicious activity in your community with just a few taps.',
      color: const Color(0xFF1E3A5F),
    ),
    OnboardingItem(
      icon: Icons.security_rounded,
      title: 'Anonymous Protection',
      description:
          'Your identity is protected. Report anonymously without fear of retaliation.',
      color: const Color(0xFF4CAF50),
    ),
    OnboardingItem(
      icon: Icons.camera_alt_rounded,
      title: 'Capture Evidence',
      description:
          'Take photos, videos, or audio recordings to support your report with evidence.',
      color: const Color(0xFFFF9800),
    ),
    OnboardingItem(
      icon: Icons.track_changes_rounded,
      title: 'Track Report Status',
      description:
          'Stay updated on the progress of your reports from submission to resolution.',
      color: const Color(0xFF2196F3),
    ),
  ];

  void _nextPage() {
    if (_currentPage < _items.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _getStarted();
    }
  }

  void _getStarted() {
    context.read<AppProvider>().setFirstTimeComplete();
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const MainNavigation()),
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            // Skip button
            Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: TextButton(
                  onPressed: _getStarted,
                  child: const Text(
                    'Skip',
                    style: TextStyle(
                      fontSize: 16,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ),
              ),
            ),
            // Page content
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: _items.length,
                onPageChanged: (index) {
                  setState(() => _currentPage = index);
                },
                itemBuilder: (context, index) {
                  return _buildPage(_items[index]);
                },
              ),
            ),
            // Page indicator
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: SmoothPageIndicator(
                controller: _pageController,
                count: _items.length,
                effect: const WormEffect(
                  dotHeight: 10,
                  dotWidth: 10,
                  spacing: 12,
                  activeDotColor: AppTheme.primaryColor,
                  dotColor: AppTheme.dividerColor,
                ),
              ),
            ),
            // Buttons
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
              child: Row(
                children: [
                  if (_currentPage > 0)
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          _pageController.previousPage(
                            duration: const Duration(milliseconds: 300),
                            curve: Curves.easeInOut,
                          );
                        },
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text('Back'),
                      ),
                    ),
                  if (_currentPage > 0) const SizedBox(width: 16),
                  Expanded(
                    flex: _currentPage > 0 ? 1 : 2,
                    child: ElevatedButton(
                      onPressed: _nextPage,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: Text(
                        _currentPage == _items.length - 1
                            ? 'Get Started'
                            : 'Next',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPage(OnboardingItem item) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Icon container
          Container(
            width: 160,
            height: 160,
            decoration: BoxDecoration(
              color: item.color.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  color: item.color.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  item.icon,
                  size: 60,
                  color: item.color,
                ),
              ),
            ),
          ),
          const SizedBox(height: 48),
          // Title
          Text(
            item.title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 16),
          // Description
          Text(
            item.description,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 16,
              color: AppTheme.textSecondary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

class OnboardingItem {
  final IconData icon;
  final String title;
  final String description;
  final Color color;

  OnboardingItem({
    required this.icon,
    required this.title,
    required this.description,
    required this.color,
  });
}
