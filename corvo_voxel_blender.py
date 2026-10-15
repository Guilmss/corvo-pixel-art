"""
Corvo Voxel 3D — gerador para Blender (2.93+ / 3.x / 4.x)
==========================================================
Como usar:
  1. Abra o Blender > aba "Scripting".
  2. Clique em "Open" e selecione este arquivo (ou cole o conteúdo).
  3. Clique em "Run Script" (Alt+P).

Gera dois objetos:
  - Corvo_Voxel  : o corvo (malha otimizada: só faces visíveis, um material por cor)
  - Galho_Voxel  : o galho/poleiro (opcional)

A lógica do voxel é idêntica ao visualizador index.html.
"""

import bpy
import bmesh
import math

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------
VOXEL_SIZE = 0.1          # tamanho de cada voxel em metros (corvo ~3 m -> ajuste à vontade)
INCLUDE_BRANCH = True     # gerar o galho
PALETTE_NAME = "classico" # "classico", "iridescente" ou "albino"
SETUP_SCENE = True        # cria câmera + luz e ativa Material Preview
EXPORT_GLB_PATH = ""      # ex.: r"C:\jogos\corvo_voxel.glb"  (vazio = não exporta)

BARK = {"BARK": "#5a3a21", "BARK2": "#7a5432", "BARK3": "#3a2414",
        "LEAF": "#6a9a3f", "LEAF2": "#3f6b2a"}
PALETTES = {
    "classico": {
        "K0": "#0b0b10", "K1": "#17171f", "K2": "#24273b", "K3": "#323d63", "K4": "#4a3672",
        "BEAK": "#2a2a31", "BEAK2": "#43434d", "EYE": "#d8cfb0", "PUPIL": "#020202",
        "LEG": "#3b3b44", "CLAW": "#141418", **BARK},
    "iridescente": {
        "K0": "#090b14", "K1": "#121a2e", "K2": "#1d2f57", "K3": "#2c6496", "K4": "#6a3fb0",
        "BEAK": "#22232b", "BEAK2": "#3b3d4a", "EYE": "#ffcf6b", "PUPIL": "#050505",
        "LEG": "#353845", "CLAW": "#121318", **BARK},
    "albino": {
        "K0": "#cfcac0", "K1": "#e6e2d9", "K2": "#f4f1ea", "K3": "#ffffff", "K4": "#eadfd0",
        "BEAK": "#e3b29e", "BEAK2": "#f0cbb9", "EYE": "#ff9a9a", "PUPIL": "#b81f36",
        "LEG": "#e0a595", "CLAW": "#c4877a", **BARK},
}

# ----------------------------------------------------------------------------
# GERADOR DE VOXELS  (X = largura, Y = cima, Z = frente; cabeça em +Z)
# ----------------------------------------------------------------------------
def rd(v):
    return math.floor(v + 0.5)


def rnd(x, y, z):
    return (((x + 50) * 92821 + (y + 50) * 68917 + (z + 50) * 31337) % 997) / 997


