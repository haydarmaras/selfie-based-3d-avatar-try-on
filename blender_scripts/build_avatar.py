import bpy
import bmesh
import json
import math
import os
import sys

# ============================================================
# ARGUMENTS
# ============================================================
argv = sys.argv
if "--" not in argv or len(argv) <= argv.index("--") + 1:
    raise RuntimeError("user_id eksik")
user_id = argv[argv.index("--") + 1]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CFG_DIR = os.path.join(PROJECT_ROOT, "utils", "blender_integration")

cfg_path = os.path.join(CFG_DIR, f"{user_id}_config.json")
if not os.path.isfile(cfg_path):
    raise RuntimeError(f"Config bulunamadı: {cfg_path}")

with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

base_model = cfg["base_model_path"]
output_glb = cfg["output_glb_path"]
measurements = cfg.get("measurements", {})
colors = cfg.get("colors", {})
hair_path = cfg.get("hair_model_path", "")
clothing_path = cfg.get("clothing_local_path", "")

# ============================================================
# HELPERS
# ============================================================
def clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))


def rgba(c, default):
    c = c if isinstance(c, list) and len(c) >= 3 else default
    return [clamp(c[0], 0, 255) / 255.0, clamp(c[1], 0, 255) / 255.0, clamp(c[2], 0, 255) / 255.0, 1.0]


def meshes():
    return [o for o in bpy.data.objects if o.type == "MESH"]


def find_name(name):
    target = name.lower()
    return next((o for o in bpy.data.objects if o.name.lower() == target), None)


def find_body():
    body = find_name("body")
    if body:
        return body
    ms = meshes()
    if not ms:
        raise RuntimeError("Base model içinde mesh bulunamadı.")
    return max(ms, key=lambda o: o.dimensions.x * o.dimensions.y * o.dimensions.z)


def material_with_color(name, color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.72
    mat.diffuse_color = color
    return mat


def set_object_color(obj, color):
    if not obj:
        return
    mat = material_with_color(f"{obj.name}_Appearance", color)
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        for i in range(len(obj.data.materials)):
            obj.data.materials[i] = mat


def delete_all_objects():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def apply_measurement_shape(body):
    m = {
        "boy": 175.0,
        "kilo": 75.0,
        "omuz_genisligi": 45.0,
        "bel_cevresi": 82.0,
        "kalca_cevresi": 98.0,
        "bacak_uzunlugu": 95.0,
    }
    for k in m:
        try:
            m[k] = float(measurements.get(k, m[k]))
        except (TypeError, ValueError):
            pass

    # Modelin yerel koordinatlarında z'nin dikey olduğu varsayılır.
    verts = body.data.vertices
    if not verts:
        return

    zs = [v.co.z for v in verts]
    zmin, zmax = min(zs), max(zs)
    zspan = max(zmax - zmin, 1e-6)

    ref = {"chest": 96.0, "waist": 82.0, "hip": 98.0, "shoulder": 45.0, "weight": 75.0, "leg": 95.0}
    chest_ratio = clamp(m["bel_cevresi"] and m["bel_cevresi"] * 0 + m["bel_cevresi"] or ref["chest"], 40, 180)
    chest_ratio = clamp(m.get("omuz_genisligi", ref["shoulder"]) / ref["shoulder"], 0.70, 1.35)
    torso_chest = clamp(m.get("omuz_genisligi", ref["shoulder"]) / ref["shoulder"], 0.75, 1.30)
    waist_ratio = clamp(m["bel_cevresi"] / ref["waist"], 0.70, 1.45)
    hip_ratio = clamp(m["kalca_cevresi"] / ref["hip"], 0.70, 1.45)
    weight_ratio = clamp((m["kilo"] / ref["weight"]) ** 0.20, 0.85, 1.18)
    leg_ratio = clamp(m["bacak_uzunlugu"] / ref["leg"], 0.80, 1.20)

    # İlk geçiş: ölçülere göre bölgesel gövde genişliği.
    for v in verts:
        n = clamp((v.co.z - zmin) / zspan, 0.0, 1.0)
        chest_w = math.exp(-((n - 0.66) / 0.16) ** 2)
        waist_w = math.exp(-((n - 0.54) / 0.13) ** 2)
        hip_w = math.exp(-((n - 0.43) / 0.16) ** 2)
        shoulder_w = math.exp(-((n - 0.76) / 0.12) ** 2)

        radial = (
            chest_w * torso_chest
            + waist_w * waist_ratio
            + hip_w * hip_ratio
            + shoulder_w * chest_ratio
        ) / max(chest_w + waist_w + hip_w + shoulder_w, 1e-6)
        radial = clamp(radial * weight_ratio, 0.72, 1.45)
        v.co.x *= radial
        v.co.y *= radial

        # Bacak uzunluğunu kalça altına daha fazla uygula.
        if n < 0.48:
            local = n / 0.48
            v.co.z = zmin + (v.co.z - zmin) * (1.0 + (leg_ratio - 1.0) * (1.0 - local))

    # Son aşamada toplam boyu tam hedefe getir.
    zs2 = [v.co.z for v in verts]
    new_span = max(max(zs2) - min(zs2), 1e-6)
    target_m = clamp(m["boy"], 100, 250) / 100.0
    scale_z = target_m / new_span
    for v in verts:
        v.co.z = (v.co.z - min(zs2)) * scale_z

    body.data.update()
    print("[BLENDER] Ölçü tabanlı vücut şekillendirme tamamlandı:", m)


def join_new_meshes(before, name):
    new_meshes = [o for o in bpy.data.objects if o.type == "MESH" and o not in before]
    if not new_meshes:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in new_meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = new_meshes[0]
    if len(new_meshes) > 1:
        bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    return result


def attach_hair(head):
    if not hair_path or not os.path.isfile(hair_path):
        print("[BLENDER] Saç modeli yok; saç import atlandı.")
        return None

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=hair_path)
    hair = join_new_meshes(before, "Hair")
    if hair is None:
        return None

    if head:
        # Saç modelinin kendi dünya dönüşümünü koru, sonra başa parent et.
        hair.parent = head
        hair.matrix_parent_inverse = head.matrix_world.inverted()
    set_object_color(hair, rgba(colors.get("hair"), [60, 40, 30]))
    print("[BLENDER] Saç eklendi:", hair_path)
    return hair


