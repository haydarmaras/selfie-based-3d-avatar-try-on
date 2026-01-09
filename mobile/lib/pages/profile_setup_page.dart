import 'dart:typed_data';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/foundation.dart' show Uint8List;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

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

  Uint8List? selfieFront; // ön selfie
  Uint8List? selfieSide; // yan selfie

  bool saving = false;

  final picker = ImagePicker();

  Future<void> pickFront() async {
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;
    selfieFront = await file.readAsBytes();
    setState(() {});
  }

  Future<void> pickSide() async {
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;
    selfieSide = await file.readAsBytes();
    setState(() {});
  }

  Future<void> save() async {
    if (!_formKey.currentState!.validate()) return;

    if (selfieFront == null || selfieSide == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Lütfen ÖNDEN ve YANDAN iki selfie yükleyiniz!"),
        ),
      );
      return;
    }

    setState(() => saving = true);

    try {
      final uid = widget.userId;

      // ---------- Firebase Storage ----------
      final storage = FirebaseStorage.instanceFor(
        bucket: "bitirmeprojesi-9b244.firebasestorage.app",
      );

      final refFront = storage.ref().child("selfies/${uid}_front.jpg");
      final refSide = storage.ref().child("selfies/${uid}_side.jpg");

      await refFront.putData(
        selfieFront!,
        SettableMetadata(contentType: "image/jpeg"),
      );
      await refSide.putData(
        selfieSide!,
        SettableMetadata(contentType: "image/jpeg"),
      );

      final urlFront = await refFront.getDownloadURL();
      final urlSide = await refSide.getDownloadURL();

      // ---------- Firestore ----------
      await FirebaseFirestore.instance.collection("users").doc(uid).set({
        "ad_soyad": name.text,
        "boy": double.tryParse(height.text) ?? 0,
        "kilo": double.tryParse(weight.text) ?? 0,
        "omuz_genisligi": double.tryParse(shoulder.text) ?? 0,
        "bel_cevresi": double.tryParse(waist.text) ?? 0,
        "kalca_cevresi": double.tryParse(hip.text) ?? 0,
        "bacak_uzunlugu": double.tryParse(leg.text) ?? 0,
        "cinsiyet": gender,
        "selfie_front_url": urlFront,
        "selfie_side_url": urlSide,
        "avatar_url": "",
      }, SetOptions(merge: true));

      // ---------- Backend’e multipart POST ----------
      final request = http.MultipartRequest(
        "POST",
        Uri.parse(backendUrl),
      );

      request.fields.addAll({
        "user_id": uid,
        "boy": height.text,
        "kilo": weight.text,
        "cinsiyet": gender,
        "omuz_genisligi": shoulder.text,
        "bel_cevresi": waist.text,
        "kalca_cevresi": hip.text,
        "bacak_uzunlugu": leg.text,
      });

      request.files.add(
        http.MultipartFile.fromBytes(
          "selfie_front",
          selfieFront!,
          filename: "${uid}_front.jpg",
        ),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          "selfie_side",
          selfieSide!,
          filename: "${uid}_side.jpg",
        ),
      );

      final response = await request.send();
      debugPrint("Backend Response Code: ${response.statusCode}");

      if (!mounted) return;

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Profil kaydedildi ve avatar oluşturuldu!"),
          ),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Backend hata kodu: ${response.statusCode}"),
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Hata: $e")),
      );
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pad = const EdgeInsets.all(16);

    return Scaffold(
      appBar: AppBar(title: const Text("Profilini Oluştur")),
      body: SingleChildScrollView(
        padding: pad,
        child: Column(
          children: [
            Card(
              child: Padding(
                padding: pad,
                child: Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      TextFormField(
                        controller: name,
                        decoration: const InputDecoration(
                          labelText: "Ad Soyad",
                          border: OutlineInputBorder(),
                        ),
                        validator: (v) =>
                            v == null || v.isEmpty ? "Ad Soyad girin" : null,
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: gender,
                        decoration: const InputDecoration(
                          labelText: "Cinsiyet",
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(
                            value: "Erkek",
                            child: Text("Erkek"),
                          ),
                          DropdownMenuItem(
                            value: "Kadın",
                            child: Text("Kadın"),
                          ),
                        ],
                        onChanged: (v) {
                          if (v != null) {
                            setState(() => gender = v);
                          }
                        },
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: height,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Boy (cm)",
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              controller: weight,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Kilo (kg)",
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: shoulder,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Omuz (cm)",
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              controller: waist,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Bel (cm)",
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: hip,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Kalça (cm)",
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              controller: leg,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Bacak Uzunluğu (cm)",
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),

            const Text(
              "⚠️ Avatar için iki fotoğraf gereklidir:\n"
              "1️⃣ Önden selfie (düz bakış)\n"
              "2️⃣ Soldan açı — yüz & saç net görünmeli",
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),

            // ÖN SELFİE
            GestureDetector(
              onTap: pickFront,
              child: Container(
                width: 160,
                height: 160,
                decoration: BoxDecoration(
                  border: Border.all(),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: selfieFront == null
                    ? const Center(child: Text("ÖN SELFİE"))
                    : ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.memory(selfieFront!, fit: BoxFit.cover),
                      ),
              ),
            ),
            const SizedBox(height: 20),

            // YAN SELFİE
            GestureDetector(
              onTap: pickSide,
              child: Container(
                width: 160,
                height: 160,
                decoration: BoxDecoration(
                  border: Border.all(),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: selfieSide == null
                    ? const Center(child: Text("YAN SELFİE"))
                    : ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.memory(selfieSide!, fit: BoxFit.cover),
                      ),
              ),
            ),

            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: saving ? null : save,
              icon: const Icon(Icons.save),
              label: Text(
                saving ? "Oluşturuluyor..." : "Kaydet ve Avatar Oluştur",
              ),
            ),
          ],
        ),
      ),
    );
  }
}
