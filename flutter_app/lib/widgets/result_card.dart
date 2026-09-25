import 'package:flutter/material.dart';
import 'nearby_places.dart';

class ResultCard extends StatelessWidget {
  final Map<String, dynamic>? result;
  final void Function(String labelClass)? onCandidateSelected;

  const ResultCard({
    super.key,
    required this.result,
    this.onCandidateSelected,
  });

  @override
  Widget build(BuildContext context) {
    if (result == null) return const SizedBox.shrink();

    final status = result!['status'];

    if (status == 'selection_required') {
      return _buildSelectionRequired(context);
    }

    if (status == 'not_identified' || status == 'not_recognized') {
      return _buildUnknown();
    }

    final category = result!['category'];

    final rawData =
        result!['translated'] ?? result!['english'] ?? result!['data'] ?? {};

    final data = rawData is Map
        ? Map<String, dynamic>.from(rawData)
        : <String, dynamic>{};

    if (category == 'landmark') {
      return _buildLandmark(data);
    }

    if (category == 'menu_or_sign') {
      return _buildText(data);
    }

    // Some backend responses may identify text without explicitly
    // setting category. Detect that safely without affecting landmarks.
    if (data['CONTENT'] != null ||
        data['content'] != null ||
        data['original_text'] != null ||
        data['source_text'] != null ||
        data['translated_text'] != null) {
      return _buildText(data);
    }

    return const SizedBox.shrink();
  }