def create_clothing_shell(body, image_path):
    if not image_path or not os.path.isfile(image_path):
        return None

    # Deforme edilmiş body'nin kopyasından üst gövde için 3D kıyafet kabuğu.
    clothing = body.copy()
    clothing.data = body.data.copy()
    clothing.name = "Clothing"
    bpy.context.collection.objects.link(clothing)

    bm = bmesh.new()
    bm.from_mesh(clothing.data)
    zmin = min(v.co.z for v in bm.verts)
    zmax = max(v.co.z for v in bm.verts)
    span = max(zmax - zmin, 1e-6)

    # T-shirt/üst giyim alanı. Alt gövdeyi kabuktan çıkar.
    keep_low = 0.40
    keep_high = 0.78
    remove = []
    for face in bm.faces:
        values = [clamp((v.co.z - zmin) / span, 0, 1) for v in face.verts]
        if max(values) < keep_low or min(values) > keep_high:
            remove.append(face)
    bmesh.ops.delete(bm, geom=remove, context="FACES")
    bm.to_mesh(clothing.data)
    bm.free()
    clothing.data.update()

    # Kabuğu birkaç mm dışarı al.
    solid = clothing.modifiers.new("ClothingThickness", "SOLIDIFY")
    solid.thickness = 0.008
    solid.offset = 1.0

    mat = bpy.data.materials.new("ClothingMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "ClothingImage"
    try:
        tex.image = bpy.data.images.load(image_path, check_existing=True)
    except Exception as exc:
        bpy.data.objects.remove(clothing, do_unlink=True)
        raise RuntimeError(f"Kıyafet görseli yüklenemedi: {exc}")
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9

    if len(clothing.data.materials) == 0:
        clothing.data.materials.append(mat)
    else:
        clothing.data.materials[0] = mat

    print("[BLENDER] 3D kıyafet kabuğu oluşturuldu:", image_path)
    return clothing

# ============================================================
# BUILD
# ============================================================
print("[BLENDER] Avatar build:", user_id)
if not os.path.isfile(base_model):
    raise RuntimeError(f"Base model yok: {base_model}")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=base_model)

body = find_body()
head = find_name("head")
eyes = find_name("eyes")

apply_measurement_shape(body)
set_object_color(body, rgba(colors.get("skin"), [220, 190, 170]))
if eyes:
    set_object_color(eyes, rgba(colors.get("eye"), [80, 80, 80]))

attach_hair(head)
create_clothing_shell(body, clothing_path)

# Kamera/ışık gerekmiyor; GLB yalnızca model olarak dışa aktarılıyor.
os.makedirs(os.path.dirname(output_glb), exist_ok=True)
if os.path.exists(output_glb):
    os.remove(output_glb)

bpy.ops.export_scene.gltf(
    filepath=output_glb,
    export_format="GLB",
    export_apply=True,
    export_materials="EXPORT",
)

if not os.path.isfile(output_glb):
    raise RuntimeError("GLB export başarısız.")

print("[BLENDER] ✔ GLB hazır:", output_glb)
