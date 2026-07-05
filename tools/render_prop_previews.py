"""Blender headless script: render preview PNGs for the bounty #14015 props that
are missing one (hash_block_crate, validator_pillar, vintage_tower).

hash_block_crate and validator_pillar ship as .md3 (already spec-compliant format),
so this script parses the MD3 binary directly and builds a Blender mesh from its
vertex/triangle/UV data (frame 0). vintage_tower ships as .obj, so it is imported
directly.

Run with:
    blender --background --factory-startup --python tools/render_prop_previews.py
"""
import bpy
import bmesh
import struct
import math
import os
import mathutils

REPO = "/tmp/agent-x36/xonotic-rustchain"
PROPS = os.path.join(REPO, "pk3_build/models/props")


def parse_md3(path):
    data = open(path, "rb").read()
    ident, version = struct.unpack_from("<4si", data, 0)
    assert ident == b"IDP3"
    flags, num_frames, num_tags, num_surfaces, num_skins = struct.unpack_from("<5i", data, 72)
    ofs_frames, ofs_tags, ofs_surfaces, ofs_eof = struct.unpack_from("<4i", data, 92)
    surfaces = []
    surf_off = ofs_surfaces
    for s in range(num_surfaces):
        base = surf_off
        s_flags, s_num_frames, s_num_shaders, s_num_verts, s_num_tris = struct.unpack_from("<5i", data, base + 68)
        s_ofs_tris, s_ofs_shaders, s_ofs_st, s_ofs_xyzn, s_ofs_end = struct.unpack_from("<5i", data, base + 88)
        tris = [struct.unpack_from("<3i", data, base + s_ofs_tris + i * 12) for i in range(s_num_tris)]
        sts = [struct.unpack_from("<2f", data, base + s_ofs_st + i * 8) for i in range(s_num_verts)]
        verts = []
        for i in range(s_num_verts):
            x, y, z, n = struct.unpack_from("<3hH", data, base + s_ofs_xyzn + i * 8)
            verts.append((x / 64.0, y / 64.0, z / 64.0))
        surfaces.append({"tris": tris, "sts": sts, "verts": verts})
        surf_off = base + s_ofs_end
    return surfaces


def mesh_from_md3(name, md3_path, texture_path=None):
    surfaces = parse_md3(md3_path)
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("uv")
    for surf in surfaces:
        bverts = [bm.verts.new(v) for v in surf["verts"]]
        bm.verts.ensure_lookup_table()
        for tri in surf["tris"]:
            try:
                face = bm.faces.new([bverts[i] for i in tri])
            except ValueError:
                continue
            for loop, idx in zip(face.loops, tri):
                loop[uv_layer].uv = surf["sts"][idx]
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    if texture_path and os.path.exists(texture_path):
        mat = bpy.data.materials.new(name + "_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = bpy.data.images.load(texture_path)
        mat.node_tree.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
        obj.data.materials.append(mat)
    return obj


def setup_render(target_obj, out_path, img_size=768):
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.scene.render.resolution_x = img_size
    bpy.context.scene.render.resolution_y = img_size
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.world = bpy.data.worlds.new("World")
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.07, 0.08, 0.09, 1.0)

    bbox_corners = [target_obj.matrix_world @ mathutils.Vector(c) for c in target_obj.bound_box]
    xs = [c.x for c in bbox_corners]
    ys = [c.y for c in bbox_corners]
    zs = [c.z for c in bbox_corners]
    cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    radius = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    dist = radius * 1.7
    cam.location = (cx + dist * 0.7, cy - dist * 0.9, cz + dist * 0.7)
    direction = mathutils.Vector((cx, cy, cz)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam

    sun_data = bpy.data.lights.new("sun", type='SUN')
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_data)
    sun.location = (cx + dist, cy - dist, cz + dist * 1.5)
    sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(sun)

    fill_data = bpy.data.lights.new("fill", type='AREA')
    fill_data.energy = 400.0
    fill_data.size = radius * 3
    fill = bpy.data.objects.new("fill", fill_data)
    fill.location = (cx - dist * 0.6, cy + dist, cz + dist * 0.4)
    bpy.context.collection.objects.link(fill)

    bpy.context.scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)


import mathutils


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def render_md3_prop(name):
    clear_scene()
    d = os.path.join(PROPS, name)
    md3 = os.path.join(d, f"{name}.md3")
    tex = os.path.join(d, f"{name}.tga")
    obj = mesh_from_md3(name, md3, tex)
    out = os.path.join(d, f"{name}_preview.png")
    setup_render(obj, out)
    print("Rendered", out)


def render_obj_prop(name):
    clear_scene()
    d = os.path.join(PROPS, name)
    obj_path = os.path.join(d, f"{name}.obj")
    bpy.ops.wm.obj_import(filepath=obj_path)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    out = os.path.join(d, f"{name}_preview.png")
    setup_render(meshes[0], out)
    print("Rendered", out)


render_md3_prop("hash_block_crate")
render_md3_prop("validator_pillar")
render_obj_prop("vintage_tower")
