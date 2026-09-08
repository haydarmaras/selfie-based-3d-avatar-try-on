import 'dart:convert';
import 'dart:typed_data';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

const String backendUrl = "http://10.0.2.2:8000/avatar_olustur";

class ProfileSetupPage extends StatefulWidget {
  final String userId;
  const ProfileSetupPage({super.key, required this.userId});

  @override
  State<ProfileSetupPage> createState() => _ProfileSetupPageState();
}

class _ProfileSetupPageState extends State<ProfileSetupPage> {
  final _formKey = GlobalKey<FormState>();
  final name = TextEditingController();
  final height = TextEditingController(text: "180");
  final weight = TextEditingController(text: "75");
  final shoulder = TextEditingController(text: "45");
  final waist = TextEditingController(text: "80");
  final hip = TextEditingController(text: "95");
  final leg = TextEditingController(text: "95");

  String gender = "Erkek";
  Uint8List? selfieFront;
  Uint8List? selfieSide;
  bool saving = false;
  final picker = ImagePicker();

  Future<void> pickFront() async {
    final file = await picker.pickImage(source: ImageSource.gallery, imageQuality: 90);
    if (file == null) return;
    setState(() async => selfieFront = await file.readAsBytes());
  }

  Future<void> pickSide() async {
    final file = await picker.pickImage(source: ImageSource.gallery, imageQuality: 90);
    if (file == null) return;
    final bytes = await file.readAsBytes();
    if (mounted) setState(() => selfieSide = bytes);
  }

  String? numberValidator(String? value, String label, double min, double max) {
    final n = double.tryParse(value?.replaceAll(',', '.') ?? '');
    if (n == null) return "$label sayısal olmalı";
    if (n < min || n > max) return "$label $min-$max arasında olmalı";
    return null;
  }

  Future<void> save() async {
    if (!_formKey.currentState!.validate()) return;
    if (selfieFront == null || selfieSide == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Ön ve yan selfie yükleyin.")),
      );
      return;
    }

    setState(() => saving = true);
    try {
      final uid = widget.userId;
      final storage = FirebaseStorage.instanceFor(
        bucket: "bitirmeprojesi-9b244.firebasestorage.app",
      );
      final frontRef = storage.ref().child("selfies/${uid}_front.jpg");
      final sideRef = storage.ref().child("selfies/${uid}_side.jpg");
      await frontRef.putData(selfieFront!, SettableMetadata(contentType: "image/jpeg"));
      await sideRef.putData(selfieSide!, SettableMetadata(contentType: "image/jpeg"));

      final frontUrl = await frontRef.getDownloadURL();
      final sideUrl = await sideRef.getDownloadURL();
      final h = height.text.replaceAll(',', '.');
      final w = weight.text.replaceAll(',', '.');
      final s = shoulder.text.replaceAll(',', '.');
      final wa = waist.text.replaceAll(',', '.');
      final hi = hip.text.replaceAll(',', '.');
      final l = leg.text.replaceAll(',', '.');

      await FirebaseFirestore.instance.collection("users").doc(uid).set({
        "ad_soyad": name.text.trim(),
        "boy": double.parse(h),
        "kilo": double.parse(w),
        "omuz_genisligi": double.parse(s),
        "bel_cevresi": double.parse(wa),
        "kalca_cevresi": double.parse(hi),
        "bacak_uzunlugu": double.parse(l),
        "cinsiyet": gender,
        "selfie_front_url": frontUrl,
        "selfie_side_url": sideUrl,
        "avatar_status": "queued",
      }, SetOptions(merge: true));

      final request = http.MultipartRequest("POST", Uri.parse(backendUrl));
      request.fields.addAll({
        "user_id": uid,
        "boy": h,
        "kilo": w,
        "cinsiyet": gender,
        "omuz_genisligi": s,
        "bel_cevresi": wa,
        "kalca_cevresi": hi,
        "bacak_uzunlugu": l,
      });
      request.files.add(http.MultipartFile.fromBytes("selfie_front", selfieFront!, filename: "${uid}_front.jpg"));
      request.files.add(http.MultipartFile.fromBytes("selfie_side", selfieSide!, filename: "${uid}_side.jpg"));

      final response = await request.send().timeout(const Duration(minutes: 5));
      final body = await response.stream.bytesToString();
      Map<String, dynamic>? json;
      try { json = jsonDecode(body) as Map<String, dynamic>; } catch (_) {}

      if (!mounted) return;
      if (response.statusCode == 200 && json?["status"] == "ok") {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Profil kaydedildi, avatar oluşturuldu.")),
        );
        Navigator.pop(context);
      } else {
        final message = json?["message"]?.toString() ?? "Backend hata kodu: ${response.statusCode}";
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Hata: $e")));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Widget field(TextEditingController c, String label, String? Function(String?)? validator) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: TextFormField(
      controller: c,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      validator: validator,
    ),
  );

  @override
  void dispose() {
    for (final c in [name, height, weight, shoulder, waist, hip, leg]) c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Profilini Oluştur")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(children: [
            TextFormField(
              controller: name,
              decoration: const InputDecoration(labelText: "Ad Soyad", border: OutlineInputBorder()),
              validator: (v) => v == null || v.trim().length < 2 ? "Ad Soyad girin" : null,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: gender,
              decoration: const InputDecoration(labelText: "Cinsiyet", border: OutlineInputBorder()),
              items: const [
                DropdownMenuItem(value: "Erkek", child: Text("Erkek")),
                DropdownMenuItem(value: "Kadın", child: Text("Kadın")),
              ],
              onChanged: (v) => setState(() => gender = v ?? gender),
            ),
            const SizedBox(height: 12),
            field(height, "Boy (cm)", (v) => numberValidator(v, "Boy", 100, 250)),
            field(weight, "Kilo (kg)", (v) => numberValidator(v, "Kilo", 25, 300)),
            field(shoulder, "Omuz (cm)", (v) => numberValidator(v, "Omuz", 20, 100)),
            field(waist, "Bel (cm)", (v) => numberValidator(v, "Bel", 40, 180)),
            field(hip, "Kalça (cm)", (v) => numberValidator(v, "Kalça", 40, 200)),
            field(leg, "Bacak Uzunluğu (cm)", (v) => numberValidator(v, "Bacak", 40, 160)),
            const SizedBox(height: 8),
            const Text("İki fotoğraf: önden düz bakış + soldan/yan açı. Yüz ve saç net görünmeli.", textAlign: TextAlign.center),
            const SizedBox(height: 16),
            Row(children: [
              Expanded(child: _photoBox("ÖN SELFİE", selfieFront, pickFront)),
              const SizedBox(width: 12),
              Expanded(child: _photoBox("YAN SELFİE", selfieSide, pickSide)),
            ]),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: saving ? null : save,
                icon: saving ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.auto_awesome),
                label: Text(saving ? "Avatar oluşturuluyor..." : "Kaydet ve Avatar Oluştur"),
              ),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _photoBox(String title, Uint8List? bytes, VoidCallback onTap) => GestureDetector(
    onTap: onTap,
    child: AspectRatio(
      aspectRatio: 1,
      child: Container(
        decoration: BoxDecoration(border: Border.all(), borderRadius: BorderRadius.circular(12)),
        child: bytes == null
            ? Center(child: Text(title))
            : ClipRRect(borderRadius: BorderRadius.circular(11), child: Image.memory(bytes, fit: BoxFit.cover)),
      ),
    ),
  );
}
