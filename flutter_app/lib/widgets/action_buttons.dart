import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class ActionButtons extends StatelessWidget {
  final bool isAnalyzing;
  final Future<void> Function(ImageSource) onPickImage;

  const ActionButtons({super.key, required this.isAnalyzing, required this.onPickImage});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _buildButton(Icons.camera_alt_outlined, 'Camera', () => onPickImage(ImageSource.camera))),
        const SizedBox(width: 12),
        Expanded(child: _buildButton(Icons.photo_library_outlined, 'Gallery', () => onPickImage(ImageSource.gallery))),
      ],
    );
  }

  Widget _buildButton(IconData icon, String label, VoidCallback onTap) {
    return OutlinedButton.icon(
      onPressed: isAnalyzing ? null : onTap,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: Colors.white,
        backgroundColor: Colors.white.withValues(alpha: 0.04),
        padding: const EdgeInsets.symmetric(vertical: 16),
        side: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
      ),
    );
  }
}