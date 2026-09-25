import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class TranslateSheet extends StatefulWidget {
  final List<int> imageBytes;
  final String filename;

  const TranslateSheet({
    super.key,
    required this.imageBytes,
    required this.filename,
  });

  static void show(BuildContext context, {
    required List<int> imageBytes,
    required String filename,
  }) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => TranslateSheet(imageBytes: imageBytes, filename: filename),
    );
  }

  @override
  State<TranslateSheet> createState() => _TranslateSheetState();
}

class _TranslateSheetState extends State<TranslateSheet> {
  String _selectedLanguage = 'English';
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  Future<void> _translate() async {
    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      final data = await ApiService.translateImage(
        imageBytes: widget.imageBytes,
        filename: widget.filename,
        targetLanguage: _selectedLanguage,
      );

      debugPrint('[TRANSLATE DEBUG] received map keys: ${data.keys}');

      if (!mounted) return;
      setState(() => _result = data);
    } catch (e) {
      debugPrint('[TRANSLATE DEBUG] error: $e');
      if (!mounted) return;
      setState(() => _error = 'Could not reach the translation service.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: Container(
          margin: const EdgeInsets.all(14),
          padding: const EdgeInsets.all(22),
          constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.8),
          decoration: BoxDecoration(
            color: const Color(0xFF0D1128).withValues(alpha: 0.96),
            borderRadius: BorderRadius.circular(26),
            border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.2)),
            boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.4), blurRadius: 24)],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.translate_rounded, color: Color(0xFF00D9FF), size: 22),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text('Translate Sign / Menu',
                        style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: const Icon(Icons.close, color: Colors.white70, size: 20),
                  ),
                ],
              ),
              const SizedBox(height: 18),

              Row(
                children: ['English', 'Hindi', 'Tamil'].map((lang) {
                  final selected = lang == _selectedLanguage;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => setState(() => _selectedLanguage = lang),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                        decoration: BoxDecoration(
                          color: selected ? const Color(0xFF00D9FF) : Colors.white.withValues(alpha: 0.06),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: selected ? const Color(0xFF00D9FF) : Colors.white.withValues(alpha: 0.14),
                          ),
                        ),
                        child: Text(
                          lang,
                          style: TextStyle(
                            color: selected ? const Color(0xFF04101A) : Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 18),

              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _loading ? null : _translate,
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF00D9FF),
                    foregroundColor: const Color(0xFF04101A),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  child: _loading
                      ? const SizedBox(
                          width: 18, height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF04101A)),
                        )
                      : const Text('Translate', style: TextStyle(fontWeight: FontWeight.w700)),
                ),
              ),

              if (_error != null) ...[
                const SizedBox(height: 16),
                Text(_error!, style: const TextStyle(color: Colors.redAccent, fontSize: 13)),
              ],

              if (_result != null) ...[
                const SizedBox(height: 18),
                if (_result!['success'] == true) ...[
                  _resultBlock('ORIGINAL TEXT', _result!['source_text']?.toString() ?? ''),
                  const SizedBox(height: 12),
                  _resultBlock('TRANSLATION (${_result!['target_language']})',
                      _result!['translated_text']?.toString() ?? '', highlight: true),
                ] else
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.orange.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: Colors.orange.withValues(alpha: 0.3)),
                    ),
                    child: Text(
                      _result!['message']?.toString() ?? 'No readable text found in the image.',
                      style: const TextStyle(color: Colors.orangeAccent, fontSize: 13),
                    ),
                  ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _resultBlock(String label, String text, {bool highlight = false}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: highlight ? const Color(0xFF00D9FF).withValues(alpha: 0.08) : Colors.white.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: highlight ? const Color(0xFF00D9FF).withValues(alpha: 0.25) : Colors.white.withValues(alpha: 0.1),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: highlight ? const Color(0xFF6FE0FF) : Colors.white54, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1)),
          const SizedBox(height: 6),
          Text(text.isEmpty ? '—' : text, style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4)),
        ],
      ),
    );
  }
}