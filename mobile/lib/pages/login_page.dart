import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class LoginPage extends StatefulWidget {
  final VoidCallback onRegisterTap;

  const LoginPage({super.key, required this.onRegisterTap});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _auth = AuthService();
  final _formKey = GlobalKey<FormState>();
  final emailCtrl = TextEditingController();
  final passCtrl = TextEditingController();
  bool loading = false;

  @override
  void dispose() {
    emailCtrl.dispose();
    passCtrl.dispose();
    super.dispose();
  }

  Future<void> login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => loading = true);

    try {
      await _auth.loginWithEmail(emailCtrl.text, passCtrl.text);
    } catch (e) {
      ScaffoldMessenger.of(
        // ignore: use_build_context_synchronously
        context,
      ).showSnackBar(SnackBar(content: Text("Hata: $e")));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Card(
            elevation: 4,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    const Text(
                      "Avatar Uygulaması",
                      style: TextStyle(fontSize: 24),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: emailCtrl,
                      decoration: const InputDecoration(
                        labelText: "E-posta",
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v!.isEmpty ? "E-posta giriniz" : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: passCtrl,
                      decoration: const InputDecoration(
                        labelText: "Şifre",
                        border: OutlineInputBorder(),
                      ),
                      obscureText: true,
                      validator: (v) =>
                          v!.length < 6 ? "En az 6 karakter" : null,
                    ),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: loading ? null : login,
                      child: loading
                          ? const CircularProgressIndicator()
                          : const Text("Giriş Yap"),
                    ),
                    TextButton(
                      onPressed: widget.onRegisterTap,
                      child: const Text("Hesabın yok mu? Kayıt Ol"),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
