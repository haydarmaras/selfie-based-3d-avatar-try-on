# Selfie-Based 3D Avatar & Virtual Try-On

Flutter + FastAPI + Firebase + Blender tabanlı bitirme projesi.

## Mimari

`Flutter → FastAPI → Firebase Storage/Firestore → Blender → GLB → Flutter`

### Akış

1. Kullanıcı kayıt/giriş yapar.
2. Boy, kilo, omuz, bel, kalça ve bacak uzunluğunu girer.
3. Ön ve yan selfie yükler.
4. FastAPI görselleri Firebase Storage'a kaydeder.
5. MediaPipe ile yüz landmark'ları çıkarılır; görünüş renkleri yaklaşık olarak tahmin edilir.
6. Blender, cinsiyete uygun base modelini açar ve ölçülere göre bölgesel gövde ölçeklemesi uygular.
7. Varsa saç modeli başa eklenir.
8. Varsa kıyafet fotoğrafından üst gövde için 3D kıyafet kabuğu oluşturulur.
9. GLB Firebase Storage'a yüklenir ve Firestore'daki `avatar_url` güncellenir.
10. Flutter `model_viewer_plus` ile avatarı gösterir.

## Klasör yapısı

```text
project-root/
├─ main.py
├─ requirements.txt
├─ serviceAccountKey.json       # LOKAL, GitHub'a yüklenmez
├─ base_models/
│  ├─ male.glb                  # LOKAL model asset'i
│  └─ female.glb                # LOKAL model asset'i
├─ hair_models/                 # opsiyonel
│  ├─ male_short_middle_part.glb
│  └─ female_default.glb
├─ clothes/                     # otomatik oluşturulur
├─ outputs/                     # otomatik oluşturulur
├─ utils/
│  ├─ api.py
│  ├─ avatar_generator.py
│  ├─ config.py
│  └─ firebase_init.py
├─ blender_scripts/
│  └─ build_avatar.py
└─ mobile/
```

## 1. Firebase Admin

Firebase Console'dan Python Admin SDK service-account JSON dosyasını alın ve proje köküne:

`serviceAccountKey.json`

adıyla koyun. Bu dosyayı GitHub'a yüklemeyin.

Storage bucket varsayılan olarak:

`bitirmeprojesi-9b244.firebasestorage.app`

Kendi bucket'ınız farklıysa `FIREBASE_STORAGE_BUCKET` ortam değişkenini ayarlayın.

## 2. Base model ve saç modelleri

Backend'in çalışması için en az:

- `base_models/male.glb`
- `base_models/female.glb`

gereklidir. Saç modelleri opsiyoneldir; bulunmazsa saç importu atlanır.

Bu binary dosyalar `.gitignore` ile dışarıda tutulur. Bu nedenle repository klonlandığında otomatik olarak gelmez.

## 3. Blender

Blender 4.x/5.x kurulu olmalıdır. Backend Blender'ı şu sırayla arar:

1. `BLENDER_EXE` ortam değişkeni
2. Bilinen Windows Blender yolları
3. PATH içindeki `blender`

Örnek PowerShell:

```powershell
$env:BLENDER_EXE="C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
```

## 4. Python backend

Python sanal ortamı oluşturun:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Kontrol:

`GET http://127.0.0.1:8000/health`

`{"status":"ok", ...}` dönmelidir.

## 5. Flutter

```powershell
cd mobile
flutter clean
flutter pub get
flutter run
```

Android emulator kullanılıyorsa backend adresi:

`http://10.0.2.2:8000`

Fiziksel Android cihaz kullanıyorsanız `profile_setup_page.dart` ve `add_clothing_page.dart` içindeki backend adresini bilgisayarınızın LAN IP'si ile değiştirin; örneğin `http://192.168.1.20:8000`.

## Firestore `users/{uid}` alanları

```text
ad_soyad
cinsiyet
boy
kilo
omuz_genisligi
bel_cevresi
kalca_cevresi
bacak_uzunlugu
selfie_front_url
selfie_side_url
avatar_url
avatar_status
avatar_error
has_clothing
clothing_storage_path
face_landmarks_count
```

## API

### `GET /health`

Backend durumunu kontrol eder.

### `POST /avatar_olustur`

Multipart alanları:

- `user_id`
- `selfie_front`
- `selfie_side`
- `boy`
- `kilo`
- `cinsiyet`
- `omuz_genisligi`
- `bel_cevresi`
- `kalca_cevresi`
- `bacak_uzunlugu`

### `POST /kiyafet_ekle`

Multipart alanları:

- `user_id`
- `clothing_image`

## Önemli teknik not

Bu sürümde kıyafet, yüklenen 2D fotoğraftan avatarın üst gövdesi üzerinde 3D bir kabuk olarak oluşturulur ve görsel bu kabuğun materyaline uygulanır. Bu, önceki yalnızca `body` materyalini değiştiren uygulamadan daha doğru bir 3D sonuç verir; ancak fizik tabanlı kumaş simülasyonu veya tek fotoğraftan gerçek 3D giysi rekonstrüksiyonu değildir.

SMPL-X modeli repository'de binary asset olarak bulunmadığı için mevcut üretim hattı base GLB üzerinden çalışır. SMPL-X'e geçiş yapılacaksa gerçek SMPL-X model dosyaları ayrıca kurulmalıdır.

## Güvenlik

- `serviceAccountKey.json` GitHub'a yüklenmez.
- Avatar, selfie ve kıyafet dosyaları GitHub'a yüklenmez.
- Üretimde `allow_origins=["*"]` yerine uygulamanızın gerçek domain/IP listesini kullanın.
