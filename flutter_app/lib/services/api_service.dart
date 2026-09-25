import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://10.10.6.208:8000';
  static const String identifyUrl = '$baseUrl/identify';
  static const String translateUrl = '$baseUrl/translate';

  static Future<Map<String, dynamic>> selectCandidate({
    required String labelClass,
    required String language,
    double? latitude,
    double? longitude,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/identify/select'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'label_class': labelClass,
        'language': language,
        if (latitude != null) 'latitude': latitude,
        if (longitude != null) 'longitude': longitude,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Selection error: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> identifyImage({
    required List<int> imageBytes,
    required String filename,
    required String language,
    double? latitude,
    double? longitude,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse(identifyUrl),
    );

    request.fields['language'] = language;

    if (latitude != null && longitude != null) {
      request.fields['latitude'] = latitude.toString();
      request.fields['longitude'] = longitude.toString();
    }

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        imageBytes,
        filename: filename,
      ),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Backend error: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> translateText({
    required String text,
    required String language,
  }) async {
    final response = await http.post(
      Uri.parse(translateUrl),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'text': text,
        'language': language,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Translation error: ${response.statusCode}');
    }
  }

  // ── Image translation — debug-instrumented per Task 11 ──
  static Future<Map<String, dynamic>> translateImage({
    required List<int> imageBytes,
    required String filename,
    required String targetLanguage,
  }) async {
    final url = '$baseUrl/translate-image';
    debugPrint('[TRANSLATE DEBUG] request URL: $url');
    debugPrint('[TRANSLATE DEBUG] image bytes: ${imageBytes.length}');
    debugPrint('[TRANSLATE DEBUG] target language: $targetLanguage');

    final request = http.MultipartRequest('POST', Uri.parse(url));

    request.fields['target_language'] = targetLanguage;
    request.files.add(
      http.MultipartFile.fromBytes('file', imageBytes, filename: filename),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    debugPrint('[TRANSLATE DEBUG] response status: ${response.statusCode}');
    debugPrint('[TRANSLATE DEBUG] raw response: ${response.body}');

    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      debugPrint('[TRANSLATE DEBUG] parsed success: ${decoded['success']}');
      debugPrint('[TRANSLATE DEBUG] parsed source_text length: '
          '${(decoded['source_text']?.toString() ?? '').length}');
      debugPrint('[TRANSLATE DEBUG] parsed translated_text length: '
          '${(decoded['translated_text']?.toString() ?? '').length}');
      return decoded;
    } else {
      throw Exception('Translation error: ${response.statusCode} — ${response.body}');
    }
  }
}
