import bpy
import os
import math

HAIR_MODELS_DIR = r"C:\okul\bitirme_projesi\hair_models"
OUTPUT_DIR = r"C:\okul\bitirme_projesi\hair_previews"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def setup_world():
    if bpy.data.worlds:
        world = bpy.data.worlds[0]
    else:
        world = bpy.data.worlds.new("World")

    bpy.context.scene.world = world
    world.use_nodes = True

    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    bg = nodes.new(type="ShaderNodeBackground")
    bg.inputs[0].default_value = (1, 1, 1, 1)  # BEYAZ
    bg.inputs[1].default_value = 1.0

    output = nodes.new(type="ShaderNodeOutputWorld")
    links.new(bg.outputs[0], output.inputs[0])


def setup_camera_and_light(target_obj):
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    cam.location = (0, -1.8, 0.8)
    cam.rotation_euler = (math.radians(90), 0, 0)

    light_data = bpy.data.lights.new(name="KeyLight", type="AREA")
    light = bpy.data.objects.new(name="KeyLight", object_data=light_data)
    bpy.context.collection.objects.link(light)
    light.location = (0, -1, 2)
    light.data.energy = 1500

def ensure_material(obj):
    mat = bpy.data.materials.new(name="Hair_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1)
    bsdf.inputs["Roughness"].default_value = 0.5
    obj.data.materials.clear()
    obj.data.materials.append(mat)

def render_hair_model(obj_path, output_path):
    clear_scene()
    setup_world()

    bpy.ops.wm.obj_import(filepath=obj_path)

    hair_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            hair_obj = obj
            break

    if hair_obj is None:
        print("Mesh bulunamadı:", obj_path)
        return

    bpy.context.view_layer.objects.active = hair_obj
    hair_obj.location = (0, 0, 0)
    hair_obj.scale = (1.2, 1.2, 1.2)

    ensure_material(hair_obj)
    setup_camera_and_light(hair_obj)

    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.filepath = output_path
    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 512
    bpy.context.scene.render.film_transparent = False

    bpy.ops.render.render(write_still=True)

def process_all():
    for f in os.listdir(HAIR_MODELS_DIR):
        if f.lower().endswith(".obj"):
            print("Render:", f)
            render_hair_model(
                os.path.join(HAIR_MODELS_DIR, f),
                os.path.join(OUTPUT_DIR, f.replace(".obj", ".png"))
            )

    print("=== THUMBNAILLER TAMAM ===")

process_all()
