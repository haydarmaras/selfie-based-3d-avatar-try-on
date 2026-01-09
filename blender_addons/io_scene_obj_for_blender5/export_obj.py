import bpy
from bpy_extras.io_utils import ExportHelper

class EXPORT_OT_obj(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.custom_obj"
    bl_label = "Export OBJ (Custom)"
    filename_ext = ".obj"
    filter_glob = "*.obj"

    def execute(self, context):
        bpy.ops.wm.obj_export(filepath=self.filepath)
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(EXPORT_OT_obj.bl_idname, text="Wavefront OBJ (.obj) - Custom")

def register():
    bpy.utils.register_class(EXPORT_OT_obj)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_obj)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
