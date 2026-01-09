import bpy
import os
import sys
import json

# --------------------------------------------------
# ARG
# --------------------------------------------------
argv = sys.argv
user_id = argv[argv.index("--") + 1] if "--" in argv else None
if not user_id:
    raise RuntimeError("user_id yok")

print("[BLENDER] Avatar build:", user_id)

# --------------------------------------------------
# PATHS
# --------------------------------------------------
PROJECT_ROOT = r"C:\okul\bitirme_projesi"
CFG_DIR = os.path.join(PROJECT_ROOT, "utils", "blender_integration")
HAIR_DIR = os.path.join(PROJECT_ROOT, "hair_models")

cfg_path = os.path.join(CFG_DIR, f"{user_id}_config.json")
if not os.path.exists(cfg_path):
    raise RuntimeError("Config yok: " + cfg_path)

with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

base_model = cfg["base_model_path"]
output_glb = cfg["output_glb_path"]
colors = cfg["colors"]
hair_preset = cfg.get("hair_preset", "")
clothing_path = cfg.get("clothing_local_path", "")

# --------------------------------------------------
# UTILS
# --------------------------------------------------
def rgba(c):
    return [c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1.0]

def meshes():
    return [o for o in bpy.data.objects if o.type == "MESH"]

def get_by_name_ci(target_name: str):
    t = target_name.lower()
    for o in bpy.data.objects:
        if o.name.lower() == t:
            return o
    return None

def color_object(obj, color_rgba):
    if not obj or obj.type != "MESH":
        return
    for slot in obj.material_slots:
        mat = slot.material
        if not mat:
            continue
        try:
            mat.diffuse_color = color_rgba
        except:
            pass

        if getattr(mat, "use_nodes", False):
            nodes = mat.node_tree.nodes
            for n in nodes:
                if n.type == "BSDF_PRINCIPLED":
                    n.inputs["Base Color"].default_value = color_rgba
                    break

def join_mesh_list(mesh_list, new_name="Hair"):
    if not mesh_list:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in mesh_list:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_list[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = new_name
    return joined

def parent_keep_transform(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()

def apply_clothing_texture(body_obj, image_path):
    if not body_obj or not os.path.exists(image_path):
        return

    # materyal oluştur
    mat = bpy.data.materials.new(name="ClothingTex")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # temiz
    for n in list(nodes):
        nodes.remove(n)

    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nodes.new(type="ShaderNodeTexImage")

    tex.image = bpy.data.images.load(image_path)

    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # body'ye uygula (en sona eklemek yerine 0'a koy)
    if len(body_obj.data.materials) == 0:
        body_obj.data.materials.append(mat)
    else:
        body_obj.data.materials[0] = mat

    print("[BLENDER] ✔ Clothing texture applied:", image_path)

# --------------------------------------------------
# RESET + IMPORT
# --------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

if not os.path.exists(base_model):
    raise RuntimeError("Base model dosyası yok: " + base_model)

bpy.ops.import_scene.gltf(filepath=base_model)

# --------------------------------------------------
# FIND PARTS (isimle bul, olmazsa fallback)
# --------------------------------------------------
body = get_by_name_ci("body")
head = get_by_name_ci("head")
eyes = get_by_name_ci("eyes")

# fallback: body yoksa en büyük mesh
if body is None:
    body = max(meshes(), key=lambda o: (o.dimensions.x * o.dimensions.y * o.dimensions.z))

# fallback: head yoksa en yukarıdaki mesh
if head is None:
    ms = meshes()
    ms.sort(key=lambda o: o.location.z, reverse=True)
    head = ms[0] if ms else None

print("[BLENDER] body:", body.name if body else "yok")
print("[BLENDER] head:", head.name if head else "yok")
print("[BLENDER] eyes:", eyes.name if eyes else "yok")

# --------------------------------------------------
# COLORS
# --------------------------------------------------
color_object(body, rgba(colors["skin"]))
if eyes:
    color_object(eyes, rgba(colors["eye"]))

# --------------------------------------------------
# HAIR IMPORT
# --------------------------------------------------
if hair_preset:
    hair_path = os.path.join(HAIR_DIR, hair_preset)
    if os.path.exists(hair_path):
        print("[BLENDER] Hair import:", hair_path)

        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=hair_path)
        new_meshes = [o for o in (set(bpy.data.objects) - before) if o.type == "MESH"]

        hair = join_mesh_list(new_meshes, "Hair")
        if hair:
            color_object(hair, rgba(colors["hair"]))
            if head:
                parent_keep_transform(hair, head)
            print("[BLENDER] ✔ Hair attached")
    else:
        print("[BLENDER] Hair preset yok:", hair_path)

# --------------------------------------------------
# CLOTHING APPLY
# --------------------------------------------------
if clothing_path and os.path.exists(clothing_path):
    apply_clothing_texture(body, clothing_path)

# --------------------------------------------------
# EXPORT
# --------------------------------------------------
os.makedirs(os.path.dirname(output_glb), exist_ok=True)

bpy.ops.export_scene.gltf(
    filepath=output_glb,
    export_format="GLB",
    export_apply=True,
)

print("[BLENDER] ✔ GLB hazır:", output_glb)
