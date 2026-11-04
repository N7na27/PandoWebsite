"""Export the LapRotator Blender model as one small GLB for the landing page.

Run it with Blender 5.2 or newer (it uses Blender's own Python):
  /Applications/Blender.app/Contents/MacOS/Blender -b "<path>/LapRotator render (revB).blend" --python tools/model.py
Writes assets/model/laprotator.glb.

The .blend (revB) holds one object per part (Drum_Body, Handle, Shaft_Luer, the membrane keys...),
each with its own render material. Every material goes to the website as it is in Blender
(Principled base color, metallic, roughness, coat), so change a material there and the site follows.
Modifiers (Smooth by Angle, bevels) are applied. Lights, cameras and hidden objects are left out.
Positions and normals are stored as 16-bit (glTF KHR_mesh_quantization), which keeps the file small.
(8-bit normals showed as streaks on the glossy plastic under the studio lights.)

Each vertex also carries Cycles ambient occlusion, baked here (attribute "_AO", 0 = fully hidden).
js/model.js darkens the soft studio light with it, the way Cycles' shadows darken the render, so
creases and the gaps between parts read like the Blender renders. The bake turns with the model.

The GLB is in meters, in the frame js/model.js expects: the scope runs along +Z (toward the tip)
through x = 0, y = 0, and the camera's three buttons face -Y.

The scene's lighting goes along too (glTF scene extras "studio"), so the site lights the model like
Cycles: every area light (size, power, color) placed by where it sits relative to the render camera,
the world color, and the color management (exposure, AgX look). js/model.js keeps those lights fixed
to its own camera, like a turntable under the studio lights.
"""
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/model/laprotator.glb"

# The revB parts are scaled up 33.0646x from meters
METERS_PER_UNIT = 1 / 33.0646
# In the .blend the scope runs along -Y (toward the tip). These parts find the frame:
SCOPE = "Shaft_Luer"      # its thin tube gives the spin axis
BUTTONS = "LR_ButtonMetal"  # the camera's three buttons, which should face -Y in the GLB
# Ambient occlusion bake: how far (Blender units, about 30 mm) a surface looks for nearby parts, and samples
AO_DISTANCE = 1.0
AO_SAMPLES = 256
# The CAD tessellation has long thin triangles (around the "Pando" lettering especially). Plain smooth
# normals average them unevenly, which shows as streaks on the glossy plastic. Blender's Weighted Normal
# modifier (by face area, keeping sharp edges) evens that out. Applied to the exported copies only.
WEIGHTED_NORMALS = True


def gltf_material(mat):
    """glTF material from a Blender material (Principled BSDF values)."""
    name = mat.name if mat else "default"
    out = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": [0.8, 0.8, 0.8, 1], "metallicFactor": 0, "roughnessFactor": 1}}
    node = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if mat and mat.node_tree else None
    pbr = out["pbrMetallicRoughness"]
    if node is None:
        if mat:
            pbr["baseColorFactor"] = [float(x) for x in mat.diffuse_color]
        return out
    get = lambda k: node.inputs[k].default_value
    pbr["baseColorFactor"] = [float(x) for x in get("Base Color")]
    pbr["metallicFactor"] = float(get("Metallic"))
    pbr["roughnessFactor"] = float(get("Roughness"))
    if float(get("Coat Weight")) > 0:
        out["extensions"] = {"KHR_materials_clearcoat": {"clearcoatFactor": float(get("Coat Weight")),
                                                         "clearcoatRoughnessFactor": float(get("Coat Roughness"))}}
    return out


def evaluated(o, depsgraph):
    """World-space vertices, corner data and materials of a mesh object, with modifiers applied."""
    ev = o.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    mesh.calc_loop_triangles()
    nv, nl, nt = len(mesh.vertices), len(mesh.loops), len(mesh.loop_triangles)
    co = np.empty(nv * 3); mesh.vertices.foreach_get("co", co)
    lv = np.empty(nl, np.int64); mesh.loops.foreach_get("vertex_index", lv)
    ln = np.empty(nl * 3); mesh.corner_normals.foreach_get("vector", ln)
    tl = np.empty(nt * 3, np.int64); mesh.loop_triangles.foreach_get("loops", tl)
    tm = np.empty(nt, np.int64); mesh.loop_triangles.foreach_get("material_index", tm)
    mats = [s.material for s in o.material_slots]
    ao = np.ones(nv)
    if "AO" in mesh.color_attributes:
        rgba = np.empty(nv * 4); mesh.color_attributes["AO"].data.foreach_get("color", rgba)
        ao = rgba.reshape(-1, 4)[:, 0]
    ev.to_mesh_clear()
    m = np.array(o.matrix_world)
    pos = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
    corner_n = ln.reshape(-1, 3) @ np.linalg.inv(m[:3, :3])
    corner_n /= np.maximum(np.linalg.norm(corner_n, axis=1, keepdims=True), 1e-12)
    return pos, lv, corner_n, tl.reshape(-1, 3), tm, mats, ao


