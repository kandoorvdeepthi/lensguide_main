import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_compass/flutter_compass.dart';
import 'package:ar_flutter_plugin_plus/ar_flutter_plugin_plus.dart';
import 'package:ar_flutter_plugin_plus/datatypes/config_planedetection.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_session_manager.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_object_manager.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_anchor_manager.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_location_manager.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ARScreen extends StatefulWidget {
  final String? poiId;
  final String? poiName;
  final String? poiLocation;
  final String? poiDescription;
  final String? poiCategory;
  final String? poiEntryFee;
  final double? poiLat;
  final double? poiLng;
  final double? userLat;
  final double? userLng;
  final List<Map<String, dynamic>>? nearbyPois;

  const ARScreen({
    super.key,
    this.poiId,
    this.poiName,
    this.poiLocation,
    this.poiDescription,
    this.poiCategory,
    this.poiEntryFee,
    this.poiLat,
    this.poiLng,
    this.userLat,
    this.userLng,
    this.nearbyPois,
  });

  @override
  State<ARScreen> createState() => _ARScreenState();
}

class _PoiVirtualAnchor {
  final Map<String, dynamic> raw;
  final String poiId;
  final String name;
  final double distanceKm;
  final double bearingDeg;

  _PoiVirtualAnchor({
    required this.raw,
    required this.poiId,
    required this.name,
    required this.distanceKm,
    required this.bearingDeg,
  });
}

class _ARScreenState extends State<ARScreen> with SingleTickerProviderStateMixin {
  // ─────────────────────────────────────────────
  // AR Managers — UNCHANGED
  // ─────────────────────────────────────────────
  ARSessionManager? arSessionManager;
  ARObjectManager? arObjectManager;
  ARAnchorManager? arAnchorManager;

  bool isReady = false;
  String statusMessage = 'Starting AR view...';

  List<_PoiVirtualAnchor> _anchors = [];

  bool _disposed = false;
  bool _arInitialized = false;

  final ValueNotifier<double?> _headingNotifier = ValueNotifier<double?>(null);
  double? _smoothedHeadingInternal;

  StreamSubscription<CompassEvent>? _compassSub;

  final ValueNotifier<String?> _selectedPoiIdNotifier = ValueNotifier<String?>(null);

  bool _panelCheckingXr = false;
  Map<String, dynamic>? _panelXrInfo;

  static const String _backendBase = 'http://10.10.6.208:8000';
  static const double _horizontalFovDeg = 65.0;
  static const double _headingSmoothingAlpha = 0.25;
  static const double _minHeadingDeltaToNotify = 0.4;

  late final AnimationController _pulseController;

  bool _showIntroOverlay = true;
  String _introText = 'SCANNING YOUR SURROUNDINGS...';

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat();

    _buildAnchors();
    _listenToCompassSafely();

