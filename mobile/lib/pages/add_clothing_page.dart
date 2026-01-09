import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

class AddClothingPage extends StatefulWidget {
  final String userId;
  const AddClothingPage({super.key, required this.userId});

  @override
  State<AddClothingPage> createState() => _AddClothingPageState();
}

class _AddClothingPageState extends State<AddClothingPage> {
  static const String backendUrl = "http://10.0.2.2:8000/kiyafet_ekle";

  final picker = ImagePicker();
  final List<Uint8List> clothes = [];
  int? selectedIndex;
  bool loading = false;

  Future<void> addPhoto() async {
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;
    final bytes = await file.readAsBytes();
    setState(() {
      clothes.add(bytes);
      selectedIndex ??= 0;
    });
  }

  Future<void> applyClothing() async {
    if (selectedIndex == null || clothes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text("Önce kıyafet fotoğrafı ekleyip seçmelisin.")),
      );
      return;
    }

    setState(() => loading = true);

    try {
      final req = http.MultipartRequest("POST", Uri.parse(backendUrl));
      req.fields["user_id"] = widget.userId;

      req.files.add(
        http.MultipartFile.fromBytes(
          "clothing_image",
          clothes[selectedIndex!],
          filename: "clothing.jpg",
        ),
      );

      final res = await req.send();

      if (!mounted) return;

      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text("✅ Kıyafet giydirildi. Avatar güncellendi.")),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Backend hata: ${res.statusCode}")),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Hata: $e")),
      );
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Kıyafet Ekle")),
      body: Column(
        children: [
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              FilledButton.icon(
                onPressed: loading ? null : addPhoto,
                icon: const Icon(Icons.add_photo_alternate),
                label: const Text("Foto Ekle"),
              ),
              const SizedBox(width: 12),
              FilledButton.icon(
                onPressed: loading ? null : applyClothing,
                icon: const Icon(Icons.checkroom),
                label: Text(loading ? "Giydiriliyor..." : "Seçileni Giydir"),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: clothes.isEmpty
                ? const Center(child: Text("Henüz kıyafet eklenmedi."))
                : GridView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: clothes.length,
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                    ),
                    itemBuilder: (_, i) {
                      final selected = selectedIndex == i;
                      return GestureDetector(
                        onTap: () => setState(() => selectedIndex = i),
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
                            child: Image.memory(clothes[i], fit: BoxFit.cover),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
