enum EvidenceType {
  photo,
  video,
  audio,
}

class EvidenceModel {
  final String id;
  final EvidenceType type;
  final String filePath;
  final DateTime capturedAt;
  final int? durationSeconds;
  final String? thumbnail;

  EvidenceModel({
    required this.id,
    required this.type,
    required this.filePath,
    required this.capturedAt,
    this.durationSeconds,
    this.thumbnail,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type.name,
      'filePath': filePath,
      'capturedAt': capturedAt.toIso8601String(),
      'durationSeconds': durationSeconds,
      'thumbnail': thumbnail,
    };
  }

  factory EvidenceModel.fromJson(Map<String, dynamic> json) {
    return EvidenceModel(
      id: json['id'],
      type: EvidenceType.values.firstWhere((e) => e.name == json['type']),
      filePath: json['filePath'],
      capturedAt: DateTime.parse(json['capturedAt']),
      durationSeconds: json['durationSeconds'],
      thumbnail: json['thumbnail'],
    );
  }

  String get typeLabel {
    switch (type) {
      case EvidenceType.photo:
        return 'Photo';
      case EvidenceType.video:
        return 'Video';
      case EvidenceType.audio:
        return 'Audio';
    }
  }

  String get icon {
    switch (type) {
      case EvidenceType.photo:
        return '📷';
      case EvidenceType.video:
        return '🎥';
      case EvidenceType.audio:
        return '🎤';
    }
  }
}
