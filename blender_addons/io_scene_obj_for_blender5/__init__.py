bl_info = {
    "name": "OBJ Import/Export for Blender 5.0",
    "author": "Custom",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "File > Import-Export",
    "description": "Restored OBJ importer/exporter for Blender 5.0",
    "category": "Import-Export",
}

import importlib
from . import import_obj, export_obj

importlib.reload(import_obj)
importlib.reload(export_obj)

def register():
    import_obj.register()
    export_obj.register()

def unregister():
    import_obj.unregister()
    export_obj.unregister()
