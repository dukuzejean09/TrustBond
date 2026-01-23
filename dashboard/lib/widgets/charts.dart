import 'package:flutter/material.dart';
import '../config/theme.dart';

class ReportsTrendChart extends StatelessWidget {
  const ReportsTrendChart({super.key});

  @override
  Widget build(BuildContext context) {
    // Simplified chart visualization using custom paint
    return CustomPaint(
      painter: TrendChartPainter(),
      child: const SizedBox.expand(),
    );
  }
}

class TrendChartPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    // Sample data points
    final data = [45, 65, 55, 80, 60, 75, 90];
    final days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    final maxValue = 100.0;
    final width = size.width;
    final height = size.height - 30; // Leave space for labels
    final stepX = width / (data.length - 1);

    // Draw grid lines
    final gridPaint = Paint()
      ..color = Colors.grey.shade200
      ..strokeWidth = 1;

    for (int i = 0; i <= 4; i++) {
      final y = height * i / 4;
      canvas.drawLine(Offset(0, y), Offset(width, y), gridPaint);
    }

    // Draw gradient fill
    final gradientPath = Path();
    final points = <Offset>[];

    for (int i = 0; i < data.length; i++) {
      final x = i * stepX;
      final y = height - (data[i] / maxValue * height);
      points.add(Offset(x, y));
    }

    gradientPath.moveTo(0, height);
    for (final point in points) {
      gradientPath.lineTo(point.dx, point.dy);
    }
    gradientPath.lineTo(width, height);
    gradientPath.close();

    final gradientPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          AppTheme.primaryNavy.withOpacity(0.3),
          AppTheme.primaryNavy.withOpacity(0.05),
        ],
      ).createShader(Rect.fromLTWH(0, 0, width, height));

    canvas.drawPath(gradientPath, gradientPaint);

    // Draw line
    final linePath = Path();
    paint.color = AppTheme.primaryNavy;

    for (int i = 0; i < points.length; i++) {
      if (i == 0) {
        linePath.moveTo(points[i].dx, points[i].dy);
      } else {
        linePath.lineTo(points[i].dx, points[i].dy);
      }
    }

    canvas.drawPath(linePath, paint);

    // Draw points
    final pointPaint = Paint()
      ..color = AppTheme.primaryNavy
      ..style = PaintingStyle.fill;

    final pointBorderPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    for (final point in points) {
      canvas.drawCircle(point, 6, pointBorderPaint);
      canvas.drawCircle(point, 4, pointPaint);
    }

    // Draw labels
    final textPainter = TextPainter(
      textDirection: TextDirection.ltr,
    );

    for (int i = 0; i < days.length; i++) {
      textPainter.text = TextSpan(
        text: days[i],
        style: TextStyle(
          color: Colors.grey.shade600,
          fontSize: 12,
        ),
      );
      textPainter.layout();
      textPainter.paint(
        canvas,
        Offset(i * stepX - textPainter.width / 2, height + 10),
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class ReportsByTypeChart extends StatelessWidget {
  const ReportsByTypeChart({super.key});

  @override
  Widget build(BuildContext context) {
    final types = [
      {'name': 'Theft', 'count': 320, 'color': Colors.orange},
      {'name': 'Fraud', 'count': 245, 'color': Colors.purple},
      {'name': 'Violence', 'count': 180, 'color': Colors.red},
      {'name': 'Traffic', 'count': 156, 'color': Colors.blue},
      {'name': 'Other', 'count': 383, 'color': Colors.grey},
    ];

    final total = types.fold<int>(0, (sum, item) => sum + (item['count'] as int));

    return Column(
      children: types.map((type) {
        final percentage = (type['count'] as int) / total * 100;
        return Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        decoration: BoxDecoration(
                          color: type['color'] as Color,
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        type['name'] as String,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                  Text(
                    '${type['count']} (${percentage.toStringAsFixed(0)}%)',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: Colors.grey.shade700,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: percentage / 100,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: AlwaysStoppedAnimation(type['color'] as Color),
                  minHeight: 8,
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}
