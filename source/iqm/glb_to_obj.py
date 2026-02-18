#!/usr/bin/env python3
"""
Blender script to convert GLB to OBJ format for IQM compilation.
Run with: blender --background --python glb_to_obj.py -- input.glb output.obj

This script:
1. Imports GLB file
2. Applies transforms
3. Exports as OBJ with materials
4. Extracts textures for Xonotic skin files
"""
import bpy
import sys
import os

def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def convert_glb_to_obj(input_path, output_path):
    """Convert GLB to OBJ with proper settings for IQM"""

    # Clear existing objects
    clear_scene()

    # Import GLB
    print(f"Importing: {input_path}")
    bpy.ops.import_scene.gltf(filepath=input_path)

    # Select all imported objects
    bpy.ops.object.select_all(action='SELECT')

    # Apply all transforms
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Join all mesh objects into one
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if len(mesh_objects) > 1:
        bpy.context.view_layer.objects.active = mesh_objects[0]
        for obj in mesh_objects:
            obj.select_set(True)
        bpy.ops.object.join()

    # Get output directory for textures
    output_dir = os.path.dirname(output_path)
    base_name = os.path.splitext(os.path.basename(output_path))[0]

    # Export textures from materials
    texture_map = {}
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    tex_name = f"{base_name}_{mat.name}"
                    tex_path = os.path.join(output_dir, f"{tex_name}.png")

                    # Save texture
                    img = node.image
                    if img.packed_file:
                        img.unpack(method='WRITE_LOCAL')
                    img.filepath_raw = tex_path
                    img.file_format = 'PNG'
                    try:
                        img.save()
                        texture_map[mat.name] = tex_name
                        print(f"Saved texture: {tex_path}")
                    except Exception as e:
                        print(f"Could not save texture for {mat.name}: {e}")

    # Export OBJ
    print(f"Exporting: {output_path}")
    bpy.ops.wm.obj_export(
        filepath=output_path,
        export_selected_objects=False,
        export_uv=True,
        export_normals=True,
        export_colors=False,
        export_materials=True,
        export_triangulated_mesh=True,
        forward_axis='Y',
        up_axis='Z',
        global_scale=1.0
    )

    # Generate .skin file for Xonotic
    skin_path = os.path.join(output_dir, f"{base_name}.skin")
    if texture_map:
        with open(skin_path, 'w') as f:
            for mat_name, tex_name in texture_map.items():
                # Xonotic skin format: material_name,texture_path (no extension)
                f.write(f"{mat_name},models/{base_name}/{tex_name}\n")
        print(f"Generated skin file: {skin_path}")

    print("Conversion complete!")
    return True

if __name__ == "__main__":
    # Get arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        print("Usage: blender --background --python glb_to_obj.py -- input.glb output.obj")
        sys.exit(1)

    if len(argv) < 2:
        print("Usage: blender --background --python glb_to_obj.py -- input.glb output.obj")
        sys.exit(1)

    input_glb = argv[0]
    output_obj = argv[1]

    if not os.path.exists(input_glb):
        print(f"Error: Input file not found: {input_glb}")
        sys.exit(1)

    success = convert_glb_to_obj(input_glb, output_obj)
    sys.exit(0 if success else 1)
