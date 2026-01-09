import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import 'avatar_page.dart';
import 'profile_setup_page.dart';
import 'add_clothing_page.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      return const Scaffold(
        body: Center(child: Text('Giriş yapılmadı')),
      );
    }

    final userDoc =
        FirebaseFirestore.instance.collection('users').doc(user.uid);

    return StreamBuilder<DocumentSnapshot>(
      stream: userDoc.snapshots(),
      builder: (context, snap) {
        final data = snap.data?.data() as Map<String, dynamic>? ?? {};

        final hasProfile = data.containsKey('boy');
        final hasAvatar = (data['avatar_url'] ?? '').toString().isNotEmpty;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Ana Sayfa'),
            actions: [
              IconButton(
                icon: const Icon(Icons.logout),
                onPressed: () => AuthService().signOut(),
              ),
            ],
          ),
          body: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Hoş geldin, ${data['ad_soyad'] ?? user.email}',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 24),
                  if (!hasProfile)
                    FilledButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ProfileSetupPage(userId: user.uid),
                          ),
                        );
                      },
                      icon: const Icon(Icons.person),
                      label: const Text('Profilini Oluştur'),
                    ),
                  if (hasProfile) ...[
                    if (hasAvatar)
                      FilledButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const AvatarPage(),
                            ),
                          );
                        },
                        icon: const Icon(Icons.visibility),
                        label: const Text('Avatarımı Göster'),
                      ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ProfileSetupPage(userId: user.uid),
                          ),
                        );
                      },
                      icon: const Icon(Icons.edit),
                      label: const Text('Bilgilerimi Güncelle'),
                    ),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => AddClothingPage(userId: user.uid),
                          ),
                        );
                      },
                      icon: const Icon(Icons.checkroom),
                      label: const Text('Kıyafet Ekle'),
                    ),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
