import 'package:flutter/material.dart';

class LanguageSheet extends StatelessWidget {
  final String selectedLanguage;
  final void Function(String) onLanguageSelected;

  const LanguageSheet({super.key, required this.selectedLanguage, required this.onLanguageSelected});

  static void show({
    required BuildContext context,
    required String selectedLanguage,
    required void Function(String) onLanguageSelected,
  }) {
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      backgroundColor: const Color(0xFF12172A),
      builder: (context) => LanguageSheet(selectedLanguage: selectedLanguage, onLanguageSelected: onLanguageSelected),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 25),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('Choose language', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: Colors.white)),
            ),
            const SizedBox(height: 6),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'LensGuide will return results in your language.',
                style: TextStyle(color: Colors.white.withValues(alpha: 0.5)),
              ),
            ),
            const SizedBox(height: 15),
            for (final language in ['English', 'Hindi', 'Tamil'])
              ListTile(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                leading: CircleAvatar(
                  backgroundColor: const Color(0xFF00D9FF).withValues(alpha: 0.15),
                  child: Text(
                    language == 'English' ? 'EN' : language == 'Hindi' ? 'हि' : 'த',
                    style: const TextStyle(color: Color(0xFF00D9FF), fontWeight: FontWeight.bold),
                  ),
                ),
                title: Text(language, style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.white)),
                trailing: selectedLanguage == language
                    ? const Icon(Icons.check_circle, color: Color(0xFF00D9FF))
                    : null,
                onTap: () {
                  onLanguageSelected(language);
                  Navigator.pop(context);
                },
              ),
          ],
        ),
      ),
    );
  }
}