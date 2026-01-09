import bpy
from bpy_extras.io_utils import ImportHelper

class IMPORT_OT_obj(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.custom_obj"
    bl_label = "Import OBJ (Custom)"
    filename_ext = ".obj"
    filter_glob = "*.obj"

    def execute(self, context):
        bpy.ops.wm.obj_import(filepath=self.filepath)
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_obj.bl_idname, text="Wavefront OBJ (.obj) - Custom")

def register():
    bpy.utils.register_class(IMPORT_OT_obj)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_obj)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
