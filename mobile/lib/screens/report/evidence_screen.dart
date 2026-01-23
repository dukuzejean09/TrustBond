import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/theme.dart';
import '../../models/evidence_model.dart';
import '../../providers/report_provider.dart';

class EvidenceScreen extends StatefulWidget {
  const EvidenceScreen({super.key});

  @override
  State<EvidenceScreen> createState() => _EvidenceScreenState();
}

class _EvidenceScreenState extends State<EvidenceScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isRecording = false;
  int _recordingSeconds = 0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _capturePhoto() {
    final reportProvider = context.read<ReportProvider>();
    
    // Simulate photo capture
    final evidence = EvidenceModel(
      id: 'PHT${DateTime.now().millisecondsSinceEpoch}',
      type: EvidenceType.photo,
      filePath: '/mock/photo_${DateTime.now().millisecondsSinceEpoch}.jpg',
      capturedAt: DateTime.now(),
    );
    
    reportProvider.addEvidence(evidence);
    _showSuccessMessage('Photo captured');
  }

  void _toggleVideoRecording() {
    if (_isRecording) {
      // Stop recording
      final reportProvider = context.read<ReportProvider>();
      final evidence = EvidenceModel(
        id: 'VID${DateTime.now().millisecondsSinceEpoch}',
        type: EvidenceType.video,
        filePath: '/mock/video_${DateTime.now().millisecondsSinceEpoch}.mp4',
        capturedAt: DateTime.now(),
        durationSeconds: _recordingSeconds,
      );
      reportProvider.addEvidence(evidence);
      _showSuccessMessage('Video saved (${_recordingSeconds}s)');
    }
    
    setState(() {
      _isRecording = !_isRecording;
      _recordingSeconds = 0;
    });
    
    if (_isRecording) {
      _startRecordingTimer();
    }
  }

  void _startRecordingTimer() {
    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 1));
      if (!_isRecording) return false;
      setState(() => _recordingSeconds++);
      if (_recordingSeconds >= 60) {
        _toggleVideoRecording();
        return false;
      }
      return true;
    });
  }

  void _toggleAudioRecording() {
    if (_isRecording) {
      // Stop recording
      final reportProvider = context.read<ReportProvider>();
      final evidence = EvidenceModel(
        id: 'AUD${DateTime.now().millisecondsSinceEpoch}',
        type: EvidenceType.audio,
        filePath: '/mock/audio_${DateTime.now().millisecondsSinceEpoch}.m4a',
        capturedAt: DateTime.now(),
        durationSeconds: _recordingSeconds,
      );
      reportProvider.addEvidence(evidence);
      _showSuccessMessage('Audio saved (${_recordingSeconds}s)');
    }
    
    setState(() {
      _isRecording = !_isRecording;
      _recordingSeconds = 0;
    });
    
    if (_isRecording) {
      _startRecordingTimer();
    }
  }

  void _uploadFromGallery(EvidenceType type) {
    final reportProvider = context.read<ReportProvider>();
    final evidence = EvidenceModel(
      id: '${type.name.toUpperCase()}${DateTime.now().millisecondsSinceEpoch}',
      type: type,
      filePath: '/mock/gallery_${DateTime.now().millisecondsSinceEpoch}',
      capturedAt: DateTime.now(),
    );
    reportProvider.addEvidence(evidence);
    _showSuccessMessage('${type.name} uploaded');
  }

  void _showSuccessMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppTheme.successColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final reportProvider = context.watch<ReportProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Add Evidence'),
        actions: [
          if (reportProvider.evidenceList.isNotEmpty)
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text(
                'Done',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: Colors.white,
          tabs: const [
            Tab(icon: Icon(Icons.camera_alt), text: 'Photo'),
            Tab(icon: Icon(Icons.videocam), text: 'Video'),
            Tab(icon: Icon(Icons.mic), text: 'Audio'),
            Tab(icon: Icon(Icons.photo_library), text: 'Gallery'),
          ],
        ),
      ),
      body: Column(
        children: [
          // Evidence count indicator
          if (reportProvider.evidenceList.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(12),
              color: AppTheme.primaryColor.withOpacity(0.1),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.attach_file, size: 18),
                  const SizedBox(width: 8),
                  Text(
                    '${reportProvider.evidenceList.length} file(s) attached',
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            ),
          // Tab content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildPhotoTab(),
                _buildVideoTab(),
                _buildAudioTab(),
                _buildGalleryTab(),
              ],
            ),
          ),
          // Evidence list preview
          if (reportProvider.evidenceList.isNotEmpty)
            Container(
              height: 120,
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 10,
                    offset: const Offset(0, -5),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Padding(
                    padding: EdgeInsets.fromLTRB(16, 12, 16, 8),
                    child: Text(
                      'Captured Evidence',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                  ),
                  Expanded(
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: reportProvider.evidenceList.length,
                      itemBuilder: (context, index) {
                        final evidence = reportProvider.evidenceList[index];
                        return _EvidencePreviewCard(
                          evidence: evidence,
                          onDelete: () {
                            reportProvider.removeEvidence(index);
                          },
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildPhotoTab() {
    return Column(
      children: [
        Expanded(
          child: Container(
            margin: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.black,
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.camera_alt_outlined,
                    size: 80,
                    color: Colors.white38,
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Camera Preview',
                    style: TextStyle(
                      color: Colors.white54,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Gallery button
              IconButton(
                onPressed: () => _uploadFromGallery(EvidenceType.photo),
                icon: const Icon(Icons.photo_library),
                iconSize: 32,
                style: IconButton.styleFrom(
                  backgroundColor: AppTheme.backgroundColor,
                  padding: const EdgeInsets.all(12),
                ),
              ),
              const SizedBox(width: 32),
              // Capture button
              GestureDetector(
                onTap: _capturePhoto,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: AppTheme.primaryColor, width: 4),
                  ),
                  child: Container(
                    margin: const EdgeInsets.all(4),
                    decoration: const BoxDecoration(
                      color: AppTheme.primaryColor,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.camera_alt,
                      color: Colors.white,
                      size: 32,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 32),
              // Switch camera button
              IconButton(
                onPressed: () {},
                icon: const Icon(Icons.flip_camera_ios),
                iconSize: 32,
                style: IconButton.styleFrom(
                  backgroundColor: AppTheme.backgroundColor,
                  padding: const EdgeInsets.all(12),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildVideoTab() {
    return Column(
      children: [
        Expanded(
          child: Container(
            margin: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.black,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Stack(
              children: [
                const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.videocam_outlined,
                        size: 80,
                        color: Colors.white38,
                      ),
                      SizedBox(height: 16),
                      Text(
                        'Video Preview',
                        style: TextStyle(
                          color: Colors.white54,
                          fontSize: 16,
                        ),
                      ),
                    ],
                  ),
                ),
                if (_isRecording && _tabController.index == 1)
                  Positioned(
                    top: 16,
                    right: 16,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.red,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.fiber_manual_record,
                            color: Colors.white,
                            size: 12,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            _formatDuration(_recordingSeconds),
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Text(
                'Max duration: 60 seconds',
                style: TextStyle(
                  color: AppTheme.textSecondary.withOpacity(0.7),
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 16),
              GestureDetector(
                onTap: _toggleVideoRecording,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: _isRecording ? Colors.red : AppTheme.primaryColor,
                      width: 4,
                    ),
                  ),
                  child: Container(
                    margin: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: _isRecording ? Colors.red : AppTheme.primaryColor,
                      shape: _isRecording ? BoxShape.rectangle : BoxShape.circle,
                      borderRadius: _isRecording ? BorderRadius.circular(8) : null,
                    ),
                    child: _isRecording
                        ? const Icon(Icons.stop, color: Colors.white, size: 32)
                        : const Icon(Icons.videocam, color: Colors.white, size: 32),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildAudioTab() {
    return Column(
      children: [
        Expanded(
          child: Container(
            margin: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.backgroundColor,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(32),
                    decoration: BoxDecoration(
                      color: (_isRecording && _tabController.index == 2)
                          ? Colors.red.withOpacity(0.1)
                          : AppTheme.primaryColor.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.mic,
                      size: 80,
                      color: (_isRecording && _tabController.index == 2)
                          ? Colors.red
                          : AppTheme.primaryColor,
                    ),
                  ),
                  const SizedBox(height: 24),
                  if (_isRecording && _tabController.index == 2) ...[
                    Text(
                      _formatDuration(_recordingSeconds),
                      style: const TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.bold,
                        color: Colors.red,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Recording...',
                      style: TextStyle(
                        color: Colors.red,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ] else
                    const Text(
                      'Tap to record audio',
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 16,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Text(
                'Max duration: 120 seconds',
                style: TextStyle(
                  color: AppTheme.textSecondary.withOpacity(0.7),
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 16),
              GestureDetector(
                onTap: _toggleAudioRecording,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: _isRecording ? Colors.red : AppTheme.primaryColor,
                      width: 4,
                    ),
                  ),
                  child: Container(
                    margin: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: _isRecording ? Colors.red : AppTheme.primaryColor,
                      shape: _isRecording ? BoxShape.rectangle : BoxShape.circle,
                      borderRadius: _isRecording ? BorderRadius.circular(8) : null,
                    ),
                    child: _isRecording
                        ? const Icon(Icons.stop, color: Colors.white, size: 32)
                        : const Icon(Icons.mic, color: Colors.white, size: 32),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildGalleryTab() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 40),
          const Icon(
            Icons.cloud_upload_outlined,
            size: 80,
            color: AppTheme.primaryColor,
          ),
          const SizedBox(height: 24),
          const Text(
            'Upload from Gallery',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Select photos, videos, or audio files from your device',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppTheme.textSecondary,
            ),
          ),
          const SizedBox(height: 40),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _UploadOption(
                icon: Icons.image,
                label: 'Photos',
                onTap: () => _uploadFromGallery(EvidenceType.photo),
              ),
              const SizedBox(width: 20),
              _UploadOption(
                icon: Icons.video_library,
                label: 'Videos',
                onTap: () => _uploadFromGallery(EvidenceType.video),
              ),
              const SizedBox(width: 20),
              _UploadOption(
                icon: Icons.audio_file,
                label: 'Audio',
                onTap: () => _uploadFromGallery(EvidenceType.audio),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatDuration(int seconds) {
    final minutes = seconds ~/ 60;
    final secs = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }
}

class _EvidencePreviewCard extends StatelessWidget {
  final EvidenceModel evidence;
  final VoidCallback onDelete;

  const _EvidencePreviewCard({
    required this.evidence,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 80,
      margin: const EdgeInsets.only(right: 12, bottom: 8),
      child: Stack(
        children: [
          Container(
            decoration: BoxDecoration(
              color: AppTheme.backgroundColor,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(evidence.icon, style: const TextStyle(fontSize: 24)),
                const SizedBox(height: 4),
                Text(
                  evidence.typeLabel,
                  style: const TextStyle(fontSize: 10),
                ),
                if (evidence.durationSeconds != null)
                  Text(
                    '${evidence.durationSeconds}s',
                    style: const TextStyle(
                      fontSize: 10,
                      color: AppTheme.textSecondary,
                    ),
                  ),
              ],
            ),
          ),
          Positioned(
            top: 0,
            right: 0,
            child: GestureDetector(
              onTap: onDelete,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: const BoxDecoration(
                  color: AppTheme.errorColor,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.close,
                  size: 12,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _UploadOption extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _UploadOption({
    required this.icon,
    required this.label,
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
          children: [
            Icon(icon, size: 40, color: AppTheme.primaryColor),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
