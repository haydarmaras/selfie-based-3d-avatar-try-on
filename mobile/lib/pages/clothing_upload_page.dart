import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';

const String clothingApiUrl = "http://10.0.2.2:8000/kiyafet_ekle";

class ClothingUploadPage extends StatefulWidget {
  const ClothingUploadPage({super.key});

  @override
  State<ClothingUploadPage> createState() => _ClothingUploadPageState();
}

class _ClothingUploadPageState extends State<ClothingUploadPage> {
  final ImagePicker _picker = ImagePicker();

  final List<Uint8List> clothingImages = [];
  int? selectedIndex;
  bool uploading = false;

  Future<void> pickClothingImage() async {
    final file = await _picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;

    final bytes = await file.readAsBytes();
    setState(() {
      clothingImages.add(bytes);
    });
  }

  Future<void> uploadSelectedClothing() async {
    if (selectedIndex == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Lütfen bir kıyafet seçin")),
      );
      return;
    }

    setState(() => uploading = true);

    try {
      final uid = FirebaseAuth.instance.currentUser!.uid;

      final request = http.MultipartRequest(
        "POST",
        Uri.parse(clothingApiUrl),
      );

      request.fields["user_id"] = uid;

      request.files.add(
        http.MultipartFile.fromBytes(
          "clothing_image",
          clothingImages[selectedIndex!],
          filename: "clothing.jpg",
        ),
      );

      final response = await request.send();

      if (!mounted) return;

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Kıyafet avatar’a giydirildi ✅")),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Hata: ${response.statusCode}")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Hata: $e")),
      );
    } finally {
      if (mounted) setState(() => uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Kıyafet Ekle"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            FilledButton.icon(
              onPressed: pickClothingImage,
              icon: const Icon(Icons.add),
              label: const Text("Yeni Kıyafet Fotoğrafı Ekle"),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: clothingImages.isEmpty
                  ? const Center(
                      child: Text(
                        "Henüz kıyafet eklenmedi",
                        style: TextStyle(fontSize: 16),
                      ),
                    )
                  : GridView.builder(
                      itemCount: clothingImages.length,
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                      ),
                      itemBuilder: (context, index) {
                        final selected = selectedIndex == index;
                        return GestureDetector(
                          onTap: () {
                            setState(() => selectedIndex = index);
                          },
                          child: Container(
                            decoration: BoxDecoration(
                              border: Border.all(
                                color: selected ? Colors.green : Colors.grey,
                                width: selected ? 3 : 1,
                              ),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(10),
                              child: Image.memory(
                                clothingImages[index],
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: uploading ? null : uploadSelectedClothing,
              icon: const Icon(Icons.check),
              label: Text(
                uploading
                    ? "Giydiriliyor..."
                    : "Seçili Kıyafeti Avatar’a Giydir",
              ),
            ),
          ],
        ),
      ),
    );
  }
}