def generate_crow():
    vox = {}

    def put(x, y, z, c):
        vox[(x, y, z)] = c

    def feather(x, y, z):
        r = rnd(x, y, z)
        return "K0" if r < 0.35 else "K1" if r < 0.75 else "K2" if r < 0.93 else "K3"

    def ell(cx, cy, cz, rx, ry, rz, fn):
        for x in range(math.floor(cx - rx), math.ceil(cx + rx) + 1):
            for y in range(math.floor(cy - ry), math.ceil(cy + ry) + 1):
                for z in range(math.floor(cz - rz), math.ceil(cz + rz) + 1):
                    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                    if d <= 1:
                        put(x, y, z, fn(x, y, z))

    # Corpo
    def body_fn(x, y, z):
        if z > 1 and y < 9:
            return "K2" if (x + y + z) % 2 == 0 else "K1"
        if y >= 12:
            return "K3" if rnd(x, y, z) < 0.5 else "K2"
        return feather(x, y, z)
    ell(0, 9, 0, 4, 4, 6, body_fn)

    # Pescoço e cabeça
    def head_fn(x, y, z):
        if y >= 17:
            r = rnd(x, y, z)
            return "K3" if r < 0.5 else "K4" if r < 0.7 else "K2"
        return feather(x, y, z)
    ell(0, 12.5, 3.5, 3, 3, 3, head_fn)
    ell(0, 15, 5.5, 3.3, 3.3, 3.3, head_fn)

    # Penas da garganta + cerdas nasais
    for x in range(-1, 2):
        put(x, 12, 8, "K1")
        put(x, 11, 7, "K0" if x % 2 else "K1")
    put(0, 10, 7, "K0")
    put(0, 16, 9, "K1")

    # Bico curvado
    for x in range(-1, 2):
        put(x, 15, 9, "BEAK"); put(x, 14, 9, "BEAK"); put(x, 14, 10, "BEAK")
        put(x, 13, 9, "BEAK2")
    put(0, 15, 10, "BEAK")
    put(0, 15, 11, "BEAK"); put(0, 14, 11, "BEAK")
    put(0, 14, 12, "BEAK"); put(0, 13, 12, "BEAK")
    put(0, 13, 13, "BEAK"); put(0, 12, 13, "BEAK")   # gancho
    put(0, 13, 10, "BEAK2"); put(0, 13, 11, "BEAK2")

    # Olhos
    for s in (-1, 1):
        put(3 * s, 16, 6, "PUPIL")
        put(3 * s, 16, 5, "EYE")

    # Asas
    for s in (-1, 1):
        for z in range(4, -13, -1):
            for y in range(5, 15):
                t = (4 - z) / 14
                y_top, y_bot = rd(12.5 - 3 * t), rd(6.5 + 2 * t)
                if y < y_bot or y > y_top:
                    continue
                z_min = -9 - (y % 3)
                if z < z_min:
                    continue
                if z == 4 and (y == y_top or y == y_bot):
                    continue
                if z == z_min:
                    c = "K0"
                elif z <= -2:
                    c = "K1" if y % 2 == 0 else "K0"
                elif y >= y_top - 1:
                    c = "K3" if rnd(4 * s, y, z) < 0.5 else "K2"
                else:
                    c = feather(4 * s, y, z)
                put(4 * s, y, z, c)
                if y_bot < y < y_top and z_min + 1 < z < 3:
                    c2 = "K3" if (y + z) % 3 == 0 else ("K1" if z % 2 else "K2")
                    put(5 * s, y, z, c2)

    # Cauda em leque
    for z in range(-5, -16, -1):
        t = (-5 - z) / 10
        yc = rd(8 - 4 * t)
        w = 1 + rd(2 * t)
        for x in range(-w, w + 1):
            if z < -14 + (x % 2):
                continue
            c = "K2" if abs(x) == w else ("K1" if x % 2 else "K0")
            put(x, yc, z, c)
            if t < 0.5:
                put(x, yc + 1, z, "K1")

    # Pernas e pés
    for s in (-1, 1):
        x = 2 * s
        put(x, 5, 0, "K1"); put(x, 5, 1, "K1"); put(x, 4, 1, "K0")
        put(x, 3, 1, "LEG"); put(x, 2, 1, "LEG")
        put(x, 1, 1, "LEG"); put(x, 1, 2, "LEG"); put(x, 1, 3, "LEG"); put(x, 0, 3, "CLAW")
        put(x, 1, 0, "LEG"); put(x, 1, -1, "LEG"); put(x, 0, -1, "CLAW")
        put(x - s, 1, 2, "LEG"); put(x - s, 1, 3, "CLAW")

    # Galho
    for x in range(-11, 12):
        for y in range(-3, 1):
            for z in range(0, 4):
                if y in (-3, 0) and z in (0, 3):
                    continue
                if (x, y, z) in vox:
                    continue
                if abs(x) == 11:
                    c = "BARK2"
                elif x % 5 == 0:
                    c = "BARK3"
                else:
                    r = rnd(x, y, z)
                    c = "BARK3" if r < 0.2 else "BARK" if r < 0.6 else "BARK2"
                put(x, y, z, c)
    for p, c in [((8, 1, 1), "BARK"), ((9, 2, 1), "BARK"), ((9, 3, 1), "BARK2"), ((10, 4, 1), "BARK2"),
                 ((10, 5, 1), "LEAF"), ((11, 5, 1), "LEAF"), ((10, 6, 1), "LEAF2"), ((11, 5, 2), "LEAF2"),
                 ((10, 5, 0), "LEAF"), ((-9, 1, 2), "BARK2"), ((-10, 2, 2), "BARK2"),
                 ((-10, 3, 2), "LEAF"), ((-11, 3, 2), "LEAF2"), ((-10, 3, 3), "LEAF2")]:
        put(*p, c)

    return vox


