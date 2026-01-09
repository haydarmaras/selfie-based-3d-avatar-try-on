import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

class AvatarPreviewPage extends StatelessWidget {
  final String avatarUrl;

  const AvatarPreviewPage({
    super.key,
    required this.avatarUrl,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Avatar Önizleme"),
        centerTitle: true,
      ),
      body: Container(
        color: Colors.black,
        child: ModelViewer(
          src: avatarUrl, // 🔥 Firebase GLB URL
          alt: "Kullanıcı Avatarı",
          ar: false,
          autoRotate: true,
          cameraControls: true,
          backgroundColor: Colors.black,
          disableZoom: false,
          exposure: 1.0,
          shadowIntensity: 1.0,
        ),
      ),
    );
  }
}
