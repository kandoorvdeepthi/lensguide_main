import 'package:flutter/material.dart';
import 'screen/home_screen.dart';

class LensGuideApp extends StatelessWidget {
  const LensGuideApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'LensGuide',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF0A0E17),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00D9FF),
          brightness: Brightness.dark,
          primary: const Color(0xFF00D9FF),
          secondary: const Color(0xFF315BEA),
          surface: const Color(0xFF12172A),
        ),
        fontFamily: 'Arial',
      ),
      home: const HomeScreen(),
    );
  }
}
