import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'firebase_options.dart';
import 'pages/login_page.dart';
import 'pages/register_page.dart';
import 'pages/home_page.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Avatar App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.indigo,
        scaffoldBackgroundColor: const Color(0xFFF8F3FF),
      ),
      home: const AuthGate(),
    );
  }
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final user = snap.data;
        if (user == null) return const AuthSwitcher();
        return const HomePage();
      },
    );
  }
}

class AuthSwitcher extends StatefulWidget {
  const AuthSwitcher({super.key});

  @override
  State<AuthSwitcher> createState() => _AuthSwitcherState();
}

class _AuthSwitcherState extends State<AuthSwitcher> {
  bool showLogin = true;

  void toggle() => setState(() => showLogin = !showLogin);

  @override
  Widget build(BuildContext context) {
    return showLogin
        ? LoginPage(onRegisterTap: toggle)
        : RegisterPage(onLoginTap: toggle);
  }
}