# ----------------------------------------------------------------------------
# CONSTRUÇÃO DA MALHA
# ----------------------------------------------------------------------------
FACES = [
    ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 1, 1), (0, 0, 1)]),
    ((1, 0, 0),  [(1, 1, 1), (1, 0, 1), (1, 1, 0), (1, 0, 0)]),
    ((0, -1, 0), [(1, 0, 1), (0, 0, 1), (1, 0, 0), (0, 0, 0)]),
    ((0, 1, 0),  [(0, 1, 1), (1, 1, 1), (0, 1, 0), (1, 1, 0)]),
    ((0, 0, -1), [(1, 0, 0), (0, 0, 0), (1, 1, 0), (0, 1, 0)]),
    ((0, 0, 1),  [(0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]),
]


def hex_to_linear(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def get_material(color_key, palette):
    name = f"Voxel_{PALETTE_NAME}_{color_key}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    rgba = hex_to_linear(palette[color_key])
    mat.diffuse_color = rgba
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        glossy = color_key in ("K3", "K4", "PUPIL", "BEAK")
        bsdf.inputs["Roughness"].default_value = 0.35 if glossy else 0.6
        bsdf.inputs["Metallic"].default_value = 0.15 if color_key in ("K3", "K4") else 0.0
    return mat


def build_object(name, voxels, palette):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    keys = sorted(set(voxels.values()))
    mat_index = {k: i for i, k in enumerate(keys)}

    verts, faces, face_mats, vmap = [], [], [], {}

    def vid(p):
        if p not in vmap:
            vmap[p] = len(verts)
            # Three.js (x, y, z) -> Blender (x, -z, y): Z para cima, cabeça olhando para -Y (vista frontal)
            verts.append((p[0] * VOXEL_SIZE, -p[2] * VOXEL_SIZE, p[1] * VOXEL_SIZE))
        return vmap[p]

    for (x, y, z), c in voxels.items():
        for (dx, dy, dz), corners in FACES:
            if (x + dx, y + dy, z + dz) in voxels:
                continue
            q = [vid((x + cx - 0.5, y + cy - 0.5, z + cz - 0.5)) for cx, cy, cz in corners]
            faces.append((q[0], q[1], q[3], q[2]))
            face_mats.append(mat_index[c])

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for k in keys:
        mesh.materials.append(get_material(k, palette))
    for poly, mi in zip(mesh.polygons, face_mats):
        poly.material_index = mi
        poly.use_smooth = False

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def setup_scene(target):
    cam = bpy.data.objects.get("Corvo_Camera")
    if cam is None:
        cam = bpy.data.objects.new("Corvo_Camera", bpy.data.cameras.new("Corvo_Camera"))
        bpy.context.collection.objects.link(cam)
    s = VOXEL_SIZE
    cam.location = (38 * s, -40 * s, 22 * s)
    con = cam.constraints.get("Track") or cam.constraints.new("TRACK_TO")
    con.name = "Track"
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    bpy.context.scene.camera = cam

    sun = bpy.data.objects.get("Corvo_Sol")
    if sun is None:
        sun = bpy.data.objects.new("Corvo_Sol", bpy.data.lights.new("Corvo_Sol", "SUN"))
        bpy.context.collection.objects.link(sun)
    sun.data.energy = 4.0
    sun.data.color = (1.0, 0.9, 0.78)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

    try:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"
    except Exception:
        pass


def main():
    palette = PALETTES[PALETTE_NAME]
    vox = generate_crow()
    branch_keys = {"BARK", "BARK2", "BARK3", "LEAF", "LEAF2"}
    crow = {p: c for p, c in vox.items() if c not in branch_keys}
    branch = {p: c for p, c in vox.items() if c in branch_keys}

    crow_obj = build_object("Corvo_Voxel", crow, palette)
    objs = [crow_obj]
    if INCLUDE_BRANCH:
        objs.append(build_object("Galho_Voxel", branch, palette))

    if SETUP_SCENE:
        setup_scene(crow_obj)

    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = crow_obj

    if EXPORT_GLB_PATH:
        bpy.ops.export_scene.gltf(filepath=EXPORT_GLB_PATH, export_format="GLB", use_selection=True)

    print(f"[Corvo Voxel] {len(crow)} voxels no corvo, {len(branch)} no galho.")


main()
