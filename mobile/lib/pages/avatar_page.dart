import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

class AvatarPage extends StatelessWidget {
  const AvatarPage({super.key});

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;

    if (user == null) {
      return const Scaffold(
        body: Center(child: Text("Giriş yapılmadı")),
      );
    }

    final userDoc =
        FirebaseFirestore.instance.collection("users").doc(user.uid);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Avatar Önizleme"),
      ),
      body: StreamBuilder<DocumentSnapshot>(
        stream: userDoc.snapshots(),
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (!snap.hasData || !snap.data!.exists) {
            return const Center(child: Text("Kullanıcı verisi yok."));
          }

          final data = snap.data!.data() as Map<String, dynamic>? ?? {};
          final avatarUrl = data["avatar_url"] ?? "";

          if (avatarUrl.isEmpty) {
            return const Center(
              child: Text(
                "Avatar henüz oluşturulmadı.\n"
                "Profil sayfasından selfie yükleyip kaydedin.",
                textAlign: TextAlign.center,
              ),
            );
          }

          return Container(
            color: Colors.black,
            child: Center(
              child: ModelViewer(
                src: avatarUrl, // ▶ Firebase Storage veya URL'den 3D model
                alt: "3D Avatar",
                autoRotate: true,
                cameraControls: true,
                ar: false,
                autoPlay: true,
                disableZoom: false,
                disablePan: false,
                backgroundColor: Colors.transparent,
              ),
            ),
          );
        },
      ),
    );
  }
}
