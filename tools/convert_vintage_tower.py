"""Blender headless script: import vintage_tower.obj and export vintage_tower.iqm
using the repo's bundled Lee Salzman IQM exporter (source/iqm/blender-4.1/iqm_export.py).

Run with:
    blender --background --factory-startup --python tools/convert_vintage_tower.py
"""
import bpy
import os
import sys
import importlib.util

REPO_ROOT = "/tmp/agent-x36/xonotic-rustchain"
OBJ_PATH = os.path.join(REPO_ROOT, "pk3_build/models/props/vintage_tower/vintage_tower.obj")
IQM_PATH = os.path.join(REPO_ROOT, "pk3_build/models/props/vintage_tower/vintage_tower.iqm")
EXPORTER_PATH = os.path.join(REPO_ROOT, "source/iqm/blender-4.1/iqm_export.py")

# --- Clear the default scene ---
bpy.ops.wm.read_factory_settings(use_empty=True)

# --- Import the OBJ ---
bpy.ops.wm.obj_import(filepath=OBJ_PATH)

imported = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print("Imported mesh objects:", [o.name for o in imported])
for o in imported:
    print(" ", o.name, "verts:", len(o.data.vertices), "polys:", len(o.data.polygons),
          "materials:", [m.name if m else None for m in o.data.materials])

# --- Load the bundled IQM exporter module directly (avoid addon registration quirks) ---
spec = importlib.util.spec_from_file_location("iqm_export", EXPORTER_PATH)
iqm_export = importlib.util.module_from_spec(spec)
sys.modules["iqm_export"] = iqm_export
spec.loader.exec_module(iqm_export)

# Select all mesh objects for export
bpy.ops.object.select_all(action='DESELECT')
for o in imported:
    o.select_set(True)
bpy.context.view_layer.objects.active = imported[0] if imported else None

matfun = lambda prefix, image: prefix  # material name format: "m" (material name only)

iqm_export.exportIQM(
    bpy.context,
    IQM_PATH,
    True,   # usemesh
    True,   # usemods
    False,  # useskel (static prop, no bones)
    True,   # usebbox
    False,  # usecol
    1.0,    # usescale
    "",     # animspec
    matfun,
    False,  # derigify
    "",     # boneorder
    False,  # namedmaterialmeshes
)

print("Wrote", IQM_PATH, "size:", os.path.getsize(IQM_PATH) if os.path.exists(IQM_PATH) else "MISSING")
