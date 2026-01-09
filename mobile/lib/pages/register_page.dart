import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

class RegisterPage extends StatefulWidget {
  final VoidCallback onLoginTap;

  const RegisterPage({super.key, required this.onLoginTap});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final emailCtrl = TextEditingController();
  final passCtrl = TextEditingController();
  final pass2Ctrl = TextEditingController();

  String? errorMessage;

  bool isValidEmail(String email) {
    return email.endsWith("@gmail.com");
  }

  bool isValidPassword(String pass) {
    final hasLetter = RegExp(r'[A-Za-z]').hasMatch(pass);
    final hasNumber = RegExp(r'[0-9]').hasMatch(pass);
    return pass.length >= 6 && hasLetter && hasNumber;
  }

  Future<void> register() async {
    String email = emailCtrl.text.trim();
    String pass = passCtrl.text.trim();
    String pass2 = pass2Ctrl.text.trim();

    setState(() => errorMessage = null);

    if (!isValidEmail(email)) {
      setState(() => errorMessage = "Email sadece @gmail.com olabilir.");
      return;
    }

    if (pass != pass2) {
      setState(() => errorMessage = "Şifreler aynı değil!");
      return;
    }

    if (!isValidPassword(pass)) {
      setState(
        () =>
            errorMessage = "Şifre en az 6 karakter, 1 harf ve 1 sayı içermeli.",
      );
      return;
    }

    try {
      await FirebaseAuth.instance.createUserWithEmailAndPassword(
        email: email,
        password: pass,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Kayıt başarılı!")));

      widget.onLoginTap(); // Login sayfasına dön
    } on FirebaseAuthException catch (e) {
      setState(() {
        if (e.code == "email-already-in-use") {
          errorMessage = "Bu email zaten kayıtlı.";
        } else if (e.code == "invalid-email") {
          errorMessage = "Geçersiz email formatı.";
        } else if (e.code == "weak-password") {
          errorMessage = "Şifre çok zayıf.";
        } else {
          errorMessage = "Firebase Hatası: ${e.message}";
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Kayıt Ol")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: emailCtrl,
              decoration: const InputDecoration(
                labelText: "Email (@gmail.com)",
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: passCtrl,
              obscureText: true,
              decoration: const InputDecoration(labelText: "Şifre"),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: pass2Ctrl,
              obscureText: true,
              decoration: const InputDecoration(labelText: "Şifre Tekrar"),
            ),
            const SizedBox(height: 16),
            if (errorMessage != null)
              Text(
                errorMessage!,
                style: const TextStyle(color: Colors.red, fontSize: 14),
              ),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: register, child: const Text("Kayıt Ol")),
            const SizedBox(height: 8),
            TextButton(
              onPressed: widget.onLoginTap,
              child: const Text("Zaten hesabın var mı? Giriş Yap"),
            ),
          ],
        ),
      ),
    );
  }
}
