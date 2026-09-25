import 'dart:math';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../widgets/hero_section.dart';
import '../widgets/image_section.dart';
import '../widgets/action_buttons.dart';
import '../widgets/language_sheet.dart';
import '../widgets/result_card.dart';
import '../screen/ar_screen.dart';
import 'package:geolocator/geolocator.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();

  XFile? selectedImage;
  String selectedLanguage = 'English';
  bool isAnalyzing = false;
  Map<String, dynamic>? result;

  Future<void> pickImage(ImageSource source) async {
    try {
      final image = await _picker.pickImage(
        source: source,
        imageQuality: 85,
      );

      if (image == null) return;

      setState(() {
        selectedImage = image;
        result = null;
      });
    } catch (e) {
      _showMessage('Could not select image.');
    }
  }

  // ─────────────────────────────────────────────
  // GET CURRENT LOCATION SAFELY
  // ─────────────────────────────────────────────
  Future<Position?> _getCurrentLocationSafely() async {
    try {
      final serviceEnabled =
          await Geolocator.isLocationServiceEnabled();

      if (!serviceEnabled) return null;

      var permission = await Geolocator.checkPermission();

      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();

        if (permission == LocationPermission.denied) {
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return null;
      }

      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
        ),
      );
    } catch (e) {
      return null;
    }
  }

  // ─────────────────────────────────────────────
  // ANALYZE IMAGE
  // ─────────────────────────────────────────────
  Future<void> analyzeImage() async {
    if (selectedImage == null) return;

    setState(() {
      isAnalyzing = true;
      result = null;
    });

    try {
      final imageBytes = await selectedImage!.readAsBytes();

      final position = await _getCurrentLocationSafely();

      final data = await ApiService.identifyImage(
        imageBytes: imageBytes,
        filename: selectedImage!.name,
        language: selectedLanguage,
        latitude: position?.latitude,
        longitude: position?.longitude,
      );

      setState(() => result = data);

      _showMessage('AI analysis completed.');
    } catch (e) {
      _showMessage('Could not connect to LensGuide backend.');
    } finally {
      if (mounted) {
        setState(() => isAnalyzing = false);
      }
    }
  }

  // ─────────────────────────────────────────────
  // HANDLE PS-06 CANDIDATE SELECTION
  // ─────────────────────────────────────────────
  Future<void> _onCandidateSelected(String labelClass) async {
    setState(() => isAnalyzing = true);

    try {
      final position = await _getCurrentLocationSafely();

      final data = await ApiService.selectCandidate(
        labelClass: labelClass,
        language: selectedLanguage,
        latitude: position?.latitude,
        longitude: position?.longitude,
      );

      if (!mounted) return;
      setState(() => result = data);
    } catch (e) {
      _showMessage('Could not resolve the selected place.');
    } finally {
      if (mounted) {
        setState(() => isAnalyzing = false);
      }
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(18),
        duration: const Duration(seconds: 3),
      ),
    );
  }

  // ─────────────────────────────────────────────
  // BUILD
  // ─────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF05040D),
      body: Stack(
        children: [
          // ── COSMIC BACKGROUND — static star-field, painted once,
          // no animation, no per-frame cost. ──
          const Positioned.fill(child: _CosmicBackground()),

          SafeArea(
            child: Column(
              children: [
                _buildTopBar(),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(20, 18, 20, 40),
                    child: Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 1050),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const HeroSection(),
                            const SizedBox(height: 24),
                            ImageSection(selectedImage: selectedImage),
                            const SizedBox(height: 14),
                            ActionButtons(
                              isAnalyzing: isAnalyzing,
                              onPickImage: pickImage,
                            ),
                            const SizedBox(height: 12),
                            _buildAnalyzeButton(),
                            ResultCard(
                              result: result,
                              onCandidateSelected: _onCandidateSelected,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAnalyzeButton() {
    final bool enabled = selectedImage != null && !isAnalyzing;

    return SizedBox(
      width: double.infinity,
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          gradient: enabled
              ? const LinearGradient(
                  colors: [Color(0xFF8B5CF6), Color(0xFF00D9FF)],
                )
              : null,
          boxShadow: enabled
              ? [
                  BoxShadow(
                    color: const Color(0xFF8B5CF6).withValues(alpha: 0.4),
                    blurRadius: 24,
                    offset: const Offset(0, 8),
                  ),
                ]
              : [],
        ),
        child: FilledButton(
          onPressed: enabled ? analyzeImage : null,
          style: FilledButton.styleFrom(
            backgroundColor: Colors.transparent,
            foregroundColor: Colors.white,
            disabledBackgroundColor: Colors.white.withValues(alpha: 0.05),
            disabledForegroundColor: Colors.white38,
            shadowColor: Colors.transparent,
            padding: const EdgeInsets.symmetric(vertical: 18),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
              side: enabled
                  ? BorderSide.none
                  : BorderSide(color: Colors.white.withValues(alpha: 0.1)),
            ),
            elevation: 0,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (isAnalyzing) ...[
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.2,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 10),
                const Text(
                  'Scanning transmission...',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ] else ...[
                const Icon(Icons.auto_awesome, size: 19),
                const SizedBox(width: 9),
                const Text(
                  'Initiate Scan',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  // ─────────────────────────────────────────────
  // RESPONSIVE TOP BAR — MISSION CONTROL STYLE
  // ─────────────────────────────────────────────
  Widget _buildTopBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 14, 24, 14),
      decoration: BoxDecoration(
        color: const Color(0xFF05040D).withValues(alpha: 0.7),
        border: Border(
          bottom: BorderSide(
            color: const Color(0xFF8B5CF6).withValues(alpha: 0.15),
          ),
        ),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isCompact = constraints.maxWidth < 420;

          return Row(
            children: [
              // Logo icon
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF8B5CF6),
                      Color(0xFF00D9FF),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF8B5CF6).withValues(alpha: 0.45),
                      blurRadius: 14,
                      spreadRadius: 1,
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.travel_explore,
                  color: Colors.white,
                  size: 21,
                ),
              ),

              const SizedBox(width: 11),

              // LensGuide title + mission status
              Flexible(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'LENSGUIDE',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: isCompact ? 15 : 18,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 2,
                        color: Colors.white,
                      ),
                    ),
                    if (!isCompact) ...[
                      const SizedBox(height: 2),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 6,
                            height: 6,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: const Color(0xFF00D9FF),
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(0xFF00D9FF).withValues(alpha: 0.8),
                                  blurRadius: 6,
                                  spreadRadius: 1,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            'MISSION • ACTIVE',
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.3,
                              color: const Color(0xFF00D9FF).withValues(alpha: 0.85),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),

              const Spacer(),

              // AR Camera button — Exploration Mode
              GestureDetector(
                onTap: () async {
                  // Get the current identified result.
                  final currentData =
                      result?['translated'] ?? result?['english'] ?? {};

                  final data = currentData is Map ? currentData : {};

                  final poiId = data['poi_id']?.toString();

                  // Temporary fallback: use the verified PS-06 demo POI
                  // whenever the backend hasn't returned a real poi_id
                  // yet. Real poi_id is used exactly as before whenever
                  // present.
                  final poiIdForAR = (poiId != null && poiId.isNotEmpty)
                      ? poiId
                      : 'poi_30fe338a';

                  final poiLat = (data['lat'] is num)
                      ? (data['lat'] as num).toDouble()
                      : null;
                  final poiLng = (data['lng'] is num)
                      ? (data['lng'] as num).toDouble()
                      : null;

                  final position = await _getCurrentLocationSafely();

                  // Safe CIT demo fallback location, used ONLY when
                  // real GPS is unavailable, so bearings stay
                  // meaningful instead of collapsing to 0/North.
                  const double citFallbackLat = 13.012338;
                  const double citFallbackLng = 77.703378;

                  final resolvedUserLat =
                      position?.latitude ?? citFallbackLat;
                  final resolvedUserLng =
                      position?.longitude ?? citFallbackLng;

                  // Combined nearby list: attractions + restaurants +
                  // hotels, unchanged shape.
                  final nearby = data['nearby'];
                  final combinedNearby = <Map<String, dynamic>>[
                    if (nearby is Map) ...[
                      ...List<Map<String, dynamic>>.from(
                        (nearby['attractions'] as List? ?? [])
                            .map((e) => Map<String, dynamic>.from(e)),
                      ),
                      ...List<Map<String, dynamic>>.from(
                        (nearby['restaurants'] as List? ?? [])
                            .map((e) => Map<String, dynamic>.from(e)),
                      ),
                      ...List<Map<String, dynamic>>.from(
                        (nearby['hotels'] as List? ?? [])
                            .map((e) => Map<String, dynamic>.from(e)),
                      ),
                    ],
                  ];

                  if (!context.mounted) return;

                  // Open AR and pass the resolved POI data.
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ARScreen(
                        poiId: poiIdForAR,
                        poiName: data['name']?.toString(),
                        poiLocation: data['location']?.toString(),
                        poiDescription: data['description']?.toString(),
                        poiCategory: data['poi_category']?.toString(),
                        poiEntryFee: data['entry_fee']?.toString(),
                        poiLat: poiLat,
                        poiLng: poiLng,
                        userLat: resolvedUserLat,
                        userLng: resolvedUserLng,
                        nearbyPois: combinedNearby,
                      ),
                    ),
                  );
                },
                child: Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: isCompact ? 9 : 13,
                    vertical: 9,
                  ),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [
                        Color(0xFF8B5CF6),
                        Color(0xFF00D9FF),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF8B5CF6).withValues(alpha: 0.35),
                        blurRadius: 12,
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.view_in_ar,
                        color: Colors.white,
                        size: 18,
                      ),
                      if (!isCompact) ...[
                        const SizedBox(width: 6),
                        const Text(
                          'EXPLORE',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 11.5,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.8,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),

              SizedBox(
                width: isCompact ? 6 : 10,
              ),

              // Language selector
              InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: () => LanguageSheet.show(
                  context: context,
                  selectedLanguage: selectedLanguage,
                  onLanguageSelected: (lang) {
                    setState(() {
                      selectedLanguage = lang;
                      result = null;
                    });
                  },
                ),
                child: Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: isCompact ? 9 : 13,
                    vertical: 9,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.04),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: const Color(0xFF8B5CF6).withValues(alpha: 0.25),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.language_rounded,
                        size: 18,
                        color: Color(0xFF00D9FF),
                      ),

                      const SizedBox(width: 7),

                      ConstrainedBox(
                        constraints: BoxConstraints(
                          maxWidth: isCompact ? 55 : 90,
                        ),
                        child: Text(
                          selectedLanguage,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ),

                      if (!isCompact) ...[
                        const SizedBox(width: 3),
                        const Icon(
                          Icons.keyboard_arrow_down_rounded,
                          size: 18,
                          color: Colors.white54,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

// ─────────────────────────────────────────────
// COSMIC BACKGROUND — deep space gradient + static star-field.
// Stars are generated ONCE with a fixed seed and painted via
// CustomPainter — no animation, no rebuilds, negligible cost.
// Purely decorative; owns no app state or logic.
// ─────────────────────────────────────────────
class _CosmicBackground extends StatelessWidget {
  const _CosmicBackground();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color(0xFF05040D),
            Color(0xFF120B26),
            Color(0xFF0A0715),
          ],
          stops: [0.0, 0.5, 1.0],
        ),
      ),
      child: CustomPaint(
        painter: _StarFieldPainter(),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _StarFieldPainter extends CustomPainter {
  static final List<_Star> _stars = _generateStars(90);

  static List<_Star> _generateStars(int count) {
    final rand = Random(42); // fixed seed — identical star-field every build
    return List.generate(count, (_) {
      return _Star(
        dxFraction: rand.nextDouble(),
        dyFraction: rand.nextDouble(),
        radius: rand.nextDouble() * 1.4 + 0.3,
        opacity: rand.nextDouble() * 0.5 + 0.15,
      );
    });
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (final star in _stars) {
      final paint = Paint()
        ..color = Colors.white.withValues(alpha: star.opacity);
      canvas.drawCircle(
        Offset(star.dxFraction * size.width, star.dyFraction * size.height),
        star.radius,
        paint,
      );
    }

    // A couple of soft violet/cyan nebula glows, very low opacity.
    final glow1 = Paint()
      ..color = const Color(0xFF8B5CF6).withValues(alpha: 0.06)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 80);
    canvas.drawCircle(Offset(size.width * 0.15, size.height * 0.1), 140, glow1);

    final glow2 = Paint()
      ..color = const Color(0xFF00D9FF).withValues(alpha: 0.05)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 100);
    canvas.drawCircle(Offset(size.width * 0.9, size.height * 0.35), 160, glow2);

    final glow3 = Paint()
      ..color = const Color(0xFF8B5CF6).withValues(alpha: 0.05)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 120);
    canvas.drawCircle(Offset(size.width * 0.3, size.height * 0.85), 180, glow3);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _Star {
  final double dxFraction;
  final double dyFraction;
  final double radius;
  final double opacity;

  _Star({
    required this.dxFraction,
    required this.dyFraction,
    required this.radius,
    required this.opacity,
  });
}
