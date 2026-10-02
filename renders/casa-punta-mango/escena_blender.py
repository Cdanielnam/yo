# Casa Punta Mango - procedural Blender (bpy) scene built from plans A-1/A-2/A-3
# Usage: python3 scene.py <view> <quality> [outfile]
#   view: hero | aerial | dusk | street | pool
#   quality: preview | final | ultra
import sys, math, random
import bpy
from mathutils import Vector, Euler

VIEW = sys.argv[1] if len(sys.argv) > 1 else "hero"
QUALITY = sys.argv[2] if len(sys.argv) > 2 else "preview"
OUT = sys.argv[3] if len(sys.argv) > 3 else f"/tmp/claude-0/-home-user-yo/672b3b8a-8a38-59da-af9e-11608921219c/scratchpad/render/{VIEW}_{QUALITY}.png"
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
COL = scene.collection

# ------------------------------------------------------------------ helpers
def link(obj):
    COL.objects.link(obj)
    return obj

def mesh_obj(name, verts, faces, mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    return link(ob)

def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return mesh_obj(name, v, f, mat)

def plane(name, x0, x1, y0, y1, z, mat):
    v = [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    return mesh_obj(name, v, [(0,1,2,3)], mat)

import bmesh
_MESH_CACHE = {}
def _cached_mesh(kind, key, mat, builder):
    k = (kind, key, mat.name)
    if k not in _MESH_CACHE:
        bm = bmesh.new()
        builder(bm)
        me = bpy.data.meshes.new(f"{kind}_{key}_{mat.name}")
        bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        me.materials.append(mat)
        _MESH_CACHE[k] = me
    return _MESH_CACHE[k]

def cyl(name, x, y, z0, z1, r, mat, segs=24):
    me = _cached_mesh('cyl', segs, mat, lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=1.0, radius2=1.0, depth=1.0))
    ob = bpy.data.objects.new(name, me)
    ob.location = (x, y, (z0+z1)/2); ob.scale = (r, r, z1-z0)
    return link(ob)

def sphere(name, x, y, z, r, mat, subdiv=3):
    me = _cached_mesh('ico', subdiv, mat, lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0))
    ob = bpy.data.objects.new(name, me)
    ob.location = (x, y, z); ob.scale = (r, r, r)
    return link(ob)

def bevel(ob, width=0.1, segs=3):
    m = ob.modifiers.new('bevel', 'BEVEL')
    m.width = width; m.segments = segs; m.limit_method = 'ANGLE'
    return ob

# ------------------------------------------------------------------ materials
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    out = nt.nodes['Material Output']
    return m, nt, bsdf, out

def tex_coord(nt, scale=1.0):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs['Vector']

def noise(nt, vec, scale=5, detail=4, rough=0.5, dist=0.0):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = dist
    nt.links.new(vec, n.inputs['Vector'])
    return n

def bump(nt, bsdf, height_out, strength=0.2, distance=0.1):
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = distance
    nt.links.new(height_out, b.inputs['Height'])
    nt.links.new(b.outputs['Normal'], bsdf.inputs['Normal'])
    return b

def mixrgb(nt, fac, a, b):
    mx = nt.nodes.new('ShaderNodeMix')
    mx.data_type = 'RGBA'
    if isinstance(fac, (int, float)):
        mx.inputs[0].default_value = fac
    else:
        nt.links.new(fac, mx.inputs[0])
    for idx, c in ((6, a), (7, b)):
        if isinstance(c, tuple):
            mx.inputs[idx].default_value = c
        else:
            nt.links.new(c, mx.inputs[idx])
    return mx.outputs[2]

def ramp(nt, fac, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    cr = r.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = stops[0][1]
    for pos, col in stops[1:]:
        e = cr.elements.new(pos); e.color = col
    nt.links.new(fac, r.inputs['Fac'])
    return r

def m_stucco(name="stucco", col=(0.92, 0.89, 0.83, 1)):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=40, detail=6, rough=0.6)
    n2 = noise(nt, vec, scale=1.5, detail=2)
    b.inputs['Base Color'].default_value = col
    r = ramp(nt, n2.outputs['Fac'], [(0.3, (col[0]*0.93, col[1]*0.93, col[2]*0.93, 1)), (0.7, col)])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    bump(nt, b, n.outputs['Fac'], 0.12, 0.05)
    return m

