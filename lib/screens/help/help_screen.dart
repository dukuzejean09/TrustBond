import 'package:flutter/material.dart';
import '../../config/theme.dart';

class HelpScreen extends StatelessWidget {
  const HelpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Help & FAQ'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Quick help cards
            Row(
              children: [
                Expanded(
                  child: _QuickHelpCard(
                    icon: Icons.phone,
                    title: 'Emergency',
                    subtitle: 'Call 112',
                    color: AppTheme.accentColor,
                    onTap: () => _showEmergencyDialog(context),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _QuickHelpCard(
                    icon: Icons.chat,
                    title: 'Support',
                    subtitle: 'Chat with us',
                    color: AppTheme.primaryColor,
                    onTap: () => _showSupportDialog(context),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // FAQ Section
            const Text(
              'Frequently Asked Questions',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),

            _FAQItem(
              question: 'How do I report an incident?',
              answer:
                  '1. Tap the "Report Incident" button on the home screen\n'
                  '2. Select the type of incident\n'
                  '3. Provide a detailed description\n'
                  '4. Confirm your location\n'
                  '5. Add evidence (photos, videos, audio) if available\n'
                  '6. Review and submit your report',
            ),
            _FAQItem(
              question: 'Is my report anonymous?',
              answer:
                  'Yes, if you enable anonymous mode, your personal information will not be associated with your report. '
                  'You can toggle anonymous mode in Settings or when creating a report. '
                  'Your identity is protected and authorities will only see the incident details.',
            ),
            _FAQItem(
              question: 'How do I add evidence to my report?',
              answer:
                  'When creating a report, tap on the Photo, Video, or Audio buttons to capture evidence. '
                  'You can also upload files from your gallery. Evidence helps authorities better understand and verify incidents.',
            ),
            _FAQItem(
              question: 'Can I track my report status?',
              answer:
                  'Yes! Go to "My Reports" to see all your submitted reports and their current status. '
                  'Reports go through these stages:\n'
                  '• Submitted - Your report has been received\n'
                  '• Under Review - Authorities are investigating\n'
                  '• Verified - The incident has been confirmed\n'
                  '• Closed - The case has been resolved',
            ),
            _FAQItem(
              question: 'What happens if I have no internet?',
              answer:
                  'You can save reports offline and submit them later when you have an internet connection. '
                  'Go to Settings > Offline Reports to view and manage saved reports.',
            ),
            _FAQItem(
              question: 'What types of incidents can I report?',
              answer:
                  'You can report various incidents including:\n'
                  '• Crimes against persons (assault, threats, harassment)\n'
                  '• Property crimes (theft, vandalism)\n'
                  '• Fraud and financial crimes\n'
                  '• Suspicious activities\n'
                  '• Public order issues\n'
                  '• Traffic and road problems\n'
                  '• Infrastructure issues',
            ),
            _FAQItem(
              question: 'How accurate does my location need to be?',
              answer:
                  'The app will automatically detect your GPS location. You can adjust the pin on the map if needed. '
                  'Accurate location helps authorities respond faster and more effectively.',
            ),
            _FAQItem(
              question: 'Can I delete a report?',
              answer:
                  'You can only delete reports that are still in "Submitted" status. '
                  'Once a report is under review or processed, it cannot be deleted. '
                  'If you submitted a report by mistake, contact support.',
            ),
            const SizedBox(height: 24),

            // Safety Tips Section
            const Text(
              'Safety Tips',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),

            _SafetyTipCard(
              icon: Icons.visibility,
              title: 'Stay Aware',
              tip: 'Always be aware of your surroundings, especially in unfamiliar areas.',
            ),
            _SafetyTipCard(
              icon: Icons.phone,
              title: 'Emergency Numbers',
              tip: 'Save emergency numbers: Police (112), Fire (111), Ambulance (912).',
            ),
            _SafetyTipCard(
              icon: Icons.group,
              title: 'Travel in Groups',
              tip: 'When possible, travel with others, especially at night.',
            ),
            _SafetyTipCard(
              icon: Icons.share_location,
              title: 'Share Your Location',
              tip: 'Let trusted friends or family know your whereabouts.',
            ),
            _SafetyTipCard(
              icon: Icons.lock,
              title: 'Secure Your Belongings',
              tip: 'Keep valuables hidden and secure, especially in public places.',
            ),
            const SizedBox(height: 24),

            // Contact Section
            const Text(
              'Contact Support',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),

            _ContactCard(
              icon: Icons.email,
              title: 'Email',
              value: 'support@crimereport.rw',
              onTap: () {},
            ),
            _ContactCard(
              icon: Icons.phone,
              title: 'Phone',
              value: '+250 788 123 456',
              onTap: () {},
            ),
            _ContactCard(
              icon: Icons.language,
              title: 'Website',
              value: 'www.crimereport.rw',
              onTap: () {},
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  void _showEmergencyDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.emergency, color: AppTheme.accentColor),
            SizedBox(width: 8),
            Text('Emergency Numbers'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _EmergencyNumber(
              service: 'Police',
              number: '112',
              onCall: () {},
            ),
            _EmergencyNumber(
              service: 'Fire Department',
              number: '111',
              onCall: () {},
            ),
            _EmergencyNumber(
              service: 'Ambulance',
              number: '912',
              onCall: () {},
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  void _showSupportDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Contact Support'),
        content: const Text(
          'Our support team is available Monday to Friday, 8 AM to 6 PM.\n\n'
          'For urgent matters, please use the emergency numbers.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              // Open chat or email
            },
            child: const Text('Start Chat'),
          ),
        ],
      ),
    );
  }
}

class _QuickHelpCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _QuickHelpCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: Colors.white, size: 28),
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: color,
                fontSize: 16,
              ),
            ),
            Text(
              subtitle,
              style: TextStyle(
                color: color.withOpacity(0.8),
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FAQItem extends StatefulWidget {
  final String question;
  final String answer;

  const _FAQItem({
    required this.question,
    required this.answer,
  });

  @override
  State<_FAQItem> createState() => _FAQItemState();
}

class _FAQItemState extends State<_FAQItem> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () => setState(() => _isExpanded = !_isExpanded),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.question,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
                  ),
                  Icon(
                    _isExpanded ? Icons.expand_less : Icons.expand_more,
                    color: AppTheme.primaryColor,
                  ),
                ],
              ),
              if (_isExpanded) ...[
                const SizedBox(height: 12),
                const Divider(),
                const SizedBox(height: 8),
                Text(
                  widget.answer,
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    height: 1.5,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _SafetyTipCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String tip;

  const _SafetyTipCard({
    required this.icon,
    required this.title,
    required this.tip,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.successColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: AppTheme.successColor, size: 24),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    tip,
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                      height: 1.4,
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
}

class _ContactCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final VoidCallback onTap;

  const _ContactCard({
    required this.icon,
    required this.title,
    required this.value,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppTheme.primaryColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: AppTheme.primaryColor),
        ),
        title: Text(title),
        subtitle: Text(value),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

class _EmergencyNumber extends StatelessWidget {
  final String service;
  final String number;
  final VoidCallback onCall;

  const _EmergencyNumber({
    required this.service,
    required this.number,
    required this.onCall,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(service),
      subtitle: Text(
        number,
        style: const TextStyle(
          fontWeight: FontWeight.bold,
          fontSize: 18,
          color: AppTheme.accentColor,
        ),
      ),
      trailing: IconButton(
        onPressed: onCall,
        icon: const Icon(Icons.phone, color: AppTheme.successColor),
      ),
    );
  }
}
