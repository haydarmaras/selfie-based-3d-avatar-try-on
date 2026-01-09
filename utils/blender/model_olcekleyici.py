import bpy
import sys


argv = sys.argv
argv = argv[argv.index("--") + 1:]  # --'den sonraki değerler
boy = float(argv[0])
kilo = float(argv[1])
cinsiyet = argv[2]
model_path = argv[3]  # Model dosyası

# Sahneyi temizleme kısımı
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Modeli içe aktarma kısımı
bpy.ops.import_scene.fbx(filepath=model_path)
print(f" {cinsiyet} modeli içe aktarıldı: {model_path}")

# Modeli seçme kısımı
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# Ölçek hesaplama kısımı
base_height = 1.75  # Referans yükseklik kısımı
scale_factor = boy / base_height

# Ölçeği uygulama kısımı
obj.scale = (scale_factor, scale_factor, scale_factor)
bpy.ops.object.transform_apply(scale=True)
print(f" Ölçek uygulandı ({scale_factor:.3f})")

print("İşlem tamamlandı")
