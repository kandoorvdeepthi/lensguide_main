import 'dart:io' show File;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class ImageSection extends StatelessWidget {
  final XFile? selectedImage;

  const ImageSection({super.key, required this.selectedImage});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 330,
      decoration: BoxDecoration(
        color: const Color(0xFF12172A),
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.3), blurRadius: 25, offset: const Offset(0, 10)),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: selectedImage == null
          ? _buildEmptyState()
          : Stack(
              fit: StackFit.expand,
              children: [
                _buildPreviewImage(),
                Positioned(
                  top: 16,
                  left: 16,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.6),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(color: const Color(0xFF00D9FF).withValues(alpha: 0.3)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.image_outlined, color: Color(0xFF00D9FF), size: 15),
                        SizedBox(width: 6),
                        Text('Ready to explore', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildPreviewImage() {
    if (kIsWeb) {
      return Image.network(selectedImage!.path, fit: BoxFit.cover);
    }
    return Image.file(File(selectedImage!.path), fit: BoxFit.cover);
  }

  Widget _buildEmptyState() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: [Color(0xFF00D9FF), Color(0xFF315BEA)]),
            borderRadius: BorderRadius.circular(22),
            boxShadow: [BoxShadow(color: const Color(0xFF00D9FF).withValues(alpha: 0.3), blurRadius: 20)],
          ),
          child: const Icon(Icons.center_focus_strong, size: 34, color: Colors.white),
        ),
        const SizedBox(height: 18),
        const Text(
          'Capture something interesting',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Colors.white),
        ),
        const SizedBox(height: 7),
        Text(
          'Landmark • Sign • Menu • Monument',
          style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 13),
        ),
      ],
    );
  }
}