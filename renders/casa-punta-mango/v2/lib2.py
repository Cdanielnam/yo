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


# ---- helper functions ----
FFL = 0.45
Z2 = FFL + 3.4
RT = Z2 + 3.1 + 0.35
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


def slats(name, x, y0, y1, z0, z1, n, mat):
    for i in range(n):
        y = y0 + (y1-y0)*(i+0.5)/n
        box(f"{name}_{i}", x, x+0.04, y-0.06, y+0.06, z0, z1, mat)
    box(f"{name}_top", x-0.02, x+0.06, y0, y1, z1, z1+0.06, mat)
    box(f"{name}_bot", x-0.02, x+0.06, y0, y1, z0-0.06, z0, mat)

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

