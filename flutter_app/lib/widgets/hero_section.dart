import 'dart:math';
import 'package:flutter/material.dart';

class HeroSection extends StatefulWidget {
  const HeroSection({super.key});

  @override
  State<HeroSection> createState() => _HeroSectionState();
}

class _HeroSectionState extends State<HeroSection>
    with SingleTickerProviderStateMixin {
  // Single shared slow controller drives star twinkle + nebula/
  // supernova pulse. One ticker, low-cost, this screen has no
  // camera/AR view competing for frame budget.
  late final AnimationController _cosmicController;

  @override
  void initState() {
    super.initState();
    _cosmicController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    )..repeat();
  }

  @override
  void dispose() {
    _cosmicController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(28),
      child: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.15)),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF6D5CFF).withValues(alpha: 0.1),
              blurRadius: 40,
              offset: const Offset(0, 12),
            ),
          ],
        ),
        child: Stack(
          children: [
            // ── BASE DEEP-SPACE GRADIENT ──
            Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF0A0E24), Color(0xFF141033), Color(0xFF080615)],
                ),
              ),
            ),

            // ── ANIMATED COSMIC LAYER — stars, nebula, supernova.
            // Purely decorative CustomPaint; never intercepts touch. ──
            Positioned.fill(
              child: IgnorePointer(
                child: AnimatedBuilder(
                  animation: _cosmicController,
                  builder: (context, _) {
                    return CustomPaint(
                      painter: _CosmicScenePainter(_cosmicController.value),
                    );
                  },
                ),
              ),
            ),

            // ── SUBTLE VIGNETTE so text stays legible over the
            // nebula/supernova glow regardless of screen size ──
            Positioned.fill(
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.black.withValues(alpha: 0.15),
                        Colors.transparent,
                        Colors.black.withValues(alpha: 0.25),
                      ],
                      stops: const [0.0, 0.4, 1.0],
                    ),
                  ),
                ),
              ),
            ),

            // ── FOREGROUND CONTENT — unchanged text/copy ──
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 30, 28, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00D9FF).withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.3)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.auto_awesome, color: Color(0xFF00D9FF), size: 15),
                        SizedBox(width: 7),
                        Text(
                          'AI-POWERED TRAVEL',
                          style: TextStyle(
                            color: Color(0xFF6FE0FF),
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 22),
                  const Text(
                    'See the world.\nUnderstand it.',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 34,
                      height: 1.08,
                      fontWeight: FontWeight.w900,
                      letterSpacing: -1,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Point your camera at a landmark, sign or menu '
                    'and let LensGuide turn what you see into useful '
                    'travel information.',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.68),
                      fontSize: 15,
                      height: 1.55,
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

// ─────────────────────────────────────────────
// COSMIC SCENE PAINTER — fixed star layout (stable seed) with a
// gentle twinkle, one slow-pulsing nebula, and one slow-pulsing
// supernova glow. All confined to this widget's own bounds via
// the outer ClipRRect, so it never bleeds outside the card.
// ─────────────────────────────────────────────
class _CosmicScenePainter extends CustomPainter {
  final double t; // 0..1, looping

  _CosmicScenePainter(this.t);

  static final List<_Star> _stars = _generateStars(70);

  static List<_Star> _generateStars(int count) {
    final rand = Random(7); // fixed seed — identical star field every build
    return List.generate(count, (i) {
      return _Star(
        dxFraction: rand.nextDouble(),
        dyFraction: rand.nextDouble(),
        radius: rand.nextDouble() * 1.3 + 0.3,
        baseOpacity: rand.nextDouble() * 0.4 + 0.2,
        twinklePhase: rand.nextDouble() * 2 * pi,
        twinkleSpeed: rand.nextDouble() * 1.5 + 0.5,
      );
    });
  }

  @override
  void paint(Canvas canvas, Size size) {
    // ── NEBULA — soft, slow-pulsing violet/blue cloud, upper-left ──
    final nebulaPulse = 0.5 + 0.5 * sin(t * 2 * pi);
    final nebulaPaint = Paint()
      ..color = const Color(0xFF7C5CFF).withValues(alpha: 0.07 + 0.03 * nebulaPulse)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 70);
    canvas.drawCircle(Offset(size.width * 0.18, size.height * 0.15), 130, nebulaPaint);

    final nebulaPaint2 = Paint()
      ..color = const Color(0xFF3B6BFF).withValues(alpha: 0.05 + 0.02 * nebulaPulse)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 90);
    canvas.drawCircle(Offset(size.width * 0.05, size.height * 0.55), 150, nebulaPaint2);

    // ── SUPERNOVA — bright pulsing point of light, background only,
    // positioned toward the upper-right so it never sits under text ──
    final novaCenter = Offset(size.width * 0.85, size.height * 0.22);
    final novaPulse = 0.5 + 0.5 * sin(t * 2 * pi * 0.6 + pi / 3);

    final novaHalo = Paint()
      ..color = const Color(0xFF9AD8FF).withValues(alpha: 0.05 + 0.04 * novaPulse)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 110);
    canvas.drawCircle(novaCenter, 160, novaHalo);

    final novaCore = Paint()
      ..color = Colors.white.withValues(alpha: 0.12 + 0.08 * novaPulse)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 24);
    canvas.drawCircle(novaCenter, 18 + 6 * novaPulse, novaCore);

    final novaBright = Paint()
      ..color = Colors.white.withValues(alpha: 0.55 + 0.25 * novaPulse);
    canvas.drawCircle(novaCenter, 2.5, novaBright);

    // ── STARS — gentle individual twinkle via phase-shifted sine ──
    for (final star in _stars) {
      final twinkle = 0.5 + 0.5 * sin(t * 2 * pi * star.twinkleSpeed + star.twinklePhase);
      final opacity = (star.baseOpacity * (0.6 + 0.4 * twinkle)).clamp(0.0, 1.0);
      final paint = Paint()..color = Colors.white.withValues(alpha: opacity);
      canvas.drawCircle(
        Offset(star.dxFraction * size.width, star.dyFraction * size.height),
        star.radius,
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _CosmicScenePainter oldDelegate) => oldDelegate.t != t;
}

class _Star {
  final double dxFraction;
  final double dyFraction;
  final double radius;
  final double baseOpacity;
  final double twinklePhase;
  final double twinkleSpeed;

  _Star({
    required this.dxFraction,
    required this.dyFraction,
    required this.radius,
    required this.baseOpacity,
    required this.twinklePhase,
    required this.twinkleSpeed,
  });
}