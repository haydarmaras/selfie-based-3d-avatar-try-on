import bpy
import json
import os

def hex_from_rgb(rgb):
    r,g,b = rgb
    return (r/255, g/255, b/255, 1)

# Dosya yolları
ROOT = r"C:\okul\bitirme_projesi"
FACE_JSON = os.path.join(ROOT, "utils", "blender_integration", "face_data.json")
HAIR_COLOR_JSON = os.path.join(ROOT, "utils", "blender_integration", "hair_color.json")
SKIN_COLOR_JSON = os.path.join(ROOT, "utils", "blender_integration", "skin_color.json")
EYE_COLOR_JSON = os.path.join(ROOT, "utils", "blender_integration", "eye_color.json")

HAIR_MODEL = os.path.join(ROOT, "hair_models", "short_hair.obj")   # buraya saç modeli koyacaksın

OUTPUT = os.path.join(ROOT, "utils", "outputs", "avatar_out.glb")


# ---------------- HAIR MODEL IMPORT ----------------
def import_hair_model(hair_path):
    bpy.ops.import_scene.obj(filepath=hair_path)
    hair_obj = bpy.context.selected_objects[0]
    return hair_obj


# ---------------- APPLY COLORS ----------------
def apply_material(obj, color):
    mat = bpy.data.materials.new(name="mat_auto")
    mat.diffuse_color = hex_from_rgb(color)
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------- MAIN ----------------
def main():
    # Load colors
    with open(HAIR_COLOR_JSON) as f:
        hair_color = json.load(f)

    with open(SKIN_COLOR_JSON) as f:
        skin_color = json.load(f)

    with open(EYE_COLOR_JSON) as f:
        eye_color = json.load(f)

    # Assume body mesh is named "high-poly.001"
    body = bpy.data.objects["high-poly.001"]
    apply_material(body, skin_color)

    # Apply eye color (material name: "eyes" or similar)
    for mat in bpy.data.materials:
        if "eye" in mat.name.lower():
            mat.diffuse_color = hex_from_rgb(eye_color)

    # Import hair
    hair = import_hair_model(HAIR_MODEL)

    # Parent to head
    head_bone = bpy.data.objects["armature"].pose.bones["head"]
    bpy.ops.object.select_all(action='DESELECT')
    hair.select_set(True)
    bpy.context.view_layer.objects.active = hair
    bpy.ops.object.parent_set(type='ARMATURE')

    # Apply hair color
    apply_material(hair, hair_color)

    # Export GLB
    bpy.ops.export_scene.gltf(filepath=OUTPUT, export_format='GLB')
    print("GLB üretildi:", OUTPUT)


main()
