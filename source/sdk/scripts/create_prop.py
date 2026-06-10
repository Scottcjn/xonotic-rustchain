#!/usr/bin/env python3
"""
Quick Prop Generator for Xonotic
Creates simple geometric props via Blender command line

Usage:
    ./create_prop.py box 100 50 30 my_crate
    ./create_prop.py cylinder 20 80 my_pipe
    ./create_prop.py desk 200 80 75 my_desk

Output: Creates OBJ file ready for IQM conversion
"""

import subprocess
import sys
import os

BLENDER_SCRIPTS = {
    'box': '''
import bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("{name}")
obj = bpy.data.objects.new("{name}", mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1)
for v in bm.verts:
    v.co.x *= {w}
    v.co.y *= {d}
    v.co.z *= {h}
    v.co.z += {h}/2
bm.to_mesh(mesh)
bm.free()
mat = bpy.data.materials.new(name="{name}_mat")
obj.data.materials.append(mat)
bpy.ops.wm.obj_export(filepath="{output}", export_materials=True, export_uv=True)
print("Created: {output}")
''',

    'cylinder': '''
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cylinder_add(radius={r}, depth={h}, location=(0, 0, {h}/2))
obj = bpy.context.active_object
obj.name = "{name}"
mat = bpy.data.materials.new(name="{name}_mat")
obj.data.materials.append(mat)
bpy.ops.wm.obj_export(filepath="{output}", export_materials=True, export_uv=True)
print("Created: {output}")
''',

    'desk': '''
import bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("{name}")
obj = bpy.data.objects.new("{name}", mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()

# Table dimensions
top_w, top_d, top_h = {w}, {d}, 5
leg_size, leg_height = 10, {h} - 5

# Table top
bmesh.ops.create_cube(bm, size=1)
for v in bm.verts:
    v.co.x *= top_w
    v.co.y *= top_d
    v.co.z *= top_h
    v.co.z += leg_height + top_h/2

# Legs at corners
inset = 15
for lx, ly in [(-top_w/2+inset, -top_d/2+inset), (top_w/2-inset, -top_d/2+inset),
               (-top_w/2+inset, top_d/2-inset), (top_w/2-inset, top_d/2-inset)]:
    bmesh.ops.create_cube(bm, size=1)
    for v in list(bm.verts)[-8:]:
        v.co.x = v.co.x * leg_size + lx
        v.co.y = v.co.y * leg_size + ly
        v.co.z = v.co.z * leg_height + leg_height/2

bm.to_mesh(mesh)
bm.free()
mat = bpy.data.materials.new(name="{name}_mat")
obj.data.materials.append(mat)
bpy.ops.wm.obj_export(filepath="{output}", export_materials=True, export_uv=True)
print("Created: {output}")
''',

    'sphere': '''
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(radius={r}, location=(0, 0, {r}))
obj = bpy.context.active_object
obj.name = "{name}"
mat = bpy.data.materials.new(name="{name}_mat")
obj.data.materials.append(mat)
bpy.ops.wm.obj_export(filepath="{output}", export_materials=True, export_uv=True)
print("Created: {output}")
''',

    'platform': '''
import bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("{name}")
obj = bpy.data.objects.new("{name}", mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1)
for v in bm.verts:
    v.co.x *= {w}
    v.co.y *= {d}
    v.co.z *= {h}
    v.co.z += {h}/2
bm.to_mesh(mesh)
bm.free()
mat = bpy.data.materials.new(name="{name}_mat")
obj.data.materials.append(mat)
bpy.ops.wm.obj_export(filepath="{output}", export_materials=True, export_uv=True)
print("Created: {output}")
'''
}

def show_help():
    print("Quick Prop Generator for Xonotic")
    print("")
    print("Usage:")
    print("  ./create_prop.py <type> <dimensions> <name>")
    print("")
    print("Types:")
    print("  box <width> <depth> <height> <name>")
    print("  cylinder <radius> <height> <name>")
    print("  desk <width> <depth> <height> <name>")
    print("  sphere <radius> <name>")
    print("  platform <width> <depth> <height> <name>")
    print("")
    print("Examples:")
    print("  ./create_prop.py box 100 50 30 crate")
    print("  ./create_prop.py cylinder 20 100 pipe")
    print("  ./create_prop.py desk 200 80 75 office_desk")
    print("")
    print("Output: Creates <name>.obj in current directory")

def main():
    if len(sys.argv) < 3:
        show_help()
        sys.exit(1)

    prop_type = sys.argv[1].lower()

    if prop_type not in BLENDER_SCRIPTS:
        print(f"Unknown prop type: {prop_type}")
        show_help()
        sys.exit(1)

    # Parse arguments based on type
    try:
        if prop_type in ['box', 'desk', 'platform']:
            w, d, h = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
            name = sys.argv[5] if len(sys.argv) > 5 else prop_type
            params = {'w': w, 'd': d, 'h': h, 'name': name}
        elif prop_type in ['cylinder', 'sphere']:
            r = float(sys.argv[2])
            if prop_type == 'cylinder':
                h = float(sys.argv[3])
                name = sys.argv[4] if len(sys.argv) > 4 else prop_type
                params = {'r': r, 'h': h, 'name': name}
            else:
                name = sys.argv[3] if len(sys.argv) > 3 else prop_type
                params = {'r': r, 'name': name}
    except (IndexError, ValueError) as e:
        print(f"Error parsing arguments: {e}")
        show_help()
        sys.exit(1)

    output = os.path.abspath(f"{name}.obj")
    params['output'] = output

    # Generate Blender script
    script = BLENDER_SCRIPTS[prop_type].format(**params)

    # Run Blender
    print(f"Creating {prop_type}: {name}")
    result = subprocess.run(
        ['blender', '--background', '--python-expr', script],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"Success! Created: {output}")
        print(f"\nConvert to IQM:")
        print(f"  /home/scott/Games/Xonotic/source/iqm/iqm {name}.iqm {name}.obj")
    else:
        print("Error creating prop:")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