def frame(depsgraph):
    """(origin, rotation rows) that take Blender world space to the GLB frame described above."""
    pos, lv, _, tl, tm, mats, _ = evaluated(bpy.data.objects[SCOPE], depsgraph)
    tip = pos[:, 1].min()
    tube = pos[pos[:, 1] < tip + (pos[:, 1].max() - tip) * 0.5]  # the far half is only the bare tube
    origin = np.array([(tube[:, 0].min() + tube[:, 0].max()) / 2, 0, (tube[:, 2].min() + tube[:, 2].max()) / 2])
    z = np.array([0.0, -1, 0])
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        pos, lv, _, tl, tm, mats, _ = evaluated(o, depsgraph)
        hit = [i for i, m in enumerate(mats) if m and m.name == BUTTONS]
        if hit:
            c = pos[lv[tl[np.isin(tm, hit)]].reshape(-1)].mean(0) - origin
            y = -(c - z * c.dot(z)); y /= np.linalg.norm(y)
            return origin, np.stack([np.cross(y, z), y, z])
    sys.exit(f"No faces with the material {BUTTONS}")


def bake_ao(objs, depsgraph):
    """Copies of the parts (modifiers applied) with Cycles ambient occlusion baked into each vertex."""
    scene = bpy.context.scene
    coll = bpy.data.collections.new("AO bake")
    scene.collection.children.link(coll)
    copies = []
    for o in objs:
        name = o.name
        o.name = name + " (original)"  # the copy keeps the part's name
        me = bpy.data.meshes.new_from_object(o.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
        c = bpy.data.objects.new(name, me)
        c.matrix_world = o.matrix_world
        coll.objects.link(c)
        me.color_attributes.active_color = me.color_attributes.new("AO", "FLOAT_COLOR", "POINT")
        if WEIGHTED_NORMALS:
            wn = c.modifiers.new("Weighted Normal", "WEIGHTED_NORMAL")
            wn.mode = "FACE_AREA"
            wn.weight = 50
            wn.keep_sharp = True
        copies.append(c)
    for o in objs:  # only the copies may block the bake rays
        o.hide_render = True
    scene.render.engine = "CYCLES"
    scene.cycles.samples = AO_SAMPLES
    scene.world.light_settings.distance = AO_DISTANCE
    bpy.ops.object.select_all(action="DESELECT")
    for c in copies:
        c.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
    return copies


def light_rig():
    """The render camera's view of the lights: each area light's place and axes relative to the model,
    in camera space (x right, y up, looking down -z), with its radiance (power per area, W/unit²)."""
    scene = bpy.context.scene
    cam = scene.camera
    Rc = np.array(cam.matrix_world.to_3x3())
    rig = bpy.data.objects.get("LightRig")
    center = np.array(rig.matrix_world.translation) if rig else np.zeros(3)
    lights = []
    for o in scene.objects:
        if o.type != "LIGHT" or o.hide_render or o.data.type != "AREA":
            continue
        L = o.data
        w, h = L.size, (L.size_y if L.shape in ("RECTANGLE", "ELLIPSE") else L.size)
        pos = Rc.T @ (np.array(o.matrix_world.translation) - center)
        axes = Rc.T @ np.array(o.matrix_world.to_3x3())  # columns: the light's x, y and z (it shines along -z)
        lights.append({"name": o.name, "position": pos.round(4).tolist(), "axes": axes.round(5).tolist(),
                       "size": [round(w, 4), round(h, 4)], "radiance": round(L.energy / (w * h), 4),
                       "color": [round(c, 4) for c in L.color]})
    bg = scene.world.node_tree.nodes.get("Background") if scene.world and scene.world.node_tree else None
    world = [round(c * bg.inputs["Strength"].default_value, 5) for c in bg.inputs["Color"].default_value[:3]] if bg else [0, 0, 0]
    view = scene.view_settings
    return {"lights": lights, "world": world, "exposure": view.exposure, "look": view.look, "viewTransform": view.view_transform}


def collect():
    """Return ({(part, material name): [(positions, normals, AO, indices), ...]}, {material name: glTF material})."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    origin, rot = frame(depsgraph)
    parts = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render and o.visible_get()]
    copies = bake_ao(parts, depsgraph)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    materials, groups = {}, {}
    for o in sorted(copies, key=lambda o: o.name):
        pos, lv, corner_n, tris, tm, mats, ao = evaluated(o, depsgraph)
        if not len(tris):
            continue
        pos = (pos - origin) @ rot.T * METERS_PER_UNIT
        corner_n = corner_n @ rot.T
        for mi in np.unique(tm):
            mat = mats[mi] if mi < len(mats) else None
            name = mat.name if mat else "default"
            materials.setdefault(name, gltf_material(mat))
            loops = tris[tm == mi].reshape(-1)
            # One vertex per unique (position, corner normal)
            pairs = np.concatenate([lv[loops][:, None].astype(np.float64), np.round(corner_n[loops], 4)], axis=1)
            uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
            first = np.zeros(len(uniq), np.int64)
            first[inv.reshape(-1)] = np.arange(len(loops))
            vi = lv[loops][first]
            groups.setdefault((o.name, name), []).append((pos[vi], corner_n[loops][first], ao[vi], inv.reshape(-1)))
    return groups, materials


def merge(chunks):
    pos, nrm, occ, idx, base = [], [], [], [], 0
    for p, n, a, i in chunks:
        pos.append(p); nrm.append(n); occ.append(a); idx.append(i + base); base += len(p)
    return np.concatenate(pos), np.concatenate(nrm), np.concatenate(occ), np.concatenate(idx)


def main():
    global STUDIO
    STUDIO = light_rig()
    groups, materials = collect()
    if not groups:
        sys.exit("No meshes found in the .blend")
    parts = {}
    for (part, name), chunks in sorted(groups.items()):
        parts.setdefault(part, {})[name] = merge(chunks)

    # One shared quantization grid for every part: world = center + half * q
    allp = np.concatenate([g[0] for prims in parts.values() for g in prims.values()])
    lo, hi = allp.min(0), allp.max(0)
    center = (lo + hi) / 2
    half = float((hi - lo).max() / 2)

    mat_names = sorted(materials)
    blob = bytearray()
    views, accessors, meshes, nodes = [], [], [], []

    def add_view(data, stride=None, target=None):
        while len(blob) % 4:
            blob.append(0)
        view = {"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}
        if stride:
            view["byteStride"] = stride
        if target:
            view["target"] = target
        blob.extend(data)
        views.append(view)
        return len(views) - 1

    for part, prims_in in parts.items():
        prims = []
        for name, (pos, nrm, occ, idx) in prims_in.items():
            # Split anything over 65535 vertices so indices stay 16-bit
            tris = idx.reshape(-1, 3)
            start = 0
            while start < len(tris):
                used, cut = set(), len(tris) - start
                for t, row in enumerate(tris[start:]):
                    used.update(row.tolist())
                    if len(used) > 65535:
                        cut = t
                        break
                sub = tris[start:start + cut]
                start += cut
                keep, local = np.unique(sub.reshape(-1), return_inverse=True)
                q = np.round((pos[keep] - center) / half * 32767).astype(np.int16)
                q4 = np.zeros((len(q), 4), np.int16); q4[:, :3] = q
                n4 = np.zeros((len(q), 4), np.int16); n4[:, :3] = np.round(nrm[keep] * 32767).astype(np.int16)
                pv = add_view(q4.tobytes(), 8, 34962)
                accessors.append({"bufferView": pv, "componentType": 5122, "normalized": True, "count": len(q),
                                  "type": "VEC3", "min": q.min(0).tolist(), "max": q.max(0).tolist()})
                nv = add_view(n4.tobytes(), 8, 34962)
                accessors.append({"bufferView": nv, "componentType": 5122, "normalized": True, "count": len(q), "type": "VEC3"})
                o4 = np.zeros((len(q), 4), np.uint8); o4[:, 0] = np.round(np.clip(occ[keep], 0, 1) * 255).astype(np.uint8)
                ov = add_view(o4.tobytes(), 4, 34962)
                accessors.append({"bufferView": ov, "componentType": 5121, "normalized": True, "count": len(q), "type": "VEC4"})
                iv = add_view(local.astype(np.uint16).tobytes(), target=34963)
                accessors.append({"bufferView": iv, "componentType": 5123, "count": len(local), "type": "SCALAR"})
                a = len(accessors)
                prims.append({"attributes": {"POSITION": a - 4, "NORMAL": a - 3, "_AO": a - 2}, "indices": a - 1, "material": mat_names.index(name)})
        meshes.append({"name": part, "primitives": prims})
        nodes.append({"name": part, "mesh": len(meshes) - 1})
        tris = sum(len(g[3]) for g in prims_in.values()) // 3
        occ = np.concatenate([g[2] for g in prims_in.values()])
        print(f"{part:20s} {tris:6d} triangles  AO mean {occ.mean():.2f} min {occ.min():.2f}")

    nodes.append({"name": "LapRotator", "children": list(range(len(parts))),
                  "translation": center.tolist(), "scale": [half] * 3})
    while len(blob) % 4:
        blob.append(0)
    mats = [materials[m] for m in mat_names]
    used = ["KHR_mesh_quantization"] + (["KHR_materials_clearcoat"] if any("extensions" in m for m in mats) else [])
    gltf = {
        "asset": {"version": "2.0", "generator": "Pando tools/model.py (Blender, LapRotator revB)"},
        "extensionsUsed": used, "extensionsRequired": ["KHR_mesh_quantization"],
        "scene": 0, "scenes": [{"nodes": [len(nodes) - 1], "extras": {"studio": STUDIO}}],
        "nodes": nodes, "meshes": meshes, "materials": mats,
        "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": len(blob)}],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.2f} MB)")
    print(f"  lights: {', '.join(L['name'] for L in STUDIO['lights'])}; world {STUDIO['world']}; {STUDIO['viewTransform']}, {STUDIO['look']}")
    for m in mats:
        print(f"  material {m['name']}: color {[round(c, 3) for c in m['pbrMetallicRoughness']['baseColorFactor'][:3]]}")


main()
