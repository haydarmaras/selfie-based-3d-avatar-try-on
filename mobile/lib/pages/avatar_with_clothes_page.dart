import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

class AvatarWithClothesPage extends StatelessWidget {
  final String avatarWithClothesUrl;

  const AvatarWithClothesPage({
    super.key,
    required this.avatarWithClothesUrl,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Kıyafetli Avatar")),
      body: Container(
        color: Colors.black,
        child: ModelViewer(
          src: avatarWithClothesUrl,
          autoRotate: true,
          cameraControls: true,
          backgroundColor: Colors.black,
        ),
      ),
    );
  }
}