def m_concrete(name="concrete", col=(0.58, 0.57, 0.55, 1)):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=3, detail=6, rough=0.65)
    n2 = noise(nt, vec, scale=60, detail=4)
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 6
    nt.links.new(vec, vor.inputs['Vector'])
    dark = (col[0]*0.8, col[1]*0.8, col[2]*0.8, 1)
    r = ramp(nt, n.outputs['Fac'], [(0.35, dark), (0.65, col)])
    vr = ramp(nt, vor.outputs['Distance'], [(0.0, (col[0]*0.88, col[1]*0.88, col[2]*0.88, 1)), (1.0, (col[0]*1.06, col[1]*1.06, col[2]*1.06, 1))])
    c2 = mixrgb(nt, 0.3, r.outputs['Color'], vr.outputs['Color'])
    nt.links.new(c2, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.65
    bump(nt, b, n2.outputs['Fac'], 0.08, 0.02)
    return m

def m_travertine(name="travertine"):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.006
    br.inputs['Brick Width'].default_value = 0.6
    br.inputs['Row Height'].default_value = 0.6
    br.inputs['Color1'].default_value = (0.80, 0.74, 0.62, 1)
    br.inputs['Color2'].default_value = (0.74, 0.68, 0.56, 1)
    br.inputs['Mortar'].default_value = (0.45, 0.42, 0.37, 1)
    br.offset = 0.5
    nt.links.new(vec, br.inputs['Vector'])
    n = noise(nt, vec, scale=8, detail=6, rough=0.7)
    veins = ramp(nt, n.outputs['Fac'], [(0.4, (0.70, 0.64, 0.52, 1)), (0.6, (0.86, 0.80, 0.68, 1))])
    c = mixrgb(nt, br.outputs['Fac'], veins.outputs['Color'], br.outputs['Color'])
    nt.links.new(c, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.5
    n2 = noise(nt, vec, scale=50, detail=5)
    mixh = mixrgb(nt, 0.5, n2.outputs['Color'], br.outputs['Fac'])
    bump(nt, b, br.outputs['Fac'], 0.3, 0.01)
    return m

def m_wood(name="teak", col=(0.46, 0.27, 0.13, 1), plank=None, dirx='X'):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'; w.bands_direction = dirx
    w.inputs['Scale'].default_value = 3.0
    w.inputs['Distortion'].default_value = 6.0
    w.inputs['Detail'].default_value = 3.0
    w.inputs['Detail Scale'].default_value = 4.0
    nt.links.new(vec, w.inputs['Vector'])
    dark = (col[0]*0.55, col[1]*0.55, col[2]*0.55, 1)
    r = ramp(nt, w.outputs['Fac'], [(0.2, dark), (0.8, col)])
    colout = r.outputs['Color']
    if plank:
        br = nt.nodes.new('ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Mortar Size'].default_value = 0.004
        br.inputs['Brick Width'].default_value = plank[0]
        br.inputs['Row Height'].default_value = plank[1]
        br.inputs['Color1'].default_value = (1, 1, 1, 1)
        br.inputs['Color2'].default_value = (0.8, 0.8, 0.8, 1)
        br.inputs['Mortar'].default_value = (0.1, 0.1, 0.1, 1)
        br.offset = 0.33
        nt.links.new(vec, br.inputs['Vector'])
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
        mul.inputs[0].default_value = 1.0
        nt.links.new(colout, mul.inputs[6]); nt.links.new(br.outputs['Color'], mul.inputs[7])
        colout = mul.outputs[2]
        bump(nt, b, br.outputs['Fac'], 0.4, 0.01)
    else:
        bump(nt, b, w.outputs['Fac'], 0.1, 0.01)
    nt.links.new(colout, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.45
    b.inputs['Coat Weight'].default_value = 0.2
    return m

def m_glass(name="glass", tint=(0.86, 0.93, 0.95, 1)):
    m, nt, b, o = new_mat(name)
    nt.nodes.remove(b)
    glass = nt.nodes.new('ShaderNodeBsdfGlass')
    glass.inputs['Color'].default_value = tint
    glass.inputs['Roughness'].default_value = 0.0
    glass.inputs['IOR'].default_value = 1.45
    trans = nt.nodes.new('ShaderNodeBsdfTransparent')
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Shadow Ray'], mix.inputs[0])
    nt.links.new(glass.outputs[0], mix.inputs[1])
    nt.links.new(trans.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs['Surface'])
    return m

def m_water(name="water", col=(0.55, 0.85, 0.9, 1), absorb=(0.25, 0.7, 0.95, 1), dens=0.3, wave=12.0):
    m, nt, b, o = new_mat(name)
    b.inputs['Base Color'].default_value = (1, 1, 1, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.02
    b.inputs['IOR'].default_value = 1.333
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=wave, detail=5, rough=0.55, dist=0.4)
    bump(nt, b, n.outputs['Fac'], 0.15, 0.03)
    va = nt.nodes.new('ShaderNodeVolumeAbsorption')
    va.inputs['Color'].default_value = absorb
    va.inputs['Density'].default_value = dens
    nt.links.new(va.outputs[0], o.inputs['Volume'])
    # let shadow rays pass so the pool floor receives direct sun (caustics are off)
    trans = nt.nodes.new('ShaderNodeBsdfTransparent')
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Shadow Ray'], mix.inputs[0])
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(trans.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs['Surface'])
    return m

def m_sea(name="sea"):
    m, nt, b, o = new_mat(name)
    b.inputs['Roughness'].default_value = 0.06
    b.inputs['Specular IOR Level'].default_value = 0.6
    b.inputs['Coat Weight'].default_value = 0.6
    vec = tex_coord(nt, 1.0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(vec, sep.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -8.0; mr.inputs['From Max'].default_value = -70.0
    nt.links.new(sep.outputs['X'], mr.inputs['Value'])
    depth = ramp(nt, mr.outputs['Result'], [(0.0, (0.25, 0.55, 0.55, 1)), (0.35, (0.05, 0.28, 0.32, 1)), (1.0, (0.02, 0.10, 0.14, 1))])
    nt.links.new(depth.outputs['Color'], b.inputs['Base Color'])
    n = noise(nt, vec, scale=0.35, detail=8, rough=0.6, dist=0.6)
    n2 = noise(nt, vec, scale=6, detail=4, rough=0.5)
    mx = mixrgb(nt, 0.35, n.outputs['Color'], n2.outputs['Color'])
    bump(nt, b, mx, 0.6, 0.3)
    return m

def m_foam(name="foam"):
    m, nt, b, o = new_mat(name)
    b.inputs['Base Color'].default_value = (0.95, 0.97, 0.97, 1)
    b.inputs['Roughness'].default_value = 0.9
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=0.6, detail=8, rough=0.7, dist=1.0)
    r = ramp(nt, n.outputs['Fac'], [(0.42, (0, 0, 0, 1)), (0.6, (1, 1, 1, 1))])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(r.outputs['Color'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs['Surface'])
    m.blend_method = 'HASHED'
    return m

def m_sand(name="sand"):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=0.6, detail=5, rough=0.6)
    n2 = noise(nt, vec, scale=120, detail=3)
    r = ramp(nt, n.outputs['Fac'], [(0.3, (0.22, 0.19, 0.16, 1)), (0.7, (0.36, 0.31, 0.26, 1))])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95
    bump(nt, b, n2.outputs['Fac'], 0.25, 0.02)
    return m

def m_wetsand(name="wetsand"):
    m, nt, b, o = new_mat(name)
    b.inputs['Base Color'].default_value = (0.15, 0.13, 0.11, 1)
    b.inputs['Roughness'].default_value = 0.35
    b.inputs['Coat Weight'].default_value = 0.5
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=2, detail=5)
    bump(nt, b, n.outputs['Fac'], 0.1, 0.02)
    return m

def m_grass(name="grassground"):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=1.2, detail=6, rough=0.6)
    r = ramp(nt, n.outputs['Fac'], [(0.3, (0.08, 0.16, 0.04, 1)), (0.7, (0.18, 0.30, 0.07, 1))])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    n2 = noise(nt, vec, scale=80, detail=4)
    bump(nt, b, n2.outputs['Fac'], 0.3, 0.02)
    return m

def m_dry(name="dryground"):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=0.05, detail=7, rough=0.7)
    n2 = noise(nt, vec, scale=2.0, detail=4)
    r = ramp(nt, n.outputs['Fac'], [(0.3, (0.36, 0.30, 0.20, 1)), (0.45, (0.28, 0.30, 0.12, 1)), (0.6, (0.13, 0.26, 0.06, 1))])
    c = mixrgb(nt, 0.25, r.outputs['Color'], n2.outputs['Color'])
    nt.links.new(c, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95
    n3 = noise(nt, vec, scale=40, detail=4)
    bump(nt, b, n3.outputs['Fac'], 0.3, 0.03)
    return m

def m_hair(name="grasshair"):
    m, nt, b, o = new_mat(name)
    b.inputs['Base Color'].default_value = (0.08, 0.20, 0.04, 1)
    b.inputs['Roughness'].default_value = 0.7
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 3
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    r = ramp(nt, n.outputs['Fac'], [(0.3, (0.06, 0.16, 0.03, 1)), (0.7, (0.18, 0.32, 0.07, 1))])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    return m

def m_leaf(name="leaf", col=(0.08, 0.24, 0.06, 1)):
    m, nt, b, o = new_mat(name)
    b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Specular IOR Level'].default_value = 0.4
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = (col[0]*2.2, col[1]*1.8, col[2]*1.2, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.3
    nt.links.new(b.outputs[0], mix.inputs[1]); nt.links.new(tl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs['Surface'])
    vec = tex_coord(nt, 1.0)
    n = noise(nt, vec, scale=4, detail=3)
    r = ramp(nt, n.outputs['Fac'], [(0.3, (col[0]*0.7, col[1]*0.7, col[2]*0.7, 1)), (0.7, (col[0]*1.3, col[1]*1.25, col[2]*1.1, 1))])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    return m

def m_trunk(name="trunk"):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    w = nt.nodes.new('ShaderNodeTexWave'); w.bands_direction = 'Z'
    w.inputs['Scale'].default_value = 6; w.inputs['Distortion'].default_value = 1.5
    nt.links.new(vec, w.inputs['Vector'])
    n = noise(nt, vec, scale=15, detail=5)
    r = ramp(nt, n.outputs['Fac'], [(0.3, (0.30, 0.25, 0.19, 1)), (0.7, (0.48, 0.42, 0.34, 1))])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    mx = mixrgb(nt, 0.5, w.outputs['Fac'], n.outputs['Fac'])
    bump(nt, b, mx, 0.5, 0.03)
    return m

def m_simple(name, col, rough=0.5, metal=0.0, coat=0.0):
    m, nt, b, o = new_mat(name)
    b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    return m

def m_emit(name, col, strength):
    m, nt, b, o = new_mat(name)
    nt.nodes.remove(b)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = col; e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs['Surface'])
    return m

def m_tile(name="pooltile"):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 0.1
    br.inputs['Row Height'].default_value = 0.1
    br.inputs['Color1'].default_value = (0.60, 0.84, 0.95, 1)
    br.inputs['Color2'].default_value = (0.50, 0.78, 0.92, 1)
    br.inputs['Mortar'].default_value = (0.7, 0.8, 0.8, 1)
    br.offset = 0.0
    nt.links.new(vec, br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.25
    bump(nt, b, br.outputs['Fac'], 0.2, 0.005)
    return m

MAT = dict(
    stucco=m_stucco(), stucco_w=m_stucco("stucco_warm", (0.93, 0.88, 0.78, 1)),
    concrete=m_concrete(), concrete_d=m_concrete("concrete_dark", (0.42, 0.41, 0.39, 1)),
    trav=m_travertine(), teak=m_wood(), teak_v=m_wood("teak_v", dirx='Z'),
    deck=m_wood("deck", (0.40, 0.25, 0.13, 1), plank=(0.14, 2.4), dirx='X'),
    glass=m_glass(), glass_rail=m_glass("glass_rail", (0.9, 0.96, 0.95, 1)),
    water=m_water(), sea=m_sea(), sand=m_sand(), wetsand=m_wetsand(), grass=m_grass(), hair=m_hair(), dry=m_dry(), foam=m_foam(),
    leaf=m_leaf("leaf", (0.06, 0.17, 0.05, 1)), palmleaf=m_leaf("palmleaf", (0.10, 0.28, 0.07, 1)), bush=m_leaf("bush", (0.07, 0.19, 0.05, 1)),
    trunk=m_trunk(), tile=m_tile(),
    white=m_simple("white", (0.9, 0.9, 0.88, 1), 0.6), offwhite=m_simple("offwhite", (0.88, 0.86, 0.8, 1), 0.7),
    fabric=m_simple("fabric", (0.85, 0.83, 0.78, 1), 0.9),
    black=m_simple("blackmetal", (0.03, 0.03, 0.03, 1), 0.4, 0.8),
    steel=m_simple("steel", (0.6, 0.6, 0.6, 1), 0.3, 1.0),
    floor=m_simple("floor_int", (0.78, 0.76, 0.72, 1), 0.3, 0.0, 0.3),
    floor2=m_simple("floor_up", (0.75, 0.72, 0.66, 1), 0.4),
    sofa=m_simple("sofa", (0.72, 0.68, 0.6, 1), 0.9), darkwood=m_wood("darkwood", (0.25, 0.14, 0.07, 1)),
    road=m_sand("road"), carpaint=m_simple("carpaint", (0.12, 0.12, 0.13, 1), 0.3, 0.6, 0.8),
    carpaint2=m_simple("carpaint2", (0.75, 0.75, 0.78, 1), 0.3, 0.7, 0.8),
    tire=m_simple("tire", (0.02, 0.02, 0.02, 1), 0.8), lamp=m_emit("lamp", (1.0, 0.75, 0.45, 1), 40),
    lampcool=m_emit("lampcool", (1.0, 0.85, 0.6, 1), 12), terracotta=m_simple("terracotta", (0.5, 0.3, 0.2, 1), 0.8),
    cushion=m_simple("cushion", (0.93, 0.92, 0.88, 1), 0.9), poolcope=m_simple("coping", (0.85, 0.80, 0.70, 1), 0.6),
)
MAT['road'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.45, 0.4, 0.33, 1)

# ------------------------------------------------------------------ site geometry
# X: 0 = sea-side lot line, 80 = street.  Y: 0..18 lot width. Z up. Pool deck Z=0, house FFL Z=0.45
FFL = 0.45
H1 = 3.4   # floor-to-floor
Z2 = FFL + H1          # second floor FFL = 3.85
ROOF = Z2 + 3.1        # roof slab bottom 6.95
RT = ROOF + 0.35       # roof top

# Terrain: big sand/ground base, beach slope, sea
# Ground outside lot and inside beach zone
def terrain():
    # sea plane (large)
    sea = plane("sea", -3000, -8.0, -3000, 3000, -1.45, MAT['sea'])
    # beach slope: X -12..20 sloping from Z -1.6 to 0
    verts, faces = [], []
    nx, ny = 40, 30
    for i in range(nx+1):
        x = -14 + (34.0*i/nx)      # -14 .. 20
        for j in range(ny+1):
            y = -600 + (1200.0*j/ny)
            t = max(0.0, min(1.0, (x+8)/28.0))
            z = -1.6 + 1.6*(t**1.3) + 0.03*math.sin(x*1.3)*math.cos(y*0.7)
            if x < -8: z = -1.7
            verts.append((x, y, z))
    for i in range(nx):
        for j in range(ny):
            a = i*(ny+1)+j
            faces.append((a, a+ny+1, a+ny+2, a+1))
    beach = mesh_obj("beach", verts, faces, MAT['sand'], smooth=True)
    # wet sand strip near water
    plane("wetsand", -9.5, -5.5, -600, 600, -1.42, MAT['wetsand'])
    plane("foam1", -12.5, -7.5, -600, 600, -1.43, MAT['foam'])
    plane("foam2", -24, -18, -600, 600, -1.44, MAT['foam'])
    # ground for lot + neighbors
    plane("ground_s", 20, 1500, -1500, -0.3, -0.02, MAT['dry'])
    plane("ground_n", 20, 1500, 18.3, 1500, -0.02, MAT['dry'])
    plane("ground_e", 80.2, 1500, -0.3, 18.3, -0.02, MAT['dry'])
    plane("ground_lot", 20, 80.2, -0.3, 18.3, -1.9, MAT['sand'])
    # road behind lot
    plane("road", 80.5, 88, -600, 600, 0.0, MAT['road'])

terrain()

# ------------------------------------------------------------------ perimeter & grounds
def lawn(name, x0, x1, y0, y1, z=0.0, hair=True):
    ob = plane(name, x0, x1, y0, y1, z, MAT['grass'])
    if hair and QUALITY != 'preview_nohair':
        # subdivide for even particle distribution
        m = ob.modifiers.new('sub', 'SUBSURF'); m.subdivision_type = 'SIMPLE'; m.levels = 3; m.render_levels = 3
        psm = ob.modifiers.new('grass', 'PARTICLE_SYSTEM')
        ps = ob.particle_systems[0].settings
        area = (x1-x0)*(y1-y0)
        ps.type = 'HAIR'
        ps.count = int(area * 120)
        ps.hair_length = 0.05
        ps.length_random = 0.4
        ps.use_advanced_hair = True
        ps.child_type = 'INTERPOLATED'
        ps.child_percent = 2
        ps.rendered_child_count = 8
        ps.clump_factor = 0.3
        ps.roughness_1 = 0.03
        ps.roughness_endpoint = 0.03
        ps.root_radius = 0.9
        ps.tip_radius = 0.05
        ps.radius_scale = 0.012
        ps.brownian_factor = 0.0
        ps.hair_step = 3
        ps.factor_random = 0.5
        ps.use_hair_bspline = True
        ps.material_slot = 'grassground'
        ob.data.materials.append(MAT['hair'])
        ps.material = 2
    return ob

# lot lawn zones (inside lot, Z slightly above ground)
lawn("lawn_beachfront", 20.1, 27.0, 0.1, 17.9, 0.0)
lawn("lawn_side_l", 27.0, 36.0, 0.1, 1.9, 0.0)
lawn("lawn_side_r", 27.0, 36.0, 16.1, 17.9, 0.0)
lawn("lawn_back_l", 52.0, 74.0, 0.1, 6.0, 0.0)
lawn("lawn_back_r", 52.0, 79.5, 12.5, 17.9, 0.0)

# perimeter walls (stucco, 2.2 m) along Y=0 and Y=18 from X=20..80, and back wall with gate
box("wall_s", 20, 80, -0.25, 0.0, -0.1, 2.2, MAT['stucco'])
box("wall_n", 20, 80, 18.0, 18.25, -0.1, 2.2, MAT['stucco'])
box("wall_back_a", 79.6, 80.0, 0, 6.0, -0.1, 2.4, MAT['stucco'])
box("wall_back_b", 79.6, 80.0, 12.5, 18.0, -0.1, 2.4, MAT['stucco'])
# sea wall at beachfront edge (retaining)
box("seawall", 19.6, 20.1, -0.3, 18.3, -0.9, 0.08, MAT['concrete'])
# steps down to beach at Y 16.5..18
for i in range(4):
    box(f"beachstep{i}", 19.6-0.35*(i+1), 19.6-0.35*i, 15.6, 17.9, -0.9, 0.05-0.22*(i+1), MAT['concrete'])

# ------------------------------------------------------------------ beachfront deck
box("deck", 22.0, 26.4, 0.4, 7.0, -0.05, 0.08, MAT['deck'])
def lounger(name, x, y, rot=0.0, mat_frame=None, mat_fab=None):
    mat_frame = mat_frame or MAT['teak']; mat_fab = mat_fab or MAT['fabric']
    parts = []
    parts.append(box(name+"_f", -1.0, 1.0, -0.36, 0.36, 0.28, 0.34, mat_frame))
    parts.append(box(name+"_c", -0.98, 0.45, -0.33, 0.33, 0.34, 0.42, mat_fab))
    for lx in (-0.9, 0.9):
        for ly in (-0.3, 0.3):
            parts.append(box(name+f"_l{lx}{ly}", lx-0.03, lx+0.03, ly-0.03, ly+0.03, 0.0, 0.28, mat_frame))
    back = box(name+"_b", 0.45, 1.05, -0.33, 0.33, 0.34, 0.42, mat_fab)
    back.location = (0, 0, 0)
    back.rotation_euler = (0, -0.9, 0)
    # rotate back around hinge at x=0.45,z=0.34 : move pivot
    back.data.transform(__import__('mathutils').Matrix.Translation((-0.45, 0, -0.34)))
    back.location = (0.45, 0, 0.34)
    parts.append(back)
    for p in parts:
        p.rotation_euler = (p.rotation_euler[0], p.rotation_euler[1], rot)
        # rotate location around origin then translate
        lx, ly, lz = p.location
        c, s = math.cos(rot), math.sin(rot)
        p.location = (x + lx*c - ly*s, y + lx*s + ly*c, lz)
    return parts
def place_z(parts, z):
    for p in parts: p.location = (p.location[0], p.location[1], p.location[2] + z)

place_z(lounger("bl1", 24.2, 2.2, rot=math.pi), 0.08)
place_z(lounger("bl2", 24.2, 4.2, rot=math.pi), 0.08)
# umbrella
cyl("umb_pole", 23.2, 3.2, 0.08, 2.6, 0.025, MAT['steel'])
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=1.5, radius2=0.0, depth=0.4, location=(23.2, 3.2, 2.5))
umb = bpy.context.active_object; umb.name = "umb_top"; umb.data.materials.append(MAT['offwhite'])

# ------------------------------------------------------------------ pool & deck (Z=0)
PX0, PX1, PY0, PY1 = 27.0, 33.6, 1.9, 12.9
# pool deck paving around the pool from X 27..36 (travertine), Y 0.1..17.9 minus pool
box("pdeck_a", 26.5, 36.0, 12.9, 16.1, -0.05, 0.0, MAT['trav'])
box("pdeck_b", 26.5, 26.9, 1.9, 12.9, -0.05, 0.0, MAT['trav'])
box("pdeck_c", 33.7, 36.0, 1.9, 12.9, -0.05, 0.0, MAT['trav'])
box("pdeck_d", 26.5, 36.0, 1.9, 1.9, -0.05, 0.0, MAT['trav']) if False else None
# coping lip
for nm, a in (("cop_s", (PX0-0.35, PX1+0.35, PY0-0.35, PY0)), ("cop_n", (PX0-0.35, PX1+0.35, PY1, PY1+0.35)),
              ("cop_w", (PX0-0.35, PX0, PY0, PY1)), ("cop_e", (PX1, PX1+0.35, PY0, PY1))):
    box(nm, *a, -0.012, 0.03, MAT['poolcope'])
# basin
box("pool_floor", PX0, PX1, PY0, PY1, -1.65, -1.55, MAT['tile'])
box("pool_wall_w", PX0-0.1, PX0, PY0, PY1, -1.6, -0.02, MAT['tile'])
box("pool_wall_e", PX1, PX1+0.1, PY0, PY1, -1.6, -0.02, MAT['tile'])
box("pool_wall_s", PX0, PX1, PY0-0.1, PY0, -1.6, -0.02, MAT['tile'])
box("pool_wall_n", PX0, PX1, PY1, PY1+0.1, -1.6, -0.02, MAT['tile'])
# sunken lounge / steps at east end (toward house) Y 7..11
box("pool_lounge", 31.6, 33.6, 7.0, 11.0, -1.55, -0.45, MAT['tile'])
box("pool_step1", 32.3, 33.6, 7.0, 11.0, -0.45, -0.30, MAT['tile'])
box("pool_step2", 33.0, 33.6, 7.0, 11.0, -0.30, -0.15, MAT['tile'])
box("pool_step_entry", PX0, PX0+0.6, PY1-2.5, PY1, -0.4, -0.15, MAT['tile'])
# water
box("pool_water", PX0+0.005, PX1-0.005, PY0+0.005, PY1-0.005, -1.5, -0.12, MAT['water'])
# pool loungers on terrace east of pool
for i, y in enumerate((8.3, 10.0, 11.7)):
    place_z(lounger(f"pl{i}", 34.8, y, rot=math.pi), 0.0)
# pool service block (bar / bath) at X 28..33, Y 14..17.5
box("svc", 28.0, 33.0, 14.0, 17.5, -0.06, 2.8, MAT['stucco_w'])
box("svc_roof", 27.6, 33.4, 13.6, 17.9, 2.8, 3.05, MAT['concrete'])
for i in range(14):
    x = 27.7 + i*0.42
    box(f"svc_slat{i}", x, x+0.08, 13.6, 17.9, 3.05, 3.25, MAT['teak'])
box("svc_counter", 28.0, 33.0, 13.3, 14.0, -0.05, 1.05, MAT['concrete_d'])
box("svc_countertop", 27.9, 33.1, 13.2, 14.05, 1.05, 1.1, MAT['white'])
box("svc_door", 30.0, 30.9, 13.98, 14.02, 0.0, 2.2, MAT['teak_v'])
for i in range(3):
    cyl(f"stool{i}", 28.8 + i*1.3, 12.8, 0.0, 0.72, 0.17, MAT['teak'])

# ------------------------------------------------------------------ terrace plinth (FFL 0.45) & steps
box("terrace", 36.0, 43.4, 0.1, 17.9, -0.055, FFL, MAT['trav'])
for i in range(3):
    box(f"tstep{i}", 36.0-0.38*(i+1), 36.0-0.38*i, 3.5, 14.5, -0.05, FFL-0.15*(i+1), MAT['trav'])
# concrete blade walls (fins) framing the terrace, support balcony slab
box("fin_l", 38.7, 40.3, 5.5, 5.8, FFL-0.03, Z2-0.05, MAT['concrete'])
box("fin_r", 38.7, 40.3, 13.1, 13.4, FFL-0.03, Z2-0.05, MAT['concrete'])
# planter strips along terrace sides (Y 1.9..2.6 and 15.4..16.1) with bushes
box("planter_l", 36.0, 43.2, 1.9, 2.7, FFL-0.03, FFL+0.45, MAT['concrete_d'])
box("planter_r", 36.0, 43.2, 15.3, 16.1, FFL-0.03, FFL+0.45, MAT['concrete_d'])

# ------------------------------------------------------------------ house
HX0, HX1, HY0, HY1 = 43.2, 52.0, 0.1, 17.9
WT = 0.25
# ground floor slab is terrace box. Interior floor
box("floor1", HX0+0.1, HX1-0.1, HY0+0.1, HY1-0.1, FFL-0.02, FFL+0.012, MAT['floor'])
# bedroom wings ground floor (Y 0.1..5.5 and 13.4..17.9) stucco volumes; central zone glass
# back wall full width (street side)
box("w_back", HX1-WT, HX1, HY0, HY1, FFL, Z2, MAT['stucco'])
# side walls
box("w_side_l", HX0+WT, HX1-WT, HY0, HY0+WT, FFL-0.02, RT-0.34, MAT['stucco'])
box("w_side_r", HX0+WT, HX1-WT, HY1-WT, HY1, FFL-0.02, RT-0.34, MAT['stucco'])
# front wall bedroom 1 wing with window opening Y 2.0..4.3
box("w_f1_a", HX0, HX0+WT, HY0, 2.0, FFL-0.02, Z2, MAT['stucco'])
box("w_f1_b", HX0, HX0+WT, 4.3, 5.5, FFL-0.02, Z2, MAT['stucco'])
box("w_f1_top", HX0, HX0+WT, 2.0, 4.3, FFL+2.7, Z2, MAT['stucco'])
box("win1", HX0+0.1, HX0+0.12, 2.0, 4.3, FFL+0.05, FFL+2.7, MAT['glass'])
# front wall bedroom 2 wing with window Y 13.7..16.0
box("w_f2_a", HX0, HX0+WT, 13.4, 13.7, FFL-0.02, Z2, MAT['stucco'])
box("w_f2_b", HX0, HX0+WT, 16.0, HY1, FFL-0.02, Z2, MAT['stucco'])
box("w_f2_top", HX0, HX0+WT, 13.7, 16.0, FFL+2.7, Z2, MAT['stucco'])
box("win2", HX0+0.1, HX0+0.12, 13.7, 16.0, FFL+0.05, FFL+2.7, MAT['glass'])
# interior partitions bedrooms (ground)
box("p1", HX0, HX1-WT, 5.5-WT/2, 5.5+WT/2, FFL-0.02, Z2, MAT['white'])
box("p2", HX0, HX1-WT, 13.4-WT/2, 13.4+WT/2, FFL-0.02, Z2, MAT['white'])
# central front: glass folding doors ground floor Y 5.5..13.4, frame + glass + mullions
box("gf_glass", HX0+0.08, HX0+0.10, 5.5, 13.4, FFL, Z2-0.3, MAT['glass'])
box("gf_head", HX0-0.05, HX0+WT, 5.5, 13.4, Z2-0.3, Z2, MAT['concrete'])
for i in range(9):
    y = 5.5 + i*(7.9/8)
    box(f"gf_mul{i}", HX0+0.04, HX0+0.14, y-0.03, y+0.03, FFL, Z2-0.3, MAT['black'])
box("gf_sill", HX0, HX0+0.18, 5.5, 13.4, FFL, FFL+0.02, MAT['black'])
# ground floor central back: sliding glass to back garden Y 5.6..13.4
box("gb_glass", HX1-0.12, HX1-0.10, 5.6, 13.4, FFL, Z2-0.3, MAT['glass'])
box("gb_head", HX1-WT, HX1+0.05, 5.6, 13.4, Z2-0.3, Z2, MAT['concrete'])
for i in range(5):
    y = 5.6 + i*(7.8/4)
    box(f"gb_mul{i}", HX1-0.16, HX1-0.06, y-0.03, y+0.03, FFL, Z2-0.3, MAT['black'])
# cut the back wall opening: rebuild back wall as two pieces instead of full
bpy.data.objects.remove(bpy.data.objects["w_back"], do_unlink=True)
box("w_back_a", HX1-WT, HX1, HY0, 5.6, FFL-0.02, Z2, MAT['stucco'])
box("w_back_b", HX1-WT, HX1, 13.4, HY1, FFL-0.02, Z2, MAT['stucco'])
box("w_back_top", HX1-WT, HX1, 5.6, 13.4, Z2-0.3, Z2, MAT['stucco'])
# entrance door (teak) on back wall at Y 4.2..5.4
box("door_main", HX1-0.05, HX1+0.02, 4.2, 5.4, FFL, FFL+2.6, MAT['teak_v'])
box("door_canopy", HX1-0.1, HX1+1.6, 3.6, 6.0, FFL+2.75, FFL+2.95, MAT['concrete'])

# second floor slab (over bedroom wings + corridor bridge along front, Y 5.5..13.4 depth 1.2) and balcony
box("slab2_l", HX0+WT, HX1-WT, HY0+WT, 5.5, Z2-0.3, Z2, MAT['concrete'])
box("slab2_r", HX0+WT, HX1-WT, 13.4, HY1-WT, Z2-0.3, Z2, MAT['concrete'])
box("slab2_bridge", HX0+WT, HX0+1.4, 5.5, 13.4, Z2-0.3, Z2, MAT['concrete'])
box("floor2_l", HX0+WT, HX1-WT, HY0+WT, 5.5, Z2-0.01, Z2+0.02, MAT['floor2'])
box("floor2_r", HX0+WT, HX1-WT, 13.4, HY1-WT, Z2-0.01, Z2+0.02, MAT['floor2'])
box("floor2_bridge", HX0+WT, HX0+1.4, 5.5, 13.4, Z2-0.01, Z2+0.02, MAT['floor2'])
# balcony cantilever slab X 40.2..43.2, Y 5.5..13.4
box("balcony", 40.2, HX0+0.05, 5.5, 13.4, Z2-0.3, Z2, MAT['concrete'])
box("balcony_floor", 40.25, HX0, 5.55, 13.35, Z2-0.01, Z2+0.02, MAT['deck'])
# glass railing
box("rail_f", 40.25, 40.27, 5.55, 13.35, Z2, Z2+1.1, MAT['glass_rail'])
box("rail_l", 40.25, HX0, 5.55, 5.57, Z2, Z2+1.1, MAT['glass_rail'])
box("rail_r", 40.25, HX0, 13.33, 13.35, Z2, Z2+1.1, MAT['glass_rail'])
box("rail_cap_f", 40.22, 40.30, 5.52, 13.38, Z2+1.08, Z2+1.12, MAT['steel'])
box("rail_cap_l", 40.22, HX0, 5.52, 5.60, Z2+1.08, Z2+1.12, MAT['steel'])
box("rail_cap_r", 40.22, HX0, 13.30, 13.38, Z2+1.08, Z2+1.12, MAT['steel'])
# balcony loungers
for i, y in enumerate((7.6, 9.45, 11.3)):
    place_z(lounger(f"bal{i}", 41.6, y, rot=math.pi, mat_fab=MAT['cushion']), Z2+0.02)

# second floor bedroom wings
box("w2_f3_a", HX0, HX0+WT, HY0, 1.6, Z2-0.02, RT-0.34, MAT['stucco'])
box("w2_f3_b", HX0, HX0+WT, 4.4, 5.5, Z2-0.02, RT-0.34, MAT['stucco'])
box("w2_f3_top", HX0, HX0+WT, 1.6, 4.4, Z2+2.6, RT-0.34, MAT['stucco'])
box("win3", HX0+0.1, HX0+0.12, 1.6, 4.4, Z2+0.05, Z2+2.6, MAT['glass'])
box("w2_f4_a", HX0, HX0+WT, 13.4, 13.6, Z2-0.02, RT-0.34, MAT['stucco'])
box("w2_f4_b", HX0, HX0+WT, 16.4, HY1, Z2-0.02, RT-0.34, MAT['stucco'])
box("w2_f4_top", HX0, HX0+WT, 13.6, 16.4, Z2+2.6, RT-0.34, MAT['stucco'])
box("win4", HX0+0.1, HX0+0.12, 13.6, 16.4, Z2+0.05, Z2+2.6, MAT['glass'])
box("w2_back", HX1-WT, HX1, HY0, HY1, Z2-0.02, RT-0.34, MAT['stucco'])
box("p3", HX0, HX1-WT, 5.5-WT/2, 5.5+WT/2, Z2-0.02, RT-0.34, MAT['white'])
box("p4", HX0, HX1-WT, 13.4-WT/2, 13.4+WT/2, Z2-0.02, RT-0.34, MAT['white'])
# second floor front: glass sliding doors to balcony Y 5.5..13.4
box("sf_glass", HX0+0.08, HX0+0.10, 5.5, 13.4, Z2, RT-0.65, MAT['glass'])
box("sf_head", HX0-0.05, HX0+WT, 5.5, 13.4, RT-0.65, RT-0.35, MAT['concrete'])
for i in range(9):
    y = 5.5 + i*(7.9/8)
    box(f"sf_mul{i}", HX0+0.04, HX0+0.14, y-0.03, y+0.03, Z2, RT-0.65, MAT['black'])
# teak brise-soleil screens in front of the 4 bedroom windows
def slats(name, x, y0, y1, z0, z1, n, mat):
    for i in range(n):
        y = y0 + (y1-y0)*(i+0.5)/n
        box(f"{name}_{i}", x, x+0.04, y-0.06, y+0.06, z0, z1, mat)
    box(f"{name}_top", x-0.02, x+0.06, y0, y1, z1, z1+0.06, mat)
    box(f"{name}_bot", x-0.02, x+0.06, y0, y1, z0-0.06, z0, mat)
slats("scr1", HX0-0.25, 1.9, 4.4, FFL+0.1, FFL+2.75, 14, MAT['teak_v'])
slats("scr2", HX0-0.25, 13.6, 16.1, FFL+0.1, FFL+2.75, 14, MAT['teak_v'])
slats("scr3", HX0-0.25, 1.5, 4.5, Z2+0.1, Z2+2.65, 16, MAT['teak_v'])
slats("scr4", HX0-0.25, 13.5, 16.5, Z2+0.1, Z2+2.65, 16, MAT['teak_v'])
# roof slab over whole house with 0.6 m front overhang, parapet
box("roof", HX0-0.7, HX1+0.3, HY0-0.3, HY1+0.3, RT-0.35, RT, MAT['concrete'])
box("roof_soffit", HX0-0.68, HX1+0.28, HY0-0.28, HY1+0.28, RT-0.37, RT-0.355, MAT['white'])
for nm, a in (("par_f", (HX0-0.7, HX0-0.5, HY0-0.3, HY1+0.3)), ("par_b", (HX1+0.1, HX1+0.3, HY0-0.3, HY1+0.3)),
              ("par_l", (HX0-0.7, HX1+0.3, HY0-0.3, HY0-0.1)), ("par_r", (HX0-0.7, HX1+0.3, HY1+0.1, HY1+0.3))):
    box(nm, *a, RT, RT+0.45, MAT['stucco'])
# roof-top slatted screen over laundry/AC zone (left back), X 49..51, Y 0.4..5.2
for i in range(10):
    y = 0.6 + i*0.5
    box(f"roofslat{i}", 48.9, 51.3, y, y+0.1, RT+0.3, RT+1.2, MAT['teak'])
box("roofslat_frame", 48.9, 51.3, 0.5, 5.6, RT+1.2, RT+1.28, MAT['black'])
# interior: double height living. feature wall of wood slats on back inside, furniture
for i in range(22):
    y = 6.0 + i*0.33
    box(f"feat{i}", HX1-WT-0.12, HX1-WT-0.02, y, y+0.1, FFL, RT-0.4, MAT['darkwood'])
# kitchen island, dining, sofa
box("island", 47.5, 50.5, 6.0, 7.0, FFL, FFL+0.9, MAT['concrete_d'])
box("island_top", 47.4, 50.6, 5.9, 7.1, FFL+0.9, FFL+0.95, MAT['white'])
box("kitchen_back", 50.0, 51.7, 5.6, 5.9, FFL, FFL+2.3, MAT['darkwood'])
box("dtable", 46.0, 49.0, 8.0, 9.2, FFL+0.72, FFL+0.78, MAT['darkwood'])
for cx in (46.5, 47.5, 48.5):
    for cy in (7.5, 9.7):
        box(f"chair{cx}{cy}", cx-0.22, cx+0.22, cy-0.22, cy+0.22, FFL+0.42, FFL+0.47, MAT['teak'])
        box(f"chairb{cx}{cy}", cx-0.22, cx+0.22, cy-0.03 + (0.19 if cy > 9 else -0.19), cy+0.03 + (0.19 if cy > 9 else -0.19), FFL+0.47, FFL+0.9, MAT['teak'])
box("sofa_a", 45.0, 47.6, 10.8, 11.7, FFL, FFL+0.42, MAT['sofa'])
box("sofa_ab", 45.0, 47.6, 11.6, 11.9, FFL+0.42, FFL+0.8, MAT['sofa'])
box("sofa_b", 47.6, 48.5, 9.9, 11.7, FFL, FFL+0.42, MAT['sofa'])
box("coffee", 45.3, 47.2, 9.9, 10.5, FFL+0.3, FFL+0.36, MAT['darkwood'])
box("rug", 44.6, 48.8, 9.6, 12.2, FFL, FFL+0.015, MAT['fabric'])
# ceiling of double height = roof soffit; recessed warm lights (emissive panels)
for x in (45.5, 48.5, 51.0):
    for y in (6.5, 9.5, 12.5):
        box(f"dl{x}{y}", x-0.08, x+0.08, y-0.08, y+0.08, RT-0.37, RT-0.355, MAT['lamp'])
# linear cove light along feature wall
box("cove", HX1-WT-0.16, HX1-WT-0.14, 6.0, 13.2, RT-0.5, RT-0.48, MAT['lamp'])
# bedroom lights visible through windows
for y in (3.2, 14.9):
    box(f"bl1{y}", 45.5, 45.66, y-0.08, y+0.08, Z2-0.32, Z2-0.305, MAT['lampcool'])
    box(f"bl2{y}", 45.5, 45.66, y-0.08, y+0.08, RT-0.37, RT-0.355, MAT['lampcool'])
    box(f"bed1{y}", 44.0, 46.0, y-1.0, y+1.0, FFL, FFL+0.5, MAT['cushion'])
    box(f"bed2{y}", 44.0, 46.0, y-1.0, y+1.0, Z2, Z2+0.5, MAT['cushion'])
# exterior wall sconces on fins and terrace
for y in (5.65, 13.25):
    box(f"sconce{y}", 38.9, 39.1, y-0.05, y+0.05, FFL+2.0, FFL+2.3, MAT['lamp'])
# terrace outdoor seating under balcony
box("osofa", 41.0, 42.0, 6.3, 9.3, FFL, FFL+0.45, MAT['cushion'])
box("osofa_b", 41.8, 42.0, 6.3, 9.3, FFL+0.45, FFL+0.85, MAT['cushion'])
box("otable", 40.6, 41.2, 7.2, 8.4, FFL+0.3, FFL+0.36, MAT['teak'])
box("odining", 41.0, 42.4, 10.4, 12.8, FFL+0.72, FFL+0.76, MAT['teak'])
for cx in (41.3, 42.1):
    for cy in (10.8, 11.6, 12.4):
        box(f"och{cx}{cy}", cx-0.2, cx+0.2, cy-0.2, cy+0.2, FFL+0.42, FFL+0.46, MAT['teak'])

# ------------------------------------------------------------------ driveway, parking, guard house, gate
box("drive", 52.0, 79.6, 6.0, 12.5, -0.04, 0.0, MAT['concrete'])
box("drive_j", 52.0, 79.6, 9.2, 9.28, 0.0, 0.004, MAT['grass'])  # grass joint strip
box("park", 56.0, 62.5, 0.6, 6.0, -0.04, 0.012, MAT['concrete'])
box("park_cover_c1", 56.3, 56.5, 0.8, 1.0, 0, 2.6, MAT['steel'])
box("park_cover_c2", 62.2, 62.4, 0.8, 1.0, 0, 2.6, MAT['steel'])
box("park_roof", 55.9, 62.7, 0.4, 6.1, 2.6, 2.7, MAT['concrete'])
for i in range(16):
    x = 56.0 + i*0.42
    box(f"park_slat{i}", x, x+0.08, 0.4, 6.1, 2.7, 2.85, MAT['teak'])
# guard house X 74..79, Y 0.4..6
box("guard", 74.0, 79.3, 0.4, 5.9, -0.05, 3.0, MAT['stucco_w'])
box("guard_roof", 73.7, 79.6, 0.1, 6.2, 3.0, 3.3, MAT['concrete'])
box("guard_win", 73.98, 74.02, 1.5, 4.5, 1.0, 2.4, MAT['glass'])
box("guard_win2", 75.5, 77.5, 5.88, 5.92, 1.0, 2.4, MAT['glass'])
# gate: teak slatted sliding gate Y 6..12.5 at X 79.7
for i in range(36):
    y = 6.05 + i*0.18
    box(f"gate{i}", 79.75, 79.85, y, y+0.1, 0.1, 2.3, MAT['teak_v'])
box("gate_fr_t", 79.72, 79.88, 6.0, 12.5, 2.3, 2.4, MAT['black'])
box("gate_fr_b", 79.72, 79.88, 6.0, 12.5, 0.0, 0.1, MAT['black'])
# gate pillars & lamps
box("gpil_a", 79.5, 80.1, 5.6, 6.0, -0.1, 2.8, MAT['concrete_d'])
box("gpil_b", 79.5, 80.1, 12.5, 12.9, -0.1, 2.8, MAT['concrete_d'])
box("gl_a", 79.6, 80.0, 5.7, 5.9, 2.8, 2.9, MAT['lamp'])
box("gl_b", 79.6, 80.0, 12.6, 12.8, 2.8, 2.9, MAT['lamp'])

def car(name, x, y, paint, rot=0.0):
    parts = []
    b = box(name+"_body", -2.3, 2.3, -0.9, 0.9, 0.35, 1.0, paint); bevel(b, 0.18, 4); parts.append(b)
    c = box(name+"_cab", -1.1, 1.3, -0.82, 0.82, 1.0, 1.55, MAT['glass']); bevel(c, 0.2, 4); parts.append(c)
    r = box(name+"_cabroof", -1.0, 1.1, -0.78, 0.78, 1.5, 1.56, paint); parts.append(r)
    for wx in (-1.45, 1.45):
        for wy in (-0.85, 0.85):
            bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.36, depth=0.25, location=(wx, wy, 0.36), rotation=(math.pi/2, 0, 0))
            w = bpy.context.active_object; w.name = name+"_w"; w.data.materials.append(MAT['tire']); parts.append(w)
    for p in parts:
        lx, ly, lz = p.location
        cr, sr = math.cos(rot), math.sin(rot)
        p.location = (x + lx*cr - ly*sr, y + lx*sr + ly*cr, lz)
        p.rotation_euler = (p.rotation_euler[0], p.rotation_euler[1], p.rotation_euler[2] + rot)
    return parts
car("car1", 59.2, 2.0, MAT['carpaint'], rot=0.0)
car("car2", 59.2, 4.4, MAT['carpaint2'], rot=0.0)

# ------------------------------------------------------------------ vegetation
def palm(name, x, y, h=7.0, lean=(0.0, 0.0), fronds=22, seed=0):
    rnd = random.Random(seed)
    # trunk: rings along a curved axis
    rings, segs = 18, 10
    verts, faces = [], []
    pts = []
    for i in range(rings+1):
        t = i/rings
        px = x + lean[0]*h*(t**2)
        py = y + lean[1]*h*(t**2)
        pz = t*h
        r = 0.22*(1-t) + 0.15*t + 0.015*math.sin(t*h*9)
        pts.append((px, py, pz))
        for j in range(segs):
            a = 2*math.pi*j/segs
            verts.append((px + r*math.cos(a), py + r*math.sin(a), pz))
    for i in range(rings):
        for j in range(segs):
            a = i*segs+j; b = i*segs+(j+1)%segs
            faces.append((a, b, b+segs, a+segs))
    faces.append(tuple(range(segs)))  # bottom cap
    tr = mesh_obj(name+"_trunk", verts, faces, MAT['trunk'], smooth=True)
    top = Vector(pts[-1])
    # crown: fronds
    fv, ff = [], []
    for k in range(fronds):
        yaw = 2*math.pi*k/fronds + rnd.uniform(-0.2, 0.2)
        pitch = rnd.uniform(-0.45, 1.1)   # radians above horizontal at base
        L = rnd.uniform(3.0, 4.2)
        droop = rnd.uniform(0.9, 1.6)
        d = Vector((math.cos(yaw), math.sin(yaw), 0.0))
        # rachis points
        rach = []
        n = 14
        for i in range(n+1):
            s = i/n
            p = top + d*(s*L*math.cos(pitch)) + Vector((0, 0, s*L*math.sin(pitch) - droop*(s**2)))
            rach.append(p)
        # rachis as thin quad strip
        side = Vector((-d.y, d.x, 0))
        base_idx = len(fv)
        for i, p in enumerate(rach):
            w = 0.04*(1-0.8*i/n)
            fv.append(p - side*w); fv.append(p + side*w)
        for i in range(n):
            a = base_idx + 2*i
            ff.append((a, a+1, a+3, a+2))
        # leaflets
        for i in range(1, n):
            s = i/n
            p = rach[i]
            tangent = (rach[i+1]-rach[i-1]).normalized()
            ll = 0.95*(1-0.55*s) + 0.12
            for sgn in (-1, 1):
                ang = rnd.uniform(0.5, 0.9)  # downward V angle
                dirv = (side*sgn*math.cos(ang) + Vector((0, 0, -math.sin(ang)))).normalized()
                dirv = (dirv + tangent*0.25).normalized()
                bi = len(fv)
                fv.append(p - tangent*0.045); fv.append(p + tangent*0.045)
                fv.append(p + dirv*ll + tangent*0.02); fv.append(p + dirv*ll - tangent*0.02)
                ff.append((bi, bi+1, bi+2, bi+3))
    cr = mesh_obj(name+"_crown", fv, ff, MAT['palmleaf'], smooth=False)
    # coconuts
    for i in range(5):
        a = rnd.uniform(0, 6.28)
        sphere(name+f"_nut{i}", top.x + 0.3*math.cos(a), top.y + 0.3*math.sin(a), top.z - 0.35, 0.13, MAT['leaf'], subdiv=2)
    return tr

def canopy_tree(name, x, y, h=5.0, r=2.6, seed=0, subdiv=4):
    rnd = random.Random(seed)
    cyl(name+"_trunk", x, y, 0, h*0.55, 0.18, MAT['trunk'])
    for i in range(6):
        ox = rnd.uniform(-r*0.5, r*0.5); oy = rnd.uniform(-r*0.5, r*0.5); oz = rnd.uniform(-r*0.3, r*0.4)
        rad = r*rnd.uniform(0.5, 0.8)
        s = sphere(name+f"_c{i}", x+ox, y+oy, h*0.55 + r*0.55 + oz, rad, MAT['leaf'], subdiv=subdiv)
        tex = bpy.data.textures.new(name+f"_t{i}", 'CLOUDS'); tex.noise_scale = 0.45; tex.noise_depth = 4
        m = s.modifiers.new('disp', 'DISPLACE'); m.texture = tex; m.strength = 1.1/rad; m.texture_coords = 'GLOBAL'
    return None

def bush(name, x, y, r=0.8, seed=0, z=0.0, subdiv=4):
    rnd = random.Random(seed)
    for i in range(5):
        rad = r*rnd.uniform(0.45, 0.8)
        s = sphere(name+f"_b{i}", x+rnd.uniform(-r*0.55, r*0.55), y+rnd.uniform(-r*0.55, r*0.55), z + r*rnd.uniform(0.25, 0.5), rad, MAT['bush'], subdiv=subdiv)
        tex = bpy.data.textures.new(name+f"_t{i}", 'CLOUDS'); tex.noise_scale = 0.18; tex.noise_depth = 3
        m = s.modifiers.new('disp', 'DISPLACE'); m.texture = tex; m.strength = 0.5/rad; m.texture_coords = 'GLOBAL'

def hedge(name, x0, x1, y, z, r=0.35, seed=0):
    rnd = random.Random(seed)
    n = int((x1-x0)/(r*0.9)) + 1
    for i in range(n):
        x = x0 + (x1-x0)*i/max(1, n-1)
        rad = r*rnd.uniform(0.8, 1.2)
        s = sphere(f"{name}_{i}", x + rnd.uniform(-0.1, 0.1), y + rnd.uniform(-0.12, 0.12), z + r*rnd.uniform(0.7, 1.1), rad, MAT['bush'], subdiv=4)
        tex = bpy.data.textures.new(s.name+'_t', 'CLOUDS'); tex.noise_scale = 0.12; tex.noise_depth = 3
        m = s.modifiers.new('disp', 'DISPLACE'); m.texture = tex; m.strength = 0.3/rad; m.texture_coords = 'GLOBAL'

# palms along the driveway (Y 12.9 line) and parking side
for i in range(8):
    palm(f"dpalm{i}", 55.5 + i*2.6, 13.3 + 0.3*math.sin(i), h=random.uniform(6.0, 8.5), lean=(random.uniform(-0.05, 0.05), random.uniform(0.0, 0.08)), seed=i)
for i in range(3):
    palm(f"ppalm{i}", 64.5 + i*3.0, 3.0, h=random.uniform(7, 9), lean=(0.02, -0.04), seed=20+i)
# palms in beachfront lawn and terrace sides
palm("fpalm0", 21.2, 9.5, h=9.0, lean=(-0.08, 0.02), seed=30)
palm("fpalm1", 21.6, 14.0, h=7.5, lean=(-0.06, 0.05), seed=31)
palm("fpalm2", 25.5, 16.5, h=8.5, lean=(-0.03, 0.06), seed=32)
palm("fpalm3", 25.0, 10.5, h=6.0, lean=(-0.08, 0.0), seed=33)
palm("spalm0", 36.5, 0.9, h=8.0, lean=(0.0, -0.05), seed=40)
palm("spalm1", 41.0, 1.0, h=9.5, lean=(-0.04, -0.04), seed=41)
palm("spalm2", 36.5, 17.1, h=8.5, lean=(0.0, 0.05), seed=42)
palm("spalm3", 41.0, 17.0, h=7.0, lean=(-0.04, 0.05), seed=43)
palm("bpalm0", 53.5, 2.5, h=7.5, lean=(0.03, -0.03), seed=50)
palm("bpalm1", 53.5, 16.0, h=8.0, lean=(0.03, 0.03), seed=51)
# trees in back lawn & neighbors
canopy_tree("tree_a", 68.0, 15.5, h=6.0, r=3.2, seed=1)
canopy_tree("tree_b", 54.5, 4.0, h=4.5, r=2.4, seed=2)
# bushes: planters and lawn edges
hedge("wall_hedge_l", 27.5, 35.5, 0.6, 0.0, r=0.5, seed=3)
hedge("wall_hedge_r", 27.5, 35.5, 17.4, 0.0, r=0.5, seed=4)
hedge("wall_hedge_l2", 36.5, 43.0, 0.6, FFL, r=0.45, seed=5)
hedge("wall_hedge_r2", 36.5, 43.0, 17.4, FFL, r=0.45, seed=6)
for i in range(9):
    bush(f"db_l{i}", 53.0 + i*2.4, 0.9, r=0.8, seed=140+i)
for i in range(5):
    bush(f"fb{i}", 20.8 + i*1.4, 16.9, r=0.7, seed=160+i)
for i in range(6):
    bush(f"bb{i}", 26.2, 7.8 + i*1.6, r=0.6, seed=180+i)
hedge("hedge_l", 36.3, 43.0, 2.3, FFL+0.42, r=0.36, seed=1)
hedge("hedge_r", 36.3, 43.0, 15.7, FFL+0.42, r=0.36, seed=2)
# neighbors: scattered palms and bushes on both sides and across road (context)
rn = random.Random(99)
for i in range(140):
    x = rn.uniform(18, 110); y = rn.choice([rn.uniform(-90, -3), rn.uniform(21, 110)])
    if rn.random() < 0.55:
        palm(f"npalm{i}", x, y, h=rn.uniform(5, 10), lean=(rn.uniform(-0.08, 0.08), rn.uniform(-0.08, 0.08)), fronds=12, seed=200+i)
    else:
        canopy_tree(f"ntree{i}", x, y, h=rn.uniform(3.5, 6.5), r=rn.uniform(2, 3.5), seed=300+i, subdiv=3)
for i in range(90):
    x = rn.uniform(16, 110); y = rn.choice([rn.uniform(-90, -2), rn.uniform(20, 110)])
    bush(f"nbush{i}", x, y, r=rn.uniform(0.7, 1.6), seed=400+i, subdiv=3)
# a few neighbor low houses for context
box("nh1", 40, 52, -14, -4, -0.05, 3.2, MAT['stucco_w']); box("nh1r", 39.5, 52.5, -14.5, -3.5, 3.2, 3.5, MAT['concrete_d'])
box("nh2", 44, 58, 24, 34, -0.05, 3.0, MAT['offwhite']); box("nh2r", 43.5, 58.5, 23.5, 34.5, 3.0, 3.3, MAT['terracotta'])
box("nh3", 60, 70, -30, -22, -0.05, 2.8, MAT['stucco']); box("nh3r", 59.5, 70.5, -30.5, -21.5, 2.8, 3.1, MAT['concrete_d'])

# ------------------------------------------------------------------ world / lighting
world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes['Background']
sky = wn.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'NISHITA'
sky.sun_size = math.radians(1.0)
sky.altitude = 5
sky.air_density = 1.0
sky.dust_density = 1.2
sky.ozone_density = 1.5
wn.links.new(sky.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0

if VIEW == 'dusk':
    sky.sun_elevation = math.radians(2.5)
    sky.sun_rotation = math.radians(250)
    sky.sun_intensity = 0.9
    sky.dust_density = 4.0
    exposure = -1.6
    for nm in ('lamp', 'lampcool'):
        MAT[nm].node_tree.nodes['Emission'].inputs['Strength'].default_value *= 3.0
else:
    sky.sun_elevation = math.radians(26)
    sky.sun_rotation = math.radians(225 if VIEW != 'pool' else 60)
    sky.sun_intensity = 1.0
    exposure = -2.6

scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Punchy'
except Exception:
    pass
scene.view_settings.exposure = exposure

# ------------------------------------------------------------------ camera
cam = bpy.data.cameras.new("cam"); cam.sensor_width = 36
camob = bpy.data.objects.new("cam", cam); link(camob); scene.camera = camob

def set_cam(loc, target, lens=24, level=True):
    cam.lens = lens
    loc = Vector(loc); target = Vector(target)
    d = target - loc
    if level:
        horiz = Vector((d.x, d.y, 0.0))
        yaw = math.atan2(horiz.y, horiz.x)
        camob.rotation_euler = Euler((math.pi/2, 0, yaw - math.pi/2), 'XYZ')
        cam.shift_y = (lens/36.0) * (d.z/horiz.length)
    else:
        camob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam.shift_y = 0
    camob.location = loc

if VIEW == 'hero':
    set_cam((26.7, 3.5, 1.75), (44.0, 11.6, 3.3), lens=24)
elif VIEW == 'dusk':
    set_cam((26.7, 3.0, 1.75), (44.0, 11.4, 3.3), lens=24)
elif VIEW == 'pool':
    set_cam((40.6, 9.6, Z2+2.1), (14.0, 6.0, -1.2), lens=20, level=False)
elif VIEW == 'aerial':
    set_cam((-30.0, -34.0, 36.0), (37.0, 9.0, 0.0), lens=38, level=False)
elif VIEW == 'street':
    set_cam((88.0, 15.5, 1.7), (76.0, 8.0, 2.4), lens=24)
elif VIEW == 'suntest':
    set_cam((23.5, 1.2, 1.7), (44.5, 9.0, 3.6), lens=26)

# ------------------------------------------------------------------ render settings
if QUALITY.startswith('preview'):
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    scene.cycles.samples = 48
elif QUALITY == 'final':
    scene.render.resolution_x, scene.render.resolution_y = 2560, 1440
    scene.cycles.samples = 200
else:
    scene.render.resolution_x, scene.render.resolution_y = 2560, 1440
    scene.cycles.samples = 400
scene.render.resolution_percentage = 100
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.03
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 8
scene.cycles.transparent_max_bounces = 24
scene.cycles.volume_bounces = 1
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.cycles.sample_clamp_indirect = 8.0
scene.cycles.blur_glossy = 1.0
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '8'
scene.render.filepath = OUT
scene.render.threads_mode = 'AUTO'
try:
    scene.cycles_curves.shape = 'RIBBONS'
    scene.cycles_curves.subdivisions = 2
except Exception:
    pass

print("objects:", len(bpy.data.objects))
bpy.ops.render.render(write_still=True)
print("DONE", OUT)