  BoxDecoration get _cardDecoration => BoxDecoration(
        color: const Color(0xFF12172A),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(
          color: Colors.white.withValues(alpha: 0.07),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 30,
            offset: const Offset(0, 12),
          ),
        ],
      );

  Widget _buildResultHeader({
    required String title,
    required String subtitle,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [
                Color(0xFF00D9FF),
                Color(0xFF315BEA),
              ],
            ),
            borderRadius: BorderRadius.circular(15),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF00D9FF).withValues(alpha: 0.35),
                blurRadius: 14,
              ),
            ],
          ),
          child: const Icon(
            Icons.auto_awesome,
            color: Colors.white,
            size: 23,
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 9,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFF00D9FF).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color:
                        const Color(0xFF00D9FF).withValues(alpha: 0.25),
                  ),
                ),
                child: const Text(
                  'AI IDENTIFIED',
                  style: TextStyle(
                    color: Color(0xFF6FE0FF),
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -0.5,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.5),
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildLandmark(Map<String, dynamic> data) {
    final name = data['name']?.toString() ?? 'Unknown landmark';
    final location = data['location']?.toString() ?? 'Unknown location';
    final description = data['description']?.toString() ?? '';
    final timings = data['timings']?.toString() ?? 'Not available';
    final entryFee = data['entry_fee']?.toString() ?? 'Not available';
    final bestTime = data['best_time']?.toString() ?? 'Not available';
    final funFact = data['fun_fact']?.toString() ?? 'Not available';

    return Container(
      margin: const EdgeInsets.only(top: 28),
      padding: const EdgeInsets.all(24),
      decoration: _cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildResultHeader(
            title: name,
            subtitle: location,
          ),
          const SizedBox(height: 24),
          if (description.isNotEmpty) _buildDescription(description),
          const SizedBox(height: 22),
          const Text(
            'VISITOR INFORMATION',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: Color(0xFF6FA0FF),
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final twoColumns = constraints.maxWidth > 600;

              return Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  SizedBox(
                    width: twoColumns
                        ? (constraints.maxWidth - 12) / 2
                        : constraints.maxWidth,
                    child: _buildInfoCard(
                      Icons.schedule_rounded,
                      'Timings',
                      timings,
                    ),
                  ),
                  SizedBox(
                    width: twoColumns
                        ? (constraints.maxWidth - 12) / 2
                        : constraints.maxWidth,
                    child: _buildInfoCard(
                      Icons.currency_rupee_rounded,
                      'Entry fee',
                      entryFee,
                    ),
                  ),
                  SizedBox(
                    width: twoColumns
                        ? (constraints.maxWidth - 12) / 2
                        : constraints.maxWidth,
                    child: _buildInfoCard(
                      Icons.wb_sunny_rounded,
                      'Best time',
                      bestTime,
                    ),
                  ),
                ],
              );
            },
          ),
          const SizedBox(height: 24),
          _buildFunFact(funFact),
          NearbyPlaces(data: data),
        ],
      ),
    );
  }

  Widget _buildDescription(String description) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'ABOUT THIS PLACE',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: Color(0xFF6FA0FF),
              letterSpacing: 1.1,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            description,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.75),
              height: 1.55,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard(
    IconData icon,
    String title,
    String value,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: Colors.white.withValues(alpha: 0.07),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: const Color(0xFF00D9FF).withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              icon,
              color: const Color(0xFF00D9FF),
              size: 19,
            ),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.45),
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFunFact(String fact) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(19),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF00D9FF).withValues(alpha: 0.08),
            const Color(0xFF315BEA).withValues(alpha: 0.08),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: const Color(0xFF00D9FF).withValues(alpha: 0.15),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(13),
            ),
            child: const Center(
              child: Text(
                '💡',
                style: TextStyle(fontSize: 20),
              ),
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'DID YOU KNOW?',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF6FE0FF),
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  fact,
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.45,
                    fontWeight: FontWeight.w500,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // TEXT / MENU RESULT
  // ---------------------------------------------------------------------------

  Widget _buildText(Map<String, dynamic> data) {
    // Support all text field names currently used by the backend/frontend.
    final original = _firstNonEmpty([
      data['original_text'],
      data['source_text'],
      data['CONTENT'],
      data['content'],
      data['text'],
    ]);

    final translation = _firstNonEmpty([
      data['translated_text'],
      data['translation'],
      data['translated'],
    ]);

    final detectedLanguage = _firstNonEmpty([
      data['detected_language'],
      data['language'],
    ], fallback: 'Unknown');

    return Container(
      margin: const EdgeInsets.only(top: 28),
      padding: const EdgeInsets.all(24),
      decoration: _cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildResultHeader(
            title: 'Translation',
            subtitle: 'Detected language: $detectedLanguage',
          ),

          const SizedBox(height: 25),

          const Text(
            'ORIGINAL',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: Color(0xFF6FA0FF),
              letterSpacing: 1.2,
            ),
          ),

          const SizedBox(height: 9),

          _buildScrollableTextBox(
            text: original,
            emptyText: 'No text detected.',
            maxHeight: 320,
          ),

          const SizedBox(height: 20),

          const Text(
            'TRANSLATION',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: Color(0xFF00D9FF),
              letterSpacing: 1.2,
            ),
          ),

          const SizedBox(height: 9),

          _buildScrollableTranslationBox(
            text: translation,
            maxHeight: 360,
          ),
        ],
      ),
    );
  }

  Widget _buildScrollableTextBox({
    required String text,
    required String emptyText,
    required double maxHeight,
  }) {
    return Container(
      width: double.infinity,
      constraints: BoxConstraints(
        maxHeight: maxHeight,
      ),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(18),
      ),
      child: SingleChildScrollView(
        child: Text(
          text.isEmpty ? emptyText : text,
          style: const TextStyle(
            fontSize: 16,
            height: 1.5,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  Widget _buildScrollableTranslationBox({
    required String text,
    required double maxHeight,
  }) {
    return Container(
      width: double.infinity,
      constraints: BoxConstraints(
        maxHeight: maxHeight,
      ),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF00D9FF).withValues(alpha: 0.08),
            const Color(0xFF315BEA).withValues(alpha: 0.08),
          ],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFF00D9FF).withValues(alpha: 0.15),
        ),
      ),
      child: SingleChildScrollView(
        child: Text(
          text.isEmpty ? 'Translation unavailable.' : text,
          style: const TextStyle(
            fontSize: 18,
            height: 1.5,
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  String _firstNonEmpty(
    List<dynamic> values, {
    String fallback = '',
  }) {
    for (final value in values) {
      if (value == null) continue;

      final text = value.toString().trim();

      if (text.isNotEmpty && text != 'null') {
        return text;
      }
    }

    return fallback;
  }

  Widget _buildSelectionRequired(BuildContext context) {
    final candidates = (result!['candidates'] as List?) ?? [];

    return Container(
      margin: const EdgeInsets.only(top: 28),
      padding: const EdgeInsets.all(24),
      decoration: _cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF00D9FF),
                  Color(0xFF315BEA),
                ],
              ),
              borderRadius: BorderRadius.circular(15),
            ),
            child: const Icon(
              Icons.help_outline,
              color: Colors.white,
              size: 23,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Not confident enough to identify this',
            style: TextStyle(
              fontSize: 19,
              fontWeight: FontWeight.w800,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Did you mean?',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.5),
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 18),
          for (final c in candidates)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: OutlinedButton(
                onPressed: () => onCandidateSelected?.call(
                  c['label_class']?.toString() ?? '',
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    vertical: 14,
                    horizontal: 16,
                  ),
                  side: BorderSide(
                    color: Colors.white.withValues(alpha: 0.1),
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  alignment: Alignment.centerLeft,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        (c['label_class']?.toString() ?? '')
                            .replaceAll('_', ' '),
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    Text(
                      '${((c['confidence_score'] ?? 0) * 100).round()}%',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.5),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildUnknown() {
    return Container(
      margin: const EdgeInsets.only(top: 28),
      padding: const EdgeInsets.all(28),
      decoration: _cardDecoration,
      child: Column(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: const Color(0xFFE8941A).withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(
              Icons.search_off_rounded,
              color: Color(0xFFE8941A),
              size: 30,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            "We couldn't identify this",
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Try another photo, or search manually.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.5),
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
