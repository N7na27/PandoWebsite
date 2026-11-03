"""Export the LapRotator Blender model as one small GLB for the landing page.

Run it with Blender (it uses Blender's own Python):
  /Applications/Blender.app/Contents/MacOS/Blender -b "<path>/LapRotator.blend" --python tools/model.py
Writes assets/model/laprotator.glb.

The .blend holds the Onshape parts, one object per CAD face. Materials:
- Faces that still have their Onshape import material get the website look by part and face:
  white housings, chrome scope and buttons, grey "Pando" lettering, dark gears and end cap
  (see material_for). Gloss and reflections for these are set in js/model.js (LOOK).
- Faces you give your own material in Blender keep it: its Principled base color, metallic,
  roughness and coat are exported as they are.
Parts moved in Blender stay moved. Positions are stored as 16-bit and normals as 8-bit
(glTF KHR_mesh_quantization), which keeps the file near 1.5 MB with no visible loss.
The GLB uses the Onshape frame in meters, where the scope runs along +Z through x = 0, y = 0.
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/model/laprotator.glb"

# Base colors of the website looks; js/model.js sets gloss, clearcoat and reflections by these names
LOOKS = {
    "housing": [0.92, 0.93, 0.94],
    "chrome": [0.9, 0.9, 0.9],
    "dark": [0.025, 0.027, 0.03],
    "print": [0.3, 0.31, 0.33],
}

# Onshape gives every part its own import material, so the material tells which part a face belongs to
PART_BY_MATERIAL = {
    "0.647059_0.647059_0.647059_0.000000_0.000000": "Camera",
    "0.901961_0.901961_0.901961_0.000000_0.000000": "Battery Housing",
    "0.901961_0.901961_0.901961_0.000000_0.001": "Main Housing",
    "0.901961_0.901961_0.901961_0.000000_0.002": "Main Housing Cap",
    "0.917647_0.917647_0.917647_0.000000_0.000000": "Coupler",
    "0.917647_0.917647_0.917647_0.000000_0.001": "Scope",
    "0.917647_0.917647_0.917647_0.000000_0.002": "Scope Gear L",
    "0.917647_0.917647_0.917647_0.000000_0.003": "Scope Gear R",
}

# The scope turns inside the housing (that's what the device does). Turn it and its gears so the
# light post points the same way as in the product render (up, on the button side).
# The turn finds the scope by its Onshape material. If you give the scope your own material in
# Blender, turn it there instead and set this to 0.
SCOPE_TURN_DEG = 180
SCOPE_PARTS = ("Scope", "Scope Gear L", "Scope Gear R")


def material_for(part, lo, hi):
    """Pick a website look for one CAD face from its part name and bounding box (mm, Onshape frame)."""
    if part == "Scope":
        return "chrome"
    if part.startswith("Scope Gear"):
        return "dark"
    if part == "Camera":
        if -27 < lo[1] < -25.5 and hi[1] < -24.7:  # the three button domes, standing off the pad at y = -24.8
            return "chrome"
        # "Pando" is engraved 0.5 mm into the side at x = -21. Walls and floors are grey;
        # faces still on the surface (the insides of P, a, d, o) stay white.
        if lo[0] > -21.01 and -20.99 < hi[0] < -20.49 and hi[2] - lo[2] < 12:
            return "print"
        if hi[2] < -107:  # end cap
            return "dark"
    return "housing"


def turn_about_scope(v, deg):
    """Rotate points or normals (N x 3) about the scope axis (z, through x = 0, y = 0)."""
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.stack([c * v[:, 0] - s * v[:, 1], s * v[:, 0] + c * v[:, 1], v[:, 2]], axis=1)


def blender_material(mat):
    """glTF material from a material made in Blender (Principled BSDF values)."""
    out = {"name": mat.name, "pbrMetallicRoughness": {"baseColorFactor": [0.8, 0.8, 0.8, 1], "metallicFactor": 0, "roughnessFactor": 0.5}}
    node = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if mat.use_nodes else None
    if node is None:
        out["pbrMetallicRoughness"]["baseColorFactor"] = list(mat.diffuse_color)
        return out
    get = lambda k: node.inputs[k].default_value
    pbr = out["pbrMetallicRoughness"]
    pbr["baseColorFactor"] = [float(x) for x in get("Base Color")]
    pbr["metallicFactor"] = float(get("Metallic"))
    pbr["roughnessFactor"] = float(get("Roughness"))
    if float(get("Coat Weight")) > 0:
        out["extensions"] = {"KHR_materials_clearcoat": {"clearcoatFactor": float(get("Coat Weight")),
                                                         "clearcoatRoughnessFactor": float(get("Coat Roughness"))}}
    return out


def collect():
    """Return {(part, material key): [(positions, normals, indices), ...]} in Onshape meters."""
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]
    # The Onshape import put every face object under one shared transform; undo it
    common = Counter(tuple(round(v, 6) for row in o.matrix_world for v in row) for o in objs).most_common(1)[0][0]
    to_onshape = np.linalg.inv(np.array(common).reshape(4, 4))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    custom = {}
    groups = {}
    for o in objs:
        ev = o.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        mesh.calc_loop_triangles()
        nv, nl, nt = len(mesh.vertices), len(mesh.loops), len(mesh.loop_triangles)
        if not nt:
            ev.to_mesh_clear()
            continue
        co = np.empty(nv * 3); mesh.vertices.foreach_get("co", co)
        lv = np.empty(nl, np.int64); mesh.loops.foreach_get("vertex_index", lv)
        ln = np.empty(nl * 3); mesh.corner_normals.foreach_get("vector", ln)
        tl = np.empty(nt * 3, np.int64); mesh.loop_triangles.foreach_get("loops", tl)
        tm = np.empty(nt, np.int64); mesh.loop_triangles.foreach_get("material_index", tm)
        mats = [s.material for s in o.material_slots]
        ev.to_mesh_clear()

        m = to_onshape @ np.array(o.matrix_world)
        pos = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        nrm_m = np.linalg.inv(m[:3, :3]).T
        corner_n = ln.reshape(-1, 3) @ nrm_m.T
        corner_n /= np.maximum(np.linalg.norm(corner_n, axis=1, keepdims=True), 1e-12)

        for mi in np.unique(tm):
            mat = mats[mi] if mi < len(mats) else None
            loops = tl.reshape(-1, 3)[tm == mi].reshape(-1)
            p = pos[lv[loops]]
            lo, hi = p.min(0) * 1000, p.max(0) * 1000
            name = mat.name if mat else ""
            if name in PART_BY_MATERIAL or not mat:
                part = PART_BY_MATERIAL.get(name, "Housing")
                key = material_for(part, lo, hi)
            else:
                part = "Custom"
                key = name
                custom[name] = blender_material(mat)
            # One vertex per unique (position, corner normal)
            pairs = np.concatenate([lv[loops][:, None].astype(np.float64), np.round(corner_n[loops], 4)], axis=1)
            uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
            first = np.zeros(len(uniq), np.int64)
            first[inv.reshape(-1)] = np.arange(len(loops))
            vp = pos[lv[loops][first]]
            vn = corner_n[loops][first]
            if part in SCOPE_PARTS and SCOPE_TURN_DEG:
                vp, vn = turn_about_scope(vp, SCOPE_TURN_DEG), turn_about_scope(vn, SCOPE_TURN_DEG)
            groups.setdefault((part, key), []).append((vp, vn, inv.reshape(-1)))
    return groups, custom


def merge(chunks):
    pos, nrm, idx, base = [], [], [], 0
    for p, n, i in chunks:
        pos.append(p); nrm.append(n); idx.append(i + base); base += len(p)
    return np.concatenate(pos), np.concatenate(nrm), np.concatenate(idx)


def main():
    groups, custom = collect()
    if not groups:
        sys.exit("No meshes found in the .blend")
    parts = {}
    for (part, key), chunks in sorted(groups.items()):
        parts.setdefault(part, {})[key] = merge(chunks)

    # One shared quantization grid for every part: world = center + half * q
    allp = np.concatenate([g[0] for prims in parts.values() for g in prims.values()])
    lo, hi = allp.min(0), allp.max(0)
    center = (lo + hi) / 2
    half = float((hi - lo).max() / 2)

    mat_names = list(LOOKS) + sorted(custom)
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

    for name, prims_in in parts.items():
        prims = []
        for key, (pos, nrm, idx) in prims_in.items():
            # Split anything over 65535 vertices so indices stay 16-bit
            order = np.arange(len(idx) // 3)
            start = 0
            while start < len(order):
                tri = idx.reshape(-1, 3)[start:]
                used, cut = set(), len(tri)
                for t, row in enumerate(tri):
                    used.update(row.tolist())
                    if len(used) > 65535:
                        cut = t
                        break
                sub = tri[:cut]
                keep, local = np.unique(sub.reshape(-1), return_inverse=True)
                start += cut
                q = np.round((pos[keep] - center) / half * 32767).astype(np.int16)
                q4 = np.zeros((len(q), 4), np.int16); q4[:, :3] = q
                n4 = np.zeros((len(q), 4), np.int8); n4[:, :3] = np.round(nrm[keep] * 127).astype(np.int8)
                pv = add_view(q4.tobytes(), 8, 34962)
                accessors.append({"bufferView": pv, "componentType": 5122, "normalized": True, "count": len(q),
                                  "type": "VEC3", "min": q.min(0).tolist(), "max": q.max(0).tolist()})
                nv = add_view(n4.tobytes(), 4, 34962)
                accessors.append({"bufferView": nv, "componentType": 5120, "normalized": True, "count": len(q), "type": "VEC3"})
                iv = add_view(local.astype(np.uint16).tobytes(), target=34963)
                accessors.append({"bufferView": iv, "componentType": 5123, "count": len(local), "type": "SCALAR"})
                a = len(accessors)
                prims.append({"attributes": {"POSITION": a - 3, "NORMAL": a - 2}, "indices": a - 1, "material": mat_names.index(key)})
        meshes.append({"name": name, "primitives": prims})
        nodes.append({"name": name, "mesh": len(meshes) - 1})
        tris = sum(len(g[2]) for g in prims_in.values()) // 3
        print(f"{name:20s} {tris:6d} triangles  {', '.join(prims_in)}")

    nodes.append({"name": "LapRotator", "children": list(range(len(parts))),
                  "translation": center.tolist(), "scale": [half] * 3})
    while len(blob) % 4:
        blob.append(0)
    materials = [{"name": m, "pbrMetallicRoughness": {"baseColorFactor": LOOKS[m] + [1],
                  "metallicFactor": 1 if m == "chrome" else 0, "roughnessFactor": 0.3}} for m in LOOKS]
    materials += [custom[m] for m in sorted(custom)]
    used = ["KHR_mesh_quantization"] + (["KHR_materials_clearcoat"] if any("extensions" in m for m in materials) else [])
    gltf = {
        "asset": {"version": "2.0", "generator": "Pando tools/model.py (Blender)"},
        "extensionsUsed": used, "extensionsRequired": ["KHR_mesh_quantization"],
        "scene": 0, "scenes": [{"nodes": [len(nodes) - 1]}],
        "nodes": nodes, "meshes": meshes, "materials": materials,
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


main()
