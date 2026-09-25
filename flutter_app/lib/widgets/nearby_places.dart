import 'package:flutter/material.dart';

class NearbyPlaces extends StatelessWidget {
  final Map<String, dynamic> data;

  const NearbyPlaces({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final nearby = data['nearby'];
    if (nearby == null || nearby is! Map) return const SizedBox.shrink();

    final attractions = nearby['attractions'];
    if (attractions is! List || attractions.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 28),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('EXPLORE NEARBY', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Color(0xFF6FA0FF), letterSpacing: 1.2)),
            Text('${attractions.length} places', style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12)),
          ],
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 154,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: attractions.length,
            separatorBuilder: (_, __) => const SizedBox(width: 12),
            itemBuilder: (context, index) {
              final item = attractions[index];
              if (item is! Map) return const SizedBox.shrink();

              final name = item['name']?.toString() ?? 'Nearby place';
              final distance = item['distance']?.toString() ?? '';
              final minutes = item['minutes']?.toString();
              final popularityScore = item['popularity_score']?.toString();

              return Container(
                width: 190,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF12172A),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(colors: [Color(0xFF00D9FF), Color(0xFF315BEA)]),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.place_outlined, color: Colors.white, size: 19),
                    ),
                    const Spacer(),
                    Text(name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: Colors.white)),
                    const SizedBox(height: 5),
                    Row(
                      children: [
                        if (distance.isNotEmpty) Text(distance, style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12)),
                        if (distance.isNotEmpty && minutes != null)
                          const Padding(padding: EdgeInsets.symmetric(horizontal: 6), child: Text('•', style: TextStyle(color: Colors.white38))),
                        if (minutes != null) Text('$minutes min', style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12)),
                        if (popularityScore != null) ...[
                          const Padding(padding: EdgeInsets.symmetric(horizontal: 6), child: Text('•', style: TextStyle(color: Colors.white38))),
                          const Icon(Icons.trending_up_rounded, color: Color(0xFF00D9FF), size: 13),
                          const SizedBox(width: 2),
                          Text(popularityScore, style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12)),
                        ],
                      ],
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}