    Future.delayed(const Duration(milliseconds: 900), () {
      if (_disposed || !mounted) return;
      setState(() => _introText = 'NEARBY PLACES DETECTED');
    });
    Future.delayed(const Duration(milliseconds: 2100), () {
      if (_disposed || !mounted) return;
      setState(() => _showIntroOverlay = false);
    });
  }

  @override
  void dispose() {
    _disposed = true;
    _compassSub?.cancel();
    _headingNotifier.dispose();
    _selectedPoiIdNotifier.dispose();
    _pulseController.dispose();

    try {
      arSessionManager?.dispose();
    } catch (_) {}

    super.dispose();
  }

  // ─────────────────────────────────────────────
  // BUILD ANCHORS — UNCHANGED
  // ─────────────────────────────────────────────
  void _buildAnchors() {
    final list = widget.nearbyPois ?? [];
    final built = <_PoiVirtualAnchor>[];

    for (final poi in list) {
      final lat = _asDouble(poi['lat']);
      final lng = _asDouble(poi['lng']);
      final distanceKm = _asDouble(poi['distance_km']);

      if (lat == null || lng == null || distanceKm == null) continue;

      double? bearing = _asDouble(poi['bearing_deg']);
      if (bearing == null && widget.userLat != null && widget.userLng != null) {
        bearing = _initialBearingDeg(widget.userLat!, widget.userLng!, lat, lng);
      }
      bearing ??= 0.0;

      built.add(_PoiVirtualAnchor(
        raw: poi,
        poiId: poi['poi_id']?.toString() ?? '',
        name: poi['name']?.toString() ?? 'Nearby place',
        distanceKm: distanceKm,
        bearingDeg: bearing,
      ));
    }

    built.sort((a, b) => a.distanceKm.compareTo(b.distanceKm));

    if (_disposed) return;
    setState(() {
      _anchors = built.take(5).toList();
      statusMessage = _anchors.isEmpty
          ? 'Move your device slowly to discover nearby places.'
          : 'Showing ${_anchors.length} nearby place${_anchors.length > 1 ? 's' : ''}.';
    });
  }

  double? _asDouble(dynamic v) {
    if (v == null) return null;
    if (v is num) return v.toDouble();
    return double.tryParse(v.toString());
  }

  double _initialBearingDeg(double lat1, double lng1, double lat2, double lng2) {
    final phi1 = lat1 * math.pi / 180;
    final phi2 = lat2 * math.pi / 180;
    final dLambda = (lng2 - lng1) * math.pi / 180;
    final y = math.sin(dLambda) * math.cos(phi2);
    final x = math.cos(phi1) * math.sin(phi2) -
        math.sin(phi1) * math.cos(phi2) * math.cos(dLambda);
    final theta = math.atan2(y, x);
    return (theta * 180 / math.pi + 360) % 360;
  }

  // ─────────────────────────────────────────────
  // COMPASS — UNCHANGED
  // ─────────────────────────────────────────────
  void _listenToCompassSafely() {
    try {
      _compassSub = FlutterCompass.events?.listen(
        (event) {
          if (_disposed) return;

          final heading = event.heading;
          if (heading == null || !heading.isFinite) return;

          final normalized = ((heading % 360) + 360) % 360;
          final smoothed = _smoothHeading(_smoothedHeadingInternal, normalized);
          _smoothedHeadingInternal = smoothed;

          final previous = _headingNotifier.value;
          if (previous != null) {
            final delta = (smoothed - previous).abs();
            final wrappedDelta = math.min(delta, 360 - delta);
            if (wrappedDelta < _minHeadingDeltaToNotify) return;
          }

          _headingNotifier.value = smoothed;
        },
        onError: (_) {},
      );
    } catch (e) {
      _headingNotifier.value = null;
    }
  }

  double _smoothHeading(double? previous, double next) {
    if (previous == null) return next;
    final prevRad = previous * math.pi / 180;
    final nextRad = next * math.pi / 180;
    final x = (1 - _headingSmoothingAlpha) * math.cos(prevRad) +
        _headingSmoothingAlpha * math.cos(nextRad);
    final y = (1 - _headingSmoothingAlpha) * math.sin(prevRad) +
        _headingSmoothingAlpha * math.sin(nextRad);
    var result = math.atan2(y, x) * 180 / math.pi;
    if (result < 0) result += 360;
    return result;
  }

  double _relativeBearing(double targetBearingDeg, double? heading) {
    final h = heading ?? 0.0;
    double rel = (targetBearingDeg - h + 540) % 360 - 180;
    return rel;
  }

  double _screenXFor(double targetBearingDeg, double? heading, Size viewSize) {
    final relBearing = _relativeBearing(targetBearingDeg, heading);
    const halfFov = _horizontalFovDeg / 2;
    final centerX = viewSize.width / 2;

    double x;
    if (relBearing.abs() <= halfFov) {
      final t = relBearing / halfFov;
      x = centerX + t * (viewSize.width / 2 - 50);
    } else {
      x = relBearing > 0 ? viewSize.width - 40 : 40;
    }
    return x.clamp(30.0, viewSize.width - 30.0);
  }

  double _opacityFor(double targetBearingDeg, double? heading) {
    final relBearing = _relativeBearing(targetBearingDeg, heading);
    return relBearing.abs() <= _horizontalFovDeg / 2 ? 1.0 : 0.5;
  }

  Offset _poiScreenPosition({
    required double bearingDeg,
    required double distanceKm,
    required double? heading,
    required Size viewSize,
    required double minDistKm,
    required double maxDistKm,
  }) {
    final x = _screenXFor(bearingDeg, heading, viewSize);
    final youY = viewSize.height - 150;

    double t;
    if ((maxDistKm - minDistKm).abs() < 0.0001) {
      t = 0.5;
    } else {
      t = math.sqrt(((distanceKm - minDistKm) / (maxDistKm - minDistKm)).clamp(0.0, 1.0));
    }
    const minY = 140.0;
    final maxY = youY - 30.0;
    final y = (youY - t * (youY - minY)).clamp(minY, maxY);

    return Offset(x, y);
  }

  double _markerScaleFor(double distanceKm, double minDistKm, double maxDistKm) {
    double t;
    if ((maxDistKm - minDistKm).abs() < 0.0001) {
      t = 0.5;
    } else {
      t = math.sqrt(((distanceKm - minDistKm) / (maxDistKm - minDistKm)).clamp(0.0, 1.0));
    }
    return 1.15 - t * 0.35;
  }

  // ─────────────────────────────────────────────
  // XR SCENE CHECK — UNCHANGED
  // ─────────────────────────────────────────────
  Future<void> _checkXrSceneForPanel(String poiId, StateSetter setPanelState) async {
    if (_disposed) return;
    setPanelState(() => _panelCheckingXr = true);
    try {
      final response = await http.get(Uri.parse('$_backendBase/xr_scene?poi_id=$poiId'));
      if (_disposed) return;
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setPanelState(() {
          _panelXrInfo = data['found'] == true ? Map<String, dynamic>.from(data) : null;
          _panelCheckingXr = false;
        });
      } else {
        setPanelState(() => _panelCheckingXr = false);
      }
    } catch (e) {
      if (_disposed) return;
      setPanelState(() => _panelCheckingXr = false);
    }
  }

  // ─────────────────────────────────────────────
  // AR VIEW READY — UNCHANGED
  // ─────────────────────────────────────────────
  void onARViewCreated(
    ARSessionManager sessionManager,
    ARObjectManager objectManager,
    ARAnchorManager anchorManager,
    ARLocationManager locationManager,
  ) {
    if (_arInitialized || _disposed) return;
    _arInitialized = true;

    try {
      arSessionManager = sessionManager;
      arObjectManager = objectManager;
      arAnchorManager = anchorManager;

      arSessionManager!.onInitialize(
        showFeaturePoints: false,
        showPlanes: false,
        customPlaneTexturePath: null,
        showWorldOrigin: false,
      );

      arObjectManager!.onInitialize();

      if (_disposed) return;
      if (!mounted) return;
      setState(() => isReady = true);
    } catch (e) {
      if (_disposed || !mounted) return;
      setState(() {
        isReady = false;
        statusMessage = 'AR could not start on this device.';
      });
    }
  }

  // ─────────────────────────────────────────────
  // CATEGORY ICON — UNCHANGED
  // ─────────────────────────────────────────────
  IconData _iconForCategory(String? category) {
    switch ((category ?? '').toLowerCase()) {
      case 'religious':
        return Icons.temple_hindu_outlined;
      case 'food':
        return Icons.restaurant_outlined;
      case 'shopping':
        return Icons.storefront_outlined;
      case 'heritage':
        return Icons.account_balance_outlined;
      case 'museum':
        return Icons.museum_outlined;
      case 'nature':
        return Icons.park_outlined;
      case 'viewpoint':
        return Icons.landscape_outlined;
      case 'nightlife':
        return Icons.nightlife_outlined;
      case 'wellness':
        return Icons.spa_outlined;
      case 'adventure':
        return Icons.terrain_outlined;
      case 'wildlife':
        return Icons.pets_outlined;
      case 'beach':
        return Icons.beach_access_outlined;
      default:
        return Icons.place_outlined;
    }
  }

  // ─────────────────────────────────────────────
  // POI INFO PANEL — FIXED: SafeArea + SingleChildScrollView +
  // isScrollControlled + maxHeight, so it can never overflow.
  // ─────────────────────────────────────────────
  void _showPoiPanelFor(_PoiVirtualAnchor anchor) {
    if (anchor.poiId.isEmpty && anchor.name == 'Nearby place') {
      return;
    }

    _selectedPoiIdNotifier.value = anchor.poiId;
    _panelXrInfo = null;
    _panelCheckingXr = false;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setPanelState) {
            if (anchor.poiId.isNotEmpty && _panelXrInfo == null && !_panelCheckingXr) {
              _checkXrSceneForPanel(anchor.poiId, setPanelState);
            }

            final category = anchor.raw['poi_category']?.toString();
            final description = anchor.raw['description']?.toString();
            final entryFee = anchor.raw['entry_fee']?.toString();
            final timings = anchor.raw['timings']?.toString();

            return SafeArea(
              child: SingleChildScrollView(
                padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
                child: Container(
                  margin: const EdgeInsets.all(14),
                  padding: const EdgeInsets.all(22),
                  constraints: BoxConstraints(
                    maxHeight: MediaQuery.of(context).size.height * 0.85,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1128).withValues(alpha: 0.92),
                    borderRadius: BorderRadius.circular(26),
                    border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.2)),
                    boxShadow: [
                      BoxShadow(color: Colors.black.withValues(alpha: 0.4), blurRadius: 24, offset: const Offset(0, 8)),
                    ],
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(colors: [Color(0xFF00D9FF), Color(0xFF7C5CFF)]),
                              shape: BoxShape.circle,
                              boxShadow: [BoxShadow(color: const Color(0xFF00D9FF).withValues(alpha: 0.4), blurRadius: 12)],
                            ),
                            child: Icon(_iconForCategory(category), color: Colors.white, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(anchor.name, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, color: Colors.white)),
                                Text(
                                  'poi_id: ${anchor.poiId.isEmpty ? "unknown" : anchor.poiId}',
                                  style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 10.5),
                                ),
                              ],
                            ),
                          ),
                          GestureDetector(
                            onTap: () {
                              _selectedPoiIdNotifier.value = null;
                              Navigator.pop(context);
                            },
                            child: Container(
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.08), shape: BoxShape.circle),
                              child: const Icon(Icons.close, size: 16, color: Colors.white),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      if (description != null && description.isNotEmpty)
                        Text(description, style: TextStyle(fontSize: 13.5, height: 1.5, color: Colors.white.withValues(alpha: 0.8))),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          if (category != null && category.isNotEmpty) _glassChip(_iconForCategory(category), category),
                          if (timings != null && timings.isNotEmpty && timings != 'Not available')
                            _glassChip(Icons.schedule_rounded, timings),
                          if (entryFee != null && entryFee.isNotEmpty) _glassChip(Icons.confirmation_number_outlined, entryFee),
                          _glassChip(
                            Icons.social_distance,
                            anchor.distanceKm < 1
                                ? '${(anchor.distanceKm * 1000).toStringAsFixed(0)} m away'
                                : '${anchor.distanceKm.toStringAsFixed(1)} km away',
                          ),
                          _glassChip(
                            Icons.view_in_ar,
                            _panelCheckingXr ? 'Checking XR...' : (_panelXrInfo != null ? 'XR available' : 'No XR scene'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: () {
                            _selectedPoiIdNotifier.value = null;
                            Navigator.pop(context);
                          },
                          icon: Icon(_panelXrInfo != null ? Icons.view_in_ar_rounded : Icons.explore_outlined, size: 18),
                          label: Text(_panelXrInfo != null ? 'View XR' : 'Explore this place'),
                          style: FilledButton.styleFrom(
                            backgroundColor: const Color(0xFF00D9FF),
                            foregroundColor: const Color(0xFF04101A),
                            padding: const EdgeInsets.symmetric(vertical: 15),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                            elevation: 0,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    ).whenComplete(() {
      if (!_disposed) _selectedPoiIdNotifier.value = null;
    });
  }

  Widget _glassChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.14)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: const Color(0xFF6FE0FF)),
          const SizedBox(width: 5),
          Text(label, style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: Colors.white.withValues(alpha: 0.9))),
        ],
      ),
    );
  }

  // ─────────────────────────────────────────────
  // BUILD
  // ─────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: LayoutBuilder(
        builder: (context, constraints) {
          final viewSize = Size(constraints.maxWidth, constraints.maxHeight);
          final isSmallScreen = viewSize.width < 360;
          final youPos = Offset(viewSize.width / 2, viewSize.height - 150);

          return Stack(
            children: [
              RepaintBoundary(
                child: ARView(
                  onARViewCreated: onARViewCreated,
                  planeDetectionConfig: PlaneDetectionConfig.horizontalAndVertical,
                ),
              ),

              IgnorePointer(
                child: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.black.withValues(alpha: 0.55),
                        Colors.transparent,
                        Colors.transparent,
                        Colors.black.withValues(alpha: 0.45),
                      ],
                      stops: const [0.0, 0.22, 0.72, 1.0],
                    ),
                  ),
                ),
              ),

              ValueListenableBuilder<double?>(
                valueListenable: _headingNotifier,
                builder: (context, heading, _) {
                  double minDist = 0, maxDist = 1;
                  if (_anchors.isNotEmpty) {
                    minDist = _anchors.map((a) => a.distanceKm).reduce(math.min);
                    maxDist = _anchors.map((a) => a.distanceKm).reduce(math.max);
                  }

                  final northX = _screenXFor(0.0, heading, viewSize);
                  final northOpacity = _opacityFor(0.0, heading);

                  return ValueListenableBuilder<String?>(
                    valueListenable: _selectedPoiIdNotifier,
                    builder: (context, selectedId, __) {
                      Offset? selectedPos;
                      if (selectedId != null) {
                        for (final a in _anchors) {
                          if (a.poiId == selectedId) {
                            selectedPos = _poiScreenPosition(
                              bearingDeg: a.bearingDeg,
                              distanceKm: a.distanceKm,
                              heading: heading,
                              viewSize: viewSize,
                              minDistKm: minDist,
                              maxDistKm: maxDist,
                            );
                            break;
                          }
                        }
                      }

                      return Stack(
                        children: [
                          if (selectedPos != null)
                            Positioned.fill(
                              child: IgnorePointer(
                                child: CustomPaint(
                                  painter: _ConnectionLinePainter(from: youPos, to: selectedPos),
                                ),
                              ),
                            ),

                          AnimatedPositioned(
                            duration: const Duration(milliseconds: 120),
                            curve: Curves.linear,
                            left: northX - 22,
                            top: 116,
                            child: AnimatedOpacity(
                              duration: const Duration(milliseconds: 200),
                              opacity: northOpacity,
                              child: Column(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(6),
                                    decoration: BoxDecoration(
                                      color: Colors.white.withValues(alpha: 0.1),
                                      shape: BoxShape.circle,
                                      border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.4)),
                                      boxShadow: [
                                        BoxShadow(color: const Color(0xFF00D9FF).withValues(alpha: 0.25), blurRadius: 8),
                                      ],
                                    ),
                                    child: const Icon(Icons.navigation_rounded, color: Color(0xFF6FE0FF), size: 15),
                                  ),
                                  const SizedBox(height: 3),
                                  const Text(
                                    'N',
                                    style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1.5),
                                  ),
                                ],
                              ),
                            ),
                          ),

                          for (final anchor in _anchors)
                            Builder(
                              builder: (context) {
                                final pos = _poiScreenPosition(
                                  bearingDeg: anchor.bearingDeg,
                                  distanceKm: anchor.distanceKm,
                                  heading: heading,
                                  viewSize: viewSize,
                                  minDistKm: minDist,
                                  maxDistKm: maxDist,
                                );
                                final baseOpacity = _opacityFor(anchor.bearingDeg, heading);
                                final baseScale = _markerScaleFor(anchor.distanceKm, minDist, maxDist);
                                final isSelected = anchor.poiId == selectedId && anchor.poiId.isNotEmpty;
                                final catIcon = _iconForCategory(anchor.raw['poi_category']?.toString());

                                return AnimatedPositioned(
                                  duration: const Duration(milliseconds: 120),
                                  curve: Curves.linear,
                                  left: pos.dx - 42,
                                  top: pos.dy - 46,
                                  child: AnimatedOpacity(
                                    duration: const Duration(milliseconds: 200),
                                    opacity: baseOpacity,
                                    child: AnimatedBuilder(
                                      animation: _pulseController,
                                      builder: (context, child) {
                                        final scale = isSelected ? baseScale * 1.18 : baseScale;
                                        return Transform.scale(scale: scale, child: child);
                                      },
                                      child: GestureDetector(
                                        onTap: () => _showPoiPanelFor(anchor),
                                        behavior: HitTestBehavior.opaque,
                                        child: Column(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            AnimatedBuilder(
                                              animation: _pulseController,
                                              builder: (context, _) {
                                                final ring = isSelected
                                                    ? (0.5 + 0.5 * math.sin(_pulseController.value * 2 * math.pi))
                                                    : 0.0;
                                                return Container(
                                                  padding: const EdgeInsets.all(11),
                                                  decoration: BoxDecoration(
                                                    gradient: LinearGradient(
                                                      begin: Alignment.topLeft,
                                                      end: Alignment.bottomRight,
                                                      colors: isSelected
                                                          ? const [Color(0xFF00D9FF), Color(0xFF7C5CFF)]
                                                          : const [Color(0xFFFF6B4A), Color(0xFFFF3D3D)],
                                                    ),
                                                    shape: BoxShape.circle,
                                                    border: Border.all(
                                                      color: Colors.white.withValues(alpha: isSelected ? 0.9 : 0.55),
                                                      width: isSelected ? 2 : 1.4,
                                                    ),
                                                    boxShadow: [
                                                      BoxShadow(
                                                        color: (isSelected ? const Color(0xFF00D9FF) : const Color(0xFFFF5A3D))
                                                            .withValues(alpha: isSelected ? 0.35 + 0.35 * ring : 0.5),
                                                        blurRadius: isSelected ? 16 + 10 * ring : 13,
                                                        spreadRadius: isSelected ? 2 + 2 * ring : 2,
                                                      ),
                                                    ],
                                                  ),
                                                  child: Icon(catIcon, color: Colors.white, size: 19),
                                                );
                                              },
                                            ),
                                            const SizedBox(height: 5),
                                            Container(
                                              constraints: const BoxConstraints(maxWidth: 110),
                                              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
                                              decoration: BoxDecoration(
                                                color: const Color(0xFF0D1128).withValues(alpha: 0.72),
                                                borderRadius: BorderRadius.circular(10),
                                                border: Border.all(
                                                  color: (isSelected ? const Color(0xFF00D9FF) : Colors.white)
                                                      .withValues(alpha: isSelected ? 0.5 : 0.14),
                                                ),
                                              ),
                                              child: Column(
                                                children: [
                                                  Text(
                                                    anchor.name,
                                                    maxLines: 1,
                                                    overflow: TextOverflow.ellipsis,
                                                    textAlign: TextAlign.center,
                                                    style: TextStyle(
                                                      color: Colors.white,
                                                      fontSize: isSmallScreen ? 10 : 11,
                                                      fontWeight: FontWeight.w800,
                                                    ),
                                                  ),
                                                  Text(
                                                    anchor.distanceKm < 1
                                                        ? '${(anchor.distanceKm * 1000).toStringAsFixed(0)} m'
                                                        : '${anchor.distanceKm.toStringAsFixed(1)} km',
                                                    style: const TextStyle(
                                                      color: Color(0xFFFFB98C),
                                                      fontSize: 9.5,
                                                      fontWeight: FontWeight.w700,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                        ],
                      );
                    },
                  );
                },
              ),

              Positioned(
                left: youPos.dx - 28,
                top: youPos.dy - 28,
                child: AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    final pulse = _pulseController.value;
                    return Column(
                      children: [
                        SizedBox(
                          width: 56,
                          height: 56,
                          child: Stack(
                            alignment: Alignment.center,
                            children: [
                              Opacity(
                                opacity: (1 - pulse).clamp(0.0, 1.0),
                                child: Container(
                                  width: 20 + pulse * 36,
                                  height: 20 + pulse * 36,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(color: const Color(0xFF4C8DFF), width: 2),
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.all(11),
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(colors: [Color(0xFF4C8DFF), Color(0xFF2154D9)]),
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.white, width: 2.5),
                                  boxShadow: [
                                    BoxShadow(color: const Color(0xFF2154D9).withValues(alpha: 0.5), blurRadius: 10, spreadRadius: 1),
                                  ],
                                ),
                                child: const Icon(Icons.navigation_rounded, color: Colors.white, size: 20),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'YOU',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10.5,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1.2,
                            shadows: [Shadow(color: Colors.black, blurRadius: 4)],
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),

              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0D1128).withValues(alpha: 0.55),
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                      ),
                      child: Row(
                        children: [
                          GestureDetector(
                            onTap: () => Navigator.pop(context),
                            child: Container(
                              width: 34,
                              height: 34,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.08),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 14),
                            ),
                          ),
                          const SizedBox(width: 10),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  'LENS GUIDE',
                                  style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w900, letterSpacing: 1.2),
                                ),
                                Text(
                                  'NEARBY DISCOVERY',
                                  style: TextStyle(color: Color(0xFF6FE0FF), fontSize: 9.5, fontWeight: FontWeight.w700, letterSpacing: 1.5),
                                ),
                              ],
                            ),
                          ),
                          AnimatedBuilder(
                            animation: _pulseController,
                            builder: (context, _) {
                              final opacity = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(_pulseController.value * 2 * math.pi));
                              return Container(
                                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.black.withValues(alpha: 0.3),
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(
                                    color: (isReady ? const Color(0xFF3DDC84) : Colors.orange).withValues(alpha: 0.5),
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Container(
                                      width: 6,
                                      height: 6,
                                      decoration: BoxDecoration(
                                        shape: BoxShape.circle,
                                        color: (isReady ? const Color(0xFF3DDC84) : Colors.orange).withValues(alpha: opacity),
                                      ),
                                    ),
                                    const SizedBox(width: 5),
                                    Text(
                                      isReady ? 'AR ACTIVE' : 'STARTING',
                                      style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.4),
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),

              Positioned(
                top: 78,
                left: 0,
                right: 0,
                child: SafeArea(
                  bottom: false,
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0D1128).withValues(alpha: 0.5),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.25)),
                      ),
                      child: Text(
                        _anchors.isEmpty ? '✦ SCANNING SURROUNDINGS...' : '✦ ${_anchors.length} NEARBY PLACE${_anchors.length > 1 ? 'S' : ''}',
                        style: const TextStyle(color: Color(0xFF6FE0FF), fontSize: 10.5, fontWeight: FontWeight.w800, letterSpacing: 1.1),
                      ),
                    ),
                  ),
                ),
              ),

              Positioned(
                bottom: 24,
                left: 20,
                right: 20,
                child: SafeArea(
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0D1128).withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                      ),
                      child: Text(
                        _anchors.isEmpty
                            ? 'Move your device slowly to discover nearby places.'
                            : statusMessage,
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 12),
                      ),
                    ),
                  ),
                ),
              ),

              if (_showIntroOverlay)
                Positioned.fill(
                  child: IgnorePointer(
                    child: Container(
                      color: Colors.black.withValues(alpha: 0.45),
                      child: Center(
                        child: AnimatedSwitcher(
                          duration: const Duration(milliseconds: 400),
                          child: Container(
                            key: ValueKey(_introText),
                            padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 14),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0D1128).withValues(alpha: 0.75),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.35)),
                              boxShadow: [
                                BoxShadow(color: const Color(0xFF00D9FF).withValues(alpha: 0.2), blurRadius: 20),
                              ],
                            ),
                            child: Text(
                              _introText,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 1.3,
                              ),
                            ),
                          ),
                        ),
                      ),
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

class _ConnectionLinePainter extends CustomPainter {
  final Offset from;
  final Offset to;

  _ConnectionLinePainter({required this.from, required this.to});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..shader = LinearGradient(
        colors: [
          const Color(0xFF00D9FF).withValues(alpha: 0.05),
          const Color(0xFF00D9FF).withValues(alpha: 0.4),
        ],
      ).createShader(Rect.fromPoints(from, to))
      ..strokeWidth = 1.6
      ..style = PaintingStyle.stroke;

    final dashPath = Path();
    const dashLength = 6.0;
    const gapLength = 5.0;
    final total = (to - from).distance;
    final direction = (to - from) / total;
    double covered = 0;
    while (covered < total) {
      final start = from + direction * covered;
      final end = from + direction * math.min(covered + dashLength, total);
      dashPath.moveTo(start.dx, start.dy);
      dashPath.lineTo(end.dx, end.dy);
      covered += dashLength + gapLength;
    }

    canvas.drawPath(dashPath, paint);
  }

  @override
  bool shouldRepaint(covariant _ConnectionLinePainter oldDelegate) =>
      oldDelegate.from != from || oldDelegate.to != to;
}