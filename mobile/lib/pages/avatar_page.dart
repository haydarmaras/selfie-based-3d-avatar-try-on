import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

class AvatarPage extends StatelessWidget {
  const AvatarPage({super.key});

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return const Scaffold(body: Center(child: Text("Giriş yapılmadı")));

    final ref = FirebaseFirestore.instance.collection("users").doc(user.uid);
    return Scaffold(
      appBar: AppBar(title: const Text("Avatar Önizleme")),
      body: StreamBuilder<DocumentSnapshot<Map<String, dynamic>>>(
        stream: ref.snapshots(),
        builder: (context, snap) {
          if (snap.hasError) return Center(child: Text("Firebase hatası: ${snap.error}"));
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          if (!snap.data!.exists) return const Center(child: Text("Kullanıcı verisi yok."));

          final data = snap.data!.data() ?? {};
          final status = data["avatar_status"]?.toString() ?? "";
          final error = data["avatar_error"]?.toString() ?? "";
          final url = data["avatar_url"]?.toString() ?? "";

          if (status == "generating" || status == "queued") {
            return const Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
              CircularProgressIndicator(), SizedBox(height: 16), Text("Avatar oluşturuluyor..."),
            ]));
          }
          if (status == "error") {
            return Center(child: Padding(padding: const EdgeInsets.all(24), child: Text("Avatar oluşturulamadı.\n$error", textAlign: TextAlign.center)));
          }
          if (url.isEmpty) {
            return const Center(child: Text("Avatar henüz oluşturulmadı.\nProfil sayfasından fotoğraf yükleyin.", textAlign: TextAlign.center));
          }

          return Container(
            color: Colors.black,
            child: ModelViewer(
              src: url,
              alt: "3D Avatar",
              autoRotate: true,
              cameraControls: true,
              ar: false,
              autoPlay: true,
              disableZoom: false,
              disablePan: false,
              backgroundColor: Colors.transparent,
            ),
          );
        },
      ),
    );
  }
}
