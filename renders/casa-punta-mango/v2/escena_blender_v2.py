# Casa Punta Mango v2 - updated design (pitched tile roof, wraparound terrace, entrance garden, L-pool at beach)
import sys, math, random
HERE = "/tmp/claude-0/-home-user-yo/672b3b8a-8a38-59da-af9e-11608921219c/scratchpad/render"
sys.argv = [sys.argv[0]] + sys.argv[1:]
VIEW = sys.argv[1] if len(sys.argv) > 1 else "hero"
QUALITY = sys.argv[2] if len(sys.argv) > 2 else "preview"
sys.argv = [sys.argv[0], VIEW, QUALITY, f"{HERE}/v2_{VIEW}_{QUALITY}.png"]
exec(open(f"{HERE}/lib2.py").read())
import bpy, math, random
from mathutils import Vector

FFL = 0.45            # house finished floor above lawn/pool deck (Z=0)
Z2 = FFL + 3.5        # second floor level (N=3.50)
WT = 0.25
HX0, HX1, HY0, HY1 = 41.5, 50.0, 0.1, 17.9   # ground floor body
SX0, SX1, SY0, SY1 = 42.7, 50.0, 0.1, 17.9   # second floor volume (full width per plan)
EAVE = Z2 + 3.0

# extra materials
def m_tile(name="rooftile"):
    m, nt, b, o = new_mat(name)
    vec = tex_coord(nt, 1.0)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.015
    br.inputs['Brick Width'].default_value = 0.22
    br.inputs['Row Height'].default_value = 0.38
    br.inputs['Color1'].default_value = (0.62, 0.40, 0.28, 1)
    br.inputs['Color2'].default_value = (0.55, 0.34, 0.24, 1)
    br.inputs['Mortar'].default_value = (0.35, 0.22, 0.16, 1)
    br.offset = 0.5
    nt.links.new(vec, br.inputs['Vector'])
    n = noise(nt, vec, scale=3, detail=4)
    c = mixrgb(nt, 0.2, br.outputs['Color'], n.outputs['Color'])
    nt.links.new(c, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.8
    w = nt.nodes.new('ShaderNodeTexWave'); w.bands_direction = 'Y'; w.inputs['Scale'].default_value = 4.5
    nt.links.new(vec, w.inputs['Vector'])
    mx = mixrgb(nt, 0.5, br.outputs['Fac'], w.outputs['Fac'])
    bump(nt, b, mx, 0.5, 0.03)
    return m
MAT['rooftile'] = m_tile()
MAT['rail'] = m_simple("railmetal", (0.12, 0.11, 0.10, 1), 0.35, 0.9)

def hip_roof(name, x0, x1, y0, y1, ze, pitch_deg, thick=0.22, mat=None):
    """hip roof, ridge along Y (long axis), eaves at ze"""
    mat = mat or MAT['rooftile']
    hs = (x1 - x0) / 2.0
    zr = ze + hs * math.tan(math.radians(pitch_deg))
    xm = (x0 + x1) / 2.0
    top = [(x0, y0, ze), (x1, y0, ze), (x1, y1, ze), (x0, y1, ze), (xm, y0 + hs, zr), (xm, y1 - hs, zr)]
    bot = [(x, y, z - thick) for (x, y, z) in top]
    v = top + bot
    faces = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5),            # top
             (6, 10, 7), (7, 10, 11, 8), (8, 11, 9), (9, 11, 10, 6),      # bottom (reversed)
             (0, 6, 7, 1), (1, 7, 8, 2), (2, 8, 9, 3), (3, 9, 6, 0)]      # eave sides
    return mesh_obj(name, v, faces, mat)

def shed_roof(name, x0, x1, y0, y1, z_out, z_in, thick=0.2, mat=None):
    mat = mat or MAT['rooftile']
    top = [(x0, y0, z_out), (x1, y0, z_in), (x1, y1, z_in), (x0, y1, z_out)]
    bot = [(x, y, z - thick) for (x, y, z) in top]
    v = top + bot
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return mesh_obj(name, v, faces, mat)

def railing(name, pts, z, h=1.05, mat=None):
    """horizontal-rail railing along polyline pts [(x,y),...] at base z"""
    mat = mat or MAT['rail']
    k = 0
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / 1.6))
        for i in range(n + 1):
            t = i / n
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            box(f"{name}_p{k}", px - 0.025, px + 0.025, py - 0.025, py + 0.025, z, z + h, mat); k += 1
        for zz, th in ((z + h - 0.02, 0.05), (z + 0.70, 0.02), (z + 0.40, 0.02), (z + 0.15, 0.02)):
            if abs(bx - ax) > abs(by - ay):
                box(f"{name}_r{k}", min(ax, bx), max(ax, bx), ay - th / 2, ay + th / 2, zz, zz + th, mat)
            else:
                box(f"{name}_r{k}", ax - th / 2, ax + th / 2, min(ay, by), max(ay, by), zz, zz + th, mat)
            k += 1

# ------------------------------------------------------------------ terrain & grounds
terrain()
# beach zone starts at X=7 (sea wall), pool deck X 9..27
box("seawall", 6.6, 7.1, -0.3, 18.3, -0.9, 0.08, MAT['concrete'])
for i in range(4):
    box(f"beachstep{i}", 6.6-0.35*(i+1), 6.6-0.35*i, 7.0, 11.0, -0.9, 0.05-0.22*(i+1), MAT['concrete'])
lawn("lawn_beach_a", 7.1, 9.0, 0.1, 17.9, 0.0)
lawn("lawn_beach_l", 9.0, 27.0, 0.1, 1.0, 0.0)
lawn("lawn_beach_r", 9.0, 27.0, 17.0, 17.9, 0.0)
lawn("lawn_mid_l", 27.0, 41.5, 0.1, 5.9, 0.0)
lawn("lawn_mid_r", 27.0, 41.5, 14.0, 17.9, 0.0)
lawn("lawn_back_l", 50.0, 74.0, 0.1, 5.7, 0.0)
lawn("lawn_back_r", 50.0, 79.5, 12.0, 17.9, 0.0)
lawn("lawn_patio_l", 50.0, 55.5, 0.1, 3.8, 0.0, hair=False)
lawn("lawn_patio_r", 50.0, 55.5, 15.8, 17.9, 0.0, hair=False)
# perimeter walls: low along beach zone, tall along the rest
box("wall_s_low", 7.1, 28.6, -0.25, 0.0, -0.1, 1.6, MAT['stucco'])
box("wall_n_low", 7.1, 28.6, 18.0, 18.25, -0.1, 1.6, MAT['stucco'])
box("wall_s", 28.6, 80, -0.25, 0.0, -0.1, 2.2, MAT['stucco'])
box("wall_n", 28.6, 80, 18.0, 18.25, -0.1, 2.2, MAT['stucco'])
box("wall_back_a", 79.6, 80.0, 0, 5.7, -0.1, 2.4, MAT['stucco'])
box("wall_back_b", 79.6, 80.0, 12.3, 18.0, -0.1, 2.4, MAT['stucco'])

# ------------------------------------------------------------------ beach zone: pool deck, L pool, bar block
box("pdeck", 9.0, 27.0, 1.0, 17.0, -0.06, 0.0, MAT['trav'])
# L pool: A X 11.6..16.4 Y 4..15.2 ; B X 16.4..18.7 Y 4..11.7 ; jacuzzi X 12.4..15.2 Y 1.4..4
def basin(name, x0, x1, y0, y1, depth):
    box(name+"_floor", x0, x1, y0, y1, -depth-0.1, -depth, MAT['tile'])
    box(name+"_w0", x0-0.1, x0, y0-0.1, y1+0.1, -depth, -0.02, MAT['tile'])
    box(name+"_w1", x1, x1+0.1, y0-0.1, y1+0.1, -depth, -0.02, MAT['tile'])
    box(name+"_w2", x0, x1, y0-0.1, y0, -depth, -0.02, MAT['tile'])
    box(name+"_w3", x0, x1, y1, y1+0.1, -depth, -0.02, MAT['tile'])
# cut the deck: rebuild as pieces around the L + jacuzzi
bpy.data.objects.remove(bpy.data.objects["pdeck"], do_unlink=True)
for nm, a in (("pd1", (9.0, 11.6, 1.0, 17.0)), ("pd2", (11.6, 12.4, 1.0, 4.0)), ("pd3", (15.2, 16.4, 1.0, 4.0)),
              ("pd4", (16.4, 18.7, 1.0, 4.0)), ("pd5", (18.7, 27.0, 1.0, 17.0)), ("pd6", (16.4, 18.7, 11.7, 17.0)),
              ("pd7", (11.6, 16.4, 15.2, 17.0))):
    box(nm, *a, -0.06, 0.0, MAT['trav'])
basin("poolA", 11.6, 16.4, 4.0, 15.2, 1.6)
basin("poolB", 16.4, 18.7, 4.0, 11.7, 1.6)
bpy.data.objects.remove(bpy.data.objects["poolA_w1"], do_unlink=True)   # shared wall A/B (partial)
box("poolA_w1b", 16.4, 16.5, 11.7, 15.2, -1.6, -0.02, MAT['tile'])
bpy.data.objects.remove(bpy.data.objects["poolB_w0"], do_unlink=True)
basin("jacuzzi", 12.4, 15.2, 1.4, 4.0, 0.9)
box("jac_seat", 12.4, 15.2, 1.4, 1.9, -0.9, -0.45, MAT['tile'])
box("pool_lounge", 11.6, 13.0, 12.0, 15.2, -1.6, -0.45, MAT['tile'])
box("pool_step", 11.6, 12.3, 12.0, 15.2, -0.45, -0.25, MAT['tile'])
box("water_A", 11.605, 16.395, 4.005, 15.195, -1.5, -0.12, MAT['water'])
box("water_B", 16.395, 18.695, 4.005, 11.695, -1.5, -0.12, MAT['water'])
box("water_J", 12.405, 15.195, 1.405, 3.995, -0.85, -0.10, MAT['water'])
for nm, a in (("copA", (11.25, 16.75, 3.65, 4.0)), ("copA2", (11.25, 16.75, 15.2, 15.55)), ("copA3", (11.25, 11.6, 4.0, 15.2)),
              ("copB", (16.75, 19.05, 3.65, 4.0)), ("copB2", (16.4, 19.05, 11.7, 12.05)), ("copB3", (18.7, 19.05, 4.0, 11.7)),
              ("copA4", (16.4, 16.75, 12.05, 15.2)), ("copJ", (12.05, 15.55, 1.05, 1.4)), ("copJ2", (12.05, 12.4, 1.4, 3.65)), ("copJ3", (15.2, 15.55, 1.4, 3.65))):
    box(nm, *a, -0.012, 0.03, MAT['poolcope'])
# loungers: west row facing the pool (+Y), east row facing (-Y)
for i in range(6):
    place_z(lounger(f"lw{i}", 19.6 + i*1.25, 2.3, rot=-math.pi/2), 0.0)
for i in range(5):
    place_z(lounger(f"le{i}", 13.6 + i*1.25, 15.9, rot=math.pi/2), 0.0)
# umbrella + loungers at the sea end
cyl("umb_pole", 9.9, 9.0, 0.0, 2.6, 0.025, MAT['steel'])
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=1.5, radius2=0.0, depth=0.4, location=(9.9, 9.0, 2.5))
umb = bpy.context.active_object; umb.name = "umb_top"; umb.data.materials.append(MAT['offwhite'])
place_z(lounger("lu0", 10.2, 7.3, rot=math.pi), 0.0)
place_z(lounger("lu1", 10.2, 10.7, rot=math.pi), 0.0)
# bar block: bar + full bathroom + 2 changing rooms, X 21..26, Y 12.6..17.8
box("bar_body", 21.0, 26.0, 12.6, 17.8, -0.06, 2.9, MAT['stucco_w'])
box("bar_open", 20.98, 21.6, 13.0, 16.2, 1.1, 2.6, MAT['darkwood'])     # back bar shelf wall (dark wood)
box("bar_counter", 20.3, 21.0, 13.0, 16.2, -0.06, 1.05, MAT['concrete_d'])
box("bar_top", 20.2, 21.1, 12.9, 16.3, 1.05, 1.1, MAT['white'])
for i in range(4):
    cyl(f"bstool{i}", 19.8, 13.4 + i*0.85, 0.0, 0.72, 0.17, MAT['teak'])
box("bar_door_bath", 23.0, 23.9, 12.58, 12.62, 0.0, 2.2, MAT['teak_v'])
box("bar_door_ch1", 24.3, 25.0, 12.58, 12.62, 0.0, 2.2, MAT['teak_v'])
box("bar_door_ch2", 25.2, 25.9, 12.58, 12.62, 0.0, 2.2, MAT['teak_v'])
box("bar_roof", 20.6, 26.4, 12.2, 18.2, 2.9, 3.15, MAT['concrete'])
# pergola terrace in front of the bar X 18.7..21
for nm, (x, y) in (("pp0", (18.9, 12.8)), ("pp1", (18.9, 17.6))):
    box(nm, x-0.08, x+0.08, y-0.08, y+0.08, 0.0, 2.9, MAT['teak'])
box("pergola_beam", 18.75, 21.0, 12.7, 12.86, 2.9, 3.1, MAT['teak']); box("pergola_beam2", 18.75, 21.0, 17.54, 17.7, 2.9, 3.1, MAT['teak'])
for i in range(12):
    y = 12.8 + i*0.42
    box(f"pslat{i}", 18.75, 21.0, y, y+0.08, 3.1, 3.28, MAT['teak'])
box("bar_table", 19.4, 20.2, 14.0, 15.4, 0.70, 0.75, MAT['teak'])
# planting along the beach-zone walls
hedge("bhedge_l", 9.5, 26.5, 0.5, 0.0, r=0.5, seed=11)
hedge("bhedge_r", 9.5, 20.0, 17.5, 0.0, r=0.5, seed=12)

# ------------------------------------------------------------------ path, terrace, house plinth
box("path", 27.0, 38.5, 5.9, 14.0, -0.05, 0.15, MAT['concrete'])
box("terrace", 38.5, 41.6, 2.0, 14.2, -0.05, FFL-0.15, MAT['trav'])
box("tstep", 38.1, 38.5, 5.9, 14.0, -0.05, 0.15 + (FFL-0.15-0.15)/2, MAT['trav'])
box("plinth", HX0, HX1, HY0, HY1, -0.05, FFL, MAT['trav'])
box("floor1", HX0+0.1, HX1-0.1, HY0+0.1, HY1-0.1, FFL-0.02, FFL+0.012, MAT['floor'])
box("tstep_in", 41.5, 41.6, 2.0, 14.2, FFL-0.15, FFL, MAT['trav'])
# terrace wing walls supporting the balcony
box("wing_l", 38.5, 41.5, 2.0, 2.3, FFL-0.18, Z2-0.3, MAT['concrete'])
box("wing_r", 38.5, 41.5, 13.9, 14.2, FFL-0.18, Z2-0.3, MAT['concrete'])

# ------------------------------------------------------------------ ground floor walls
# front wall X=41.5: bedroom windows with slats, central glass Y 4.7..13.3
box("w_f_a", HX0, HX0+WT, HY0, 1.5, FFL-0.02, Z2, MAT['stucco'])
box("w_f_b", HX0, HX0+WT, 4.2, 4.7, FFL-0.02, Z2, MAT['stucco'])
box("w_f_c", HX0, HX0+WT, 13.3, 13.8, FFL-0.02, Z2, MAT['stucco'])
box("w_f_d", HX0, HX0+WT, 16.6, HY1, FFL-0.02, Z2, MAT['stucco'])
box("w_f_t1", HX0, HX0+WT, 1.5, 4.2, FFL+2.7, Z2, MAT['stucco'])
box("w_f_t2", HX0, HX0+WT, 13.8, 16.6, FFL+2.7, Z2, MAT['stucco'])
box("win1", HX0+0.1, HX0+0.12, 1.5, 4.2, FFL+0.05, FFL+2.7, MAT['glass'])
box("win2", HX0+0.1, HX0+0.12, 13.8, 16.6, FFL+0.05, FFL+2.7, MAT['glass'])
slats("scr1", HX0-0.25, 1.4, 4.3, FFL+0.1, FFL+2.75, 16, MAT['teak_v'])
slats("scr2", HX0-0.25, 13.7, 16.7, FFL+0.1, FFL+2.75, 16, MAT['teak_v'])
box("gf_glass", HX0+0.08, HX0+0.10, 4.7, 13.3, FFL, Z2-0.35, MAT['glass'])
box("gf_head", HX0-0.05, HX0+WT, 4.7, 13.3, Z2-0.35, Z2, MAT['concrete'])
for i in range(9):
    y = 4.7 + i*(8.6/8)
    box(f"gf_mul{i}", HX0+0.04, HX0+0.14, y-0.03, y+0.03, FFL, Z2-0.35, MAT['black'])
box("gf_sill", HX0, HX0+0.18, 4.7, 13.3, FFL, FFL+0.02, MAT['black'])
# side walls
box("w_side_l", HX0+WT, HX1-WT, HY0, HY0+WT, FFL-0.02, Z2, MAT['stucco'])
box("w_side_r", HX0+WT, HX1-WT, HY1-WT, HY1, FFL-0.02, Z2, MAT['stucco'])
# back wall X=50: entrance door Y 4..6.3, glass to patio Y 7..12
box("w_b_a", HX1-WT, HX1, HY0, 4.0, FFL-0.02, Z2, MAT['stucco'])
box("w_b_b", HX1-WT, HX1, 6.3, 7.0, FFL-0.02, Z2, MAT['stucco'])
box("w_b_c", HX1-WT, HX1, 12.0, HY1, FFL-0.02, Z2, MAT['stucco'])
box("w_b_t1", HX1-WT, HX1, 4.0, 6.3, FFL+2.6, Z2, MAT['stucco'])
box("w_b_t2", HX1-WT, HX1, 7.0, 12.0, Z2-0.35, Z2, MAT['stucco'])
box("door_main", HX1-0.05, HX1+0.02, 4.0, 6.3, FFL, FFL+2.6, MAT['teak_v'])
box("door_canopy", HX1-0.1, HX1+1.8, 3.4, 6.9, FFL+2.75, FFL+2.95, MAT['concrete'])
box("gb_glass", HX1-0.12, HX1-0.10, 7.0, 12.0, FFL, Z2-0.35, MAT['glass'])
for i in range(5):
    y = 7.0 + i*1.25
    box(f"gb_mul{i}", HX1-0.16, HX1-0.06, y-0.03, y+0.03, FFL, Z2-0.35, MAT['black'])
# interior partitions
# interior: jardín planter at the entry, feature wall, furniture, lights
box("jardin", 48.3, 49.3, 8.3, 11.9, FFL, FFL+0.5, MAT['concrete_d'])
for i in range(4):
    bush(f"jbush{i}", 48.8, 8.7 + i*0.95, r=0.45, seed=500+i, z=FFL+0.5)
for i in range(16):
    y = 12.6 + i*0.25
    box(f"feat{i}", HX1-WT-0.12, HX1-WT-0.02, y, y+0.08, FFL, Z2, MAT['darkwood'])
box("dtable", 44.5, 47.3, 7.6, 8.8, FFL+0.72, FFL+0.78, MAT['darkwood'])
for cx in (45.0, 46.0, 47.0):
    for cy in (7.1, 9.3):
        box(f"chair{cx}{cy}", cx-0.22, cx+0.22, cy-0.22, cy+0.22, FFL+0.42, FFL+0.47, MAT['teak'])
        box(f"chairb{cx}{cy}", cx-0.22, cx+0.22, cy-0.03 + (0.19 if cy > 9 else -0.19), cy+0.03 + (0.19 if cy > 9 else -0.19), FFL+0.47, FFL+0.9, MAT['teak'])
box("sofa_a", 43.5, 46.0, 10.2, 11.1, FFL, FFL+0.42, MAT['sofa'])
box("sofa_ab", 43.5, 46.0, 11.0, 11.3, FFL+0.42, FFL+0.8, MAT['sofa'])
box("sofa_b", 46.0, 46.9, 9.4, 11.1, FFL, FFL+0.42, MAT['sofa'])
box("coffee", 43.8, 45.6, 9.4, 10.0, FFL+0.3, FFL+0.36, MAT['darkwood'])
box("rug", 43.2, 47.2, 9.1, 11.6, FFL, FFL+0.015, MAT['fabric'])
for y in (3.2, 14.8):
    box(f"bl1{y}", 44.0, 44.16, y-0.08, y+0.08, Z2-0.32, Z2-0.305, MAT['lampcool'])
# second floor slab over the whole ground floor (wraparound terrace) + balcony cantilever
box("slab2", HX0+WT, HX1-WT, HY0+WT, HY1-WT, Z2-0.3, Z2, MAT['concrete'])
box("slab2_edge_f", HX0-0.05, HX0+WT, HY0-0.05, HY1+0.05, Z2-0.3, Z2, MAT['concrete'])
box("slab2_edge_l", HX0-0.05, HX1+0.05, HY0-0.05, HY0+WT, Z2-0.3, Z2, MAT['concrete'])
box("slab2_edge_r", HX0-0.05, HX1+0.05, HY1-WT, HY1+0.05, Z2-0.3, Z2, MAT['concrete'])
box("balcony", 39.9, HX0, 4.5, 13.4, Z2-0.3, Z2, MAT['concrete'])
box("terr2_floor_f", 39.95, SX0, HY0+0.05, HY1-0.05, Z2-0.01, Z2+0.02, MAT['deck'])
# fix: balcony deck only within Y 4.5..13.4 beyond X 41.5
bpy.data.objects.remove(bpy.data.objects["terr2_floor_f"], do_unlink=True)
box("terr2_floor_f1", HX0, SX0, HY0+0.05, HY1-0.05, Z2-0.01, Z2+0.02, MAT['deck'])
box("terr2_floor_f2", 39.95, HX0, 4.55, 13.35, Z2-0.01, Z2+0.02, MAT['deck'])
# railing around the level-3.5 terrace
railing("rail", [(SX0, HY0+0.15), (HX0+0.08, HY0+0.15), (HX0+0.08, 4.55), (39.98, 4.55), (39.98, 13.35), (HX0+0.08, 13.35), (HX0+0.08, HY1-0.15), (SX0, HY1-0.15)], Z2+0.02)
# balcony lounge chairs & planters
for i, y in enumerate((6.6, 8.6)):
    place_z(lounger(f"bal{i}", 40.9, y, rot=math.pi, mat_fab=MAT['cushion']), Z2+0.02)
box("bal_table", 40.5, 41.3, 10.3, 12.3, Z2+0.72, Z2+0.76, MAT['teak'])
for cx in (40.4, 41.3):
    for cy in (10.7, 11.9):
        box(f"bch{cx}{cy}", cx-0.2, cx+0.2, cy-0.2, cy+0.2, Z2+0.44, Z2+0.48, MAT['teak'])

# ------------------------------------------------------------------ second floor volume
box("w2_f_a", SX0, SX0+WT, SY0, 1.7, Z2-0.02, EAVE, MAT['stucco'])
box("w2_f_b", SX0, SX0+WT, 4.2, 4.7, Z2-0.02, EAVE, MAT['stucco'])
box("w2_f_c", SX0, SX0+WT, 13.3, 13.8, Z2-0.02, EAVE, MAT['stucco'])
box("w2_f_d", SX0, SX0+WT, 16.3, SY1, Z2-0.02, EAVE, MAT['stucco'])
box("w2_f_t1", SX0, SX0+WT, 1.7, 4.2, Z2+2.5, EAVE, MAT['stucco'])
box("w2_f_t2", SX0, SX0+WT, 13.8, 16.3, Z2+2.5, EAVE, MAT['stucco'])
box("w2_f_t3", SX0, SX0+WT, 4.7, 13.3, Z2+2.7, EAVE, MAT['stucco'])
box("win3", SX0+0.1, SX0+0.12, 1.7, 4.2, Z2+0.05, Z2+2.5, MAT['glass'])
box("win4", SX0+0.1, SX0+0.12, 13.8, 16.3, Z2+0.05, Z2+2.5, MAT['glass'])
slats("scr3", SX0-0.25, 1.6, 4.3, Z2+0.1, Z2+2.55, 15, MAT['teak_v'])
slats("scr4", SX0-0.25, 13.7, 16.4, Z2+0.1, Z2+2.55, 15, MAT['teak_v'])
box("sf_glass", SX0+0.08, SX0+0.10, 4.7, 13.3, Z2, Z2+2.7, MAT['glass'])
for i in range(7):
    y = 4.7 + i*(8.6/6)
    box(f"sf_mul{i}", SX0+0.04, SX0+0.14, y-0.03, y+0.03, Z2, Z2+2.7, MAT['black'])
box("w2_side_l", SX0+WT, SX1-WT, SY0, SY0+WT, Z2-0.02, EAVE, MAT['stucco'])
box("w2_side_r", SX0+WT, SX1-WT, SY1-WT, SY1, Z2-0.02, EAVE, MAT['stucco'])
box("w2_back", SX1-WT, SX1, SY0, SY1, Z2-0.02, EAVE, MAT['stucco'])
box("win_sl", SX0+0.6, SX0+1.4, SY0+0.1, SY0+0.12, Z2+1.6, Z2+2.3, MAT['glass'])
box("win_sr", SX0+0.6, SX0+1.4, SY1-0.12, SY1-0.1, Z2+1.6, Z2+2.3, MAT['glass'])
# (second-floor partitions, floors and furniture are built in interiors())
# ceiling / lights under the roof over the void
box("ceil2", SX0+0.1, SX1-0.1, SY0+0.1, SY1-0.1, EAVE-0.05, EAVE, MAT['white'])
for x in (44.5, 47.0, 49.0):
    for y in (6.0, 9.0, 12.0):
        box(f"dl{x}{y}", x-0.08, x+0.08, y-0.08, y+0.08, EAVE-0.07, EAVE-0.05, MAT['lamp'])
box("cove", HX1-WT-0.16, HX1-WT-0.14, 12.6, 16.6, Z2-0.5, Z2-0.48, MAT['lamp'])
box("cove2", SX1-WT-0.16, SX1-WT-0.14, 5.0, 13.0, EAVE-0.25, EAVE-0.23, MAT['lamp'])
# ground floor ceiling (underside of slab) lights
for x in (43.0, 46.0, 48.5):
    for y in (6.0, 9.0, 12.0):
        box(f"gl{x}{y}", x-0.08, x+0.08, y-0.08, y+0.08, Z2-0.32, Z2-0.30, MAT['lamp'])
# roofs: main hip roof (ridge along Y) + shed roof over the balcony
hip_roof("roof_main", SX0-1.0, SX1+1.0, SY0-1.0, SY1+1.0, EAVE, 30)
box("fascia_soffit", SX0-0.98, SX1+0.98, SY0-0.98, SY1+0.98, EAVE-0.24, EAVE-0.22, MAT['white'])
box("ceil1", HX0+0.1, HX1-0.1, HY0+0.1, HY1-0.1, Z2-0.31, Z2-0.30, MAT['white'])
shed_roof("roof_balcony", 39.4, SX0+0.05, 3.8, 14.1, Z2+2.35, Z2+3.3)
for nm, y in (("bpost_l", 4.1), ("bpost_r", 13.8)):
    box(nm, 39.9, 40.05, y-0.08, y+0.08, Z2, Z2+2.4, MAT['teak'])
box("bbeam", 39.85, 40.1, 3.9, 14.0, Z2+2.2, Z2+2.4, MAT['teak'])
# wall sconces
for y in (2.15, 14.05):
    box(f"sconce{y}", 38.7, 38.9, y-0.05, y+0.05, FFL+1.9, FFL+2.2, MAT['lamp'])

# ------------------------------------------------------------------ entrance garden patio, driveway, parking, guard house
box("patio", 50.0, 55.5, 3.8, 15.8, -0.05, FFL, MAT['trav'])
for i in range(3):
    box(f"pstep{i}", 55.5+0.35*i, 55.85+0.35*i, 5.7, 12.0, -0.05, FFL-0.15*(i+1), MAT['trav'])
box("planter", 51.6, 54.9, 6.7, 13.6, FFL-0.02, FFL+0.5, MAT['concrete_d'])
hedge("planter_hedge", 52.0, 54.5, 8.0, FFL+0.45, r=0.45, seed=21)
hedge("planter_hedge2", 52.0, 54.5, 12.3, FFL+0.45, r=0.45, seed=22)
palm("ppalm_c", 53.2, 10.2, h=5.5, lean=(0.0, 0.03), seed=77)
box("drive", 55.85, 80.0, 5.7, 12.0, -0.04, 0.0, MAT['concrete'])
box("apron", 80.0, 86.0, 5.0, 12.8, -0.04, 0.0, MAT['concrete'])
box("park", 58.7, 65.8, 0.4, 5.5, -0.04, 0.012, MAT['concrete'])
car("car1", 60.0, 3.0, MAT['carpaint'], rot=math.pi/2)
car("car2", 62.3, 3.0, MAT['carpaint2'], rot=math.pi/2)
car("car3", 64.6, 3.0, m_simple("carpaint3", (0.45, 0.08, 0.08, 1), 0.3, 0.7, 0.8), rot=math.pi/2)
for i, x in enumerate((73.3, 69.0, 63.8, 59.0)):
    palm(f"dpalm_l{i}", x, 4.9 if x > 66 else 5.3, h=4.5 + 0.4*i, lean=(0.0, -0.03), fronds=18, seed=600+i)
    palm(f"dpalm_r{i}", x, 12.8, h=4.8 + 0.3*i, lean=(0.0, 0.03), fronds=18, seed=620+i)
palm("bpalm0", 56.5, 2.0, h=8.0, lean=(0.03, -0.03), seed=50)
palm("bpalm1", 56.5, 16.0, h=8.5, lean=(0.03, 0.03), seed=51)
palm("bpalm2", 70.0, 15.5, h=7.0, lean=(0.0, 0.04), seed=52)
box("guard", 74.0, 79.5, 0.4, 6.0, -0.05, 3.0, MAT['stucco_w'])
box("guard_roof", 73.5, 80.0, 0.0, 6.5, 3.0, 3.3, MAT['concrete'])
box("guard_win", 73.98, 74.02, 1.5, 4.5, 1.0, 2.4, MAT['glass'])
box("guard_win2", 75.5, 77.5, 5.98, 6.02, 1.0, 2.4, MAT['glass'])
box("guard_door", 78.0, 78.9, 5.98, 6.04, 0.0, 2.2, MAT['teak_v'])
GO = 6.6 if VIEW == "access" else 0.0   # gate slid open along the wall
for i in range(36):
    y = 5.75 + i*0.18 + GO
    box(f"gate{i}", 79.75, 79.85, y, y+0.1, 0.1, 2.3, MAT['teak_v'])
box("gate_fr_t", 79.72, 79.88, 5.7+GO, 12.3+GO, 2.3, 2.4, MAT['black'])
box("gate_fr_b", 79.72, 79.88, 5.7+GO, 12.3+GO, 0.0, 0.1, MAT['black'])
box("gpil_a", 79.5, 80.1, 5.3, 5.7, -0.1, 2.8, MAT['concrete_d'])
box("gpil_b", 79.5, 80.1, 12.3, 12.7, -0.1, 2.8, MAT['concrete_d'])
box("gl_a", 79.6, 80.0, 5.4, 5.6, 2.8, 2.9, MAT['lamp'])
box("gl_b", 79.6, 80.0, 12.4, 12.6, 2.8, 2.9, MAT['lamp'])

# ------------------------------------------------------------------ vegetation in the lot
palm("fpalm0", 8.3, 3.0, h=9.0, lean=(-0.08, 0.02), seed=30)
palm("fpalm1", 8.0, 15.0, h=8.0, lean=(-0.06, 0.05), seed=31)
palm("fpalm2", 23.5, 1.1, h=8.5, lean=(-0.03, -0.06), seed=32)
palm("fpalm3", 26.5, 16.9, h=7.5, lean=(-0.03, 0.06), seed=33)
palm("mpalm0", 30.0, 1.2, h=8.5, lean=(-0.05, -0.04), seed=40)
palm("mpalm1", 35.5, 1.0, h=9.5, lean=(-0.04, -0.04), seed=41)
palm("mpalm2", 30.0, 16.8, h=8.0, lean=(-0.05, 0.05), seed=42)
palm("mpalm3", 35.5, 17.0, h=7.0, lean=(-0.04, 0.05), seed=43)
palm("mpalm4", 40.0, 16.9, h=9.0, lean=(-0.02, 0.05), seed=44)
palm("mpalm5", 40.0, 1.1, h=8.0, lean=(-0.02, -0.05), seed=45)
canopy_tree("tree_a", 31.5, 2.4, h=4.0, r=1.8, seed=1)
canopy_tree("tree_b", 31.5, 15.6, h=4.0, r=1.8, seed=2)
hedge("mhedge_l", 28.0, 41.0, 0.6, 0.0, r=0.5, seed=3)
hedge("mhedge_r", 28.0, 41.0, 17.4, 0.0, r=0.5, seed=4)
for i in range(8):
    bush(f"pathbush_l{i}", 28.5 + i*1.3, 5.3, r=0.5, seed=140+i)
    bush(f"pathbush_r{i}", 28.5 + i*1.3, 14.6, r=0.5, seed=160+i)
hedge("bhedge_back", 50.5, 55.0, 0.8, 0.0, r=0.45, seed=5)
hedge("bhedge_back2", 50.5, 55.0, 17.2, 0.0, r=0.45, seed=6)
# neighbours
rn = random.Random(99)
for i in range(140):
    x = rn.uniform(10, 110); y = rn.choice([rn.uniform(-90, -3), rn.uniform(21, 110)])
    if rn.random() < 0.55:
        palm(f"npalm{i}", x, y, h=rn.uniform(5, 10), lean=(rn.uniform(-0.08, 0.08), rn.uniform(-0.08, 0.08)), fronds=12, seed=200+i)
    else:
        canopy_tree(f"ntree{i}", x, y, h=rn.uniform(3.5, 6.5), r=rn.uniform(2, 3.5), seed=300+i, subdiv=3)
for i in range(90):
    x = rn.uniform(8, 110); y = rn.choice([rn.uniform(-90, -2), rn.uniform(20, 110)])
    bush(f"nbush{i}", x, y, r=rn.uniform(0.7, 1.6), seed=400+i, subdiv=3)
box("nh1", 40, 52, -14, -4, -0.05, 3.2, MAT['stucco_w']); hip_roof("nh1r", 39.2, 52.8, -14.8, -3.2, 3.2, 22)
box("nh2", 44, 58, 24, 34, -0.05, 3.0, MAT['offwhite']); hip_roof("nh2r", 43.2, 58.8, 23.2, 34.8, 3.0, 22)
box("nh3", 60, 70, -30, -22, -0.05, 2.8, MAT['stucco']); box("nh3r", 59.5, 70.5, -30.5, -21.5, 2.8, 3.1, MAT['concrete_d'])


# ------------------------------------------------------------------ interiors (per plans: nivel 1 / nivel 2)
MAT['bathtile'] = m_simple("bathtile", (0.80, 0.80, 0.78, 1), 0.3, 0.0, 0.4)
MAT['woodfloor'] = m_wood("woodfloor", (0.55, 0.36, 0.20, 1), plank=(0.12, 1.2), dirx='Y')
MAT['linen'] = m_simple("linen", (0.90, 0.88, 0.84, 1), 0.9)
MAT['porcelain'] = m_simple("porcelain", (0.95, 0.95, 0.95, 1), 0.15, 0.0, 0.6)
MAT['closetwood'] = m_wood("closetwood", (0.35, 0.22, 0.12, 1), dirx='Z')
LABELS = {1: [], 2: []}

def wall(name, x0, x1, y0, y1, z0, z1, gap=None, axis='y'):
    """interior partition; gap=(a,b) leaves a door opening along the wall's long axis"""
    if gap is None:
        return box(name, x0, x1, y0, y1, z0, z1, MAT['white'])
    a, b = gap
    if axis == 'y':   # wall runs along Y (x0..x1 thin)
        box(name+"_a", x0, x1, y0, a, z0, z1, MAT['white']); box(name+"_b", x0, x1, b, y1, z0, z1, MAT['white'])
        box(name+"_h", x0, x1, a, b, z0+2.1, z1, MAT['white'])
    else:             # wall runs along X
        box(name+"_a", x0, a, y0, y1, z0, z1, MAT['white']); box(name+"_b", b, x1, y0, y1, z0, z1, MAT['white'])
        box(name+"_h", a, b, y0, y1, z0+2.1, z1, MAT['white'])

def bed(name, x, y, z, w=1.6, l=2.0, head='+x'):
    # bed centred at x,y; head side along given direction
    box(name+"_base", x-l/2, x+l/2, y-w/2, y+w/2, z, z+0.35, MAT['closetwood'])
    box(name+"_matt", x-l/2+0.05, x+l/2-0.05, y-w/2+0.05, y+w/2-0.05, z+0.35, z+0.55, MAT['linen'])
    box(name+"_cover", x-l/2+0.05, x+l/2-0.8, y-w/2+0.05, y+w/2-0.05, z+0.55, z+0.62, MAT['cushion'])
    hx = x+l/2 if head == '+x' else x-l/2
    box(name+"_head", hx-0.06, hx+0.06, y-w/2-0.1, y+w/2+0.1, z, z+1.1, MAT['closetwood'])
    px = x+l/2-0.45 if head == '+x' else x-l/2+0.45
    for py in (y-w/4, y+w/4):
        box(name+f"_pil{py:.1f}", px-0.25, px+0.25, py-w/4+0.08, py+w/4-0.08, z+0.55, z+0.68, MAT['white'])
    for sy in (y-w/2-0.35, y+w/2+0.35):
        box(name+f"_nt{sy:.1f}", hx-0.5, hx, sy-0.22, sy+0.22, z, z+0.5, MAT['teak'])

def toilet(name, x, y, z, rot_x=False):
    box(name+"_tank", x-0.2, x+0.2, y-0.1, y+0.1, z, z+0.75, MAT['porcelain'])
    cyl(name+"_bowl", x, y+0.32, z, z+0.4, 0.2, MAT['porcelain'], segs=16)

def vanity(name, x0, x1, y0, y1, z):
    box(name+"_c", x0, x1, y0, y1, z, z+0.85, MAT['closetwood'])
    box(name+"_top", x0-0.02, x1+0.02, y0-0.02, y1+0.02, z+0.85, z+0.88, MAT['white'])
    cyl(name+"_basin", (x0+x1)/2, (y0+y1)/2, z+0.88, z+0.98, 0.2, MAT['porcelain'], segs=20)

def shower(name, x0, x1, y0, y1, z, glass_axis='x'):
    box(name+"_tray", x0, x1, y0, y1, z, z+0.06, MAT['bathtile'])
    if glass_axis == 'x':
        box(name+"_glass", x1-0.02, x1, y0, y1, z+0.06, z+2.0, MAT['glass_rail'])
    else:
        box(name+"_glass", x0, x1, y1-0.02, y1, z+0.06, z+2.0, MAT['glass_rail'])

def closet_run(name, x0, x1, y0, y1, z, h=2.1):
    box(name, x0, x1, y0, y1, z, z+h, MAT['closetwood'])
    box(name+"_shelf", x0-0.01, x1+0.01, y0-0.01, y1+0.01, z+1.0, z+1.03, MAT['linen'])

def appliance(name, x0, x1, y0, y1, z, mat=None):
    box(name, x0, x1, y0, y1, z, z+0.85, mat or MAT['white'])
    box(name+"_door", x0-0.01, x1+0.01, y0-0.01, y1+0.01, z+0.2, z+0.7, MAT['black'])

def stairs(name, x0, y0, y1, z0, z1, n=14, width=1.7, dir_y=1):
    rise = (z1-z0)/n; run = (y1-y0)/n
    for i in range(n):
        ya = y0 + i*run if dir_y > 0 else y1 - (i+1)*run
        box(f"{name}_s{i}", x0, x0+width, ya, ya+run, z0, z0+rise*(i+1), MAT['floor2'])

# ---------- NIVEL 1 ----------
Z1, W1 = FFL, Z2-0.30
# bedroom wood floors, bath tile floors
box("fl_d1", HX0+WT, 46.0, 1.8, 4.7, Z1+0.012, Z1+0.02, MAT['woodfloor'])
box("fl_d2", HX0+WT, 46.0, 13.3, 16.2, Z1+0.012, Z1+0.02, MAT['woodfloor'])
box("fl_b1", HX0+WT, 46.2, HY0+WT, 1.8, Z1+0.012, Z1+0.02, MAT['bathtile'])
box("fl_b2", HX0+WT, 46.2, 16.2, HY1-WT, Z1+0.012, Z1+0.02, MAT['bathtile'])
box("fl_wc1", 46.0, 47.2, HY0+WT, 4.7, Z1+0.012, Z1+0.02, MAT['woodfloor'])
box("fl_wc2", 46.0, 47.2, 13.3, HY1-WT, Z1+0.012, Z1+0.02, MAT['woodfloor'])
box("fl_serv", 47.2, HX1-WT, HY0+WT, 4.7, Z1+0.012, Z1+0.02, MAT['bathtile'])
box("fl_bano", 47.2, 49.0, 16.6, HY1-WT, Z1+0.012, Z1+0.02, MAT['bathtile'])
# partitions
wall("n1_d1_bath", HX0+WT, 46.2, 1.8-0.06, 1.8+0.06, Z1, W1, gap=(45.0, 45.9), axis='x')
wall("n1_d1_cl", 46.0-0.06, 46.0+0.06, HY0+WT, 4.7, Z1, W1, gap=(3.7, 4.6))
wall("n1_cl_serv", 47.2-0.06, 47.2+0.06, HY0+WT, 4.7, Z1, W1, gap=(2.9, 3.8))
wall("n1_p1", HX0+WT, 47.2, 4.7-0.06, 4.7+0.06, Z1, W1, gap=(46.2, 47.1), axis='x')
wall("n1_serv_a", 47.2, HX1-WT, 1.4-0.06, 1.4+0.06, Z1, W1, gap=(48.7, 49.6), axis='x')
wall("n1_serv_b", 47.2, HX1-WT, 2.9-0.06, 2.9+0.06, Z1, W1, gap=(48.7, 49.6), axis='x')
wall("n1_serv_c", 47.2, 49.0, 4.7-0.06, 4.7+0.06, Z1, W1)
wall("n1_alac_a", 47.2, 49.0, 6.7-0.06, 6.7+0.06, Z1, W1)
wall("n1_alac_b", 49.0-0.06, 49.0+0.06, 4.7, 6.7, Z1, W1, gap=(5.3, 6.2))
wall("n1_kit", 46.0-0.06, 46.0+0.06, 4.7, 7.1, Z1, W1, gap=(6.0, 7.0))
wall("n1_d2_bath", HX0+WT, 46.2, 16.2-0.06, 16.2+0.06, Z1, W1, gap=(45.0, 45.9), axis='x')
wall("n1_d2_cl", 46.0-0.06, 46.0+0.06, 13.3, HY1-WT, Z1, W1, gap=(13.4, 14.3))
wall("n1_cl2_st", 47.2-0.06, 47.2+0.06, 13.3, HY1-WT, Z1, W1, gap=(16.7, 17.6))
wall("n1_p2", HX0+WT, 46.0, 13.3-0.06, 13.3+0.06, Z1, W1, gap=(43.5, 44.4), axis='x')
wall("n1_p2b", 47.2, HX1-WT, 13.3-0.06, 13.3+0.06, Z1, W1, gap=(47.3, 48.0), axis='x')
wall("n1_linos", 47.2, 49.0, 16.6-0.06, 16.6+0.06, Z1, W1)
wall("n1_bano", 49.0-0.06, 49.0+0.06, 16.6, HY1-WT, Z1, W1, gap=(16.7, 17.5))
# bedroom 1 & 2
bed("bed1", 43.5, 3.25, Z1, head='+x'); bed("bed2", 43.5, 14.75, Z1, head='+x')
closet_run("cl1", 46.1, 47.1, HY0+WT+0.05, 1.3, Z1); closet_run("cl1b", 46.1, 46.6, 1.3, 3.6, Z1, h=1.6)
closet_run("cl2", 46.1, 47.1, 16.7, HY1-WT-0.05, Z1); closet_run("cl2b", 46.1, 46.6, 14.4, 16.7, Z1, h=1.6)
# bathrooms strip Y 0.1..1.8 : shower X 41.75..43.2, vanity 43.3..44.5, light well 44.5..45.2, toilet 45.2..46.2
shower("sh1", HX0+WT, 43.2, HY0+WT, 1.8-0.06, Z1, glass_axis='x'); vanity("van1", 43.4, 44.5, HY0+WT, 0.75, Z1)
box("vano1", 44.5, 45.2, HY0+WT, 1.74, Z1+0.02, Z1+0.1, MAT['grass']); bush("vb1", 44.85, 0.9, r=0.35, seed=700, z=Z1+0.1)
toilet("wc1", 45.7, HY0+WT+0.1, Z1)
shower("sh2", HX0+WT, 43.2, 16.2+0.06, HY1-WT, Z1, glass_axis='x'); vanity("van2", 43.4, 44.5, 17.25, HY1-WT, Z1)
box("vano2", 44.5, 45.2, 16.26, HY1-WT, Z1+0.02, Z1+0.1, MAT['grass']); bush("vb2", 44.85, 17.1, r=0.35, seed=701, z=Z1+0.1)
toilet("wc2", 45.7, HY1-WT-0.55, Z1)
# service: pila, tendedero, lavandería, alacena
box("pila", 48.6, 49.6, HY0+WT+0.1, 1.2, Z1, Z1+0.85, MAT['concrete_d'])
for i in range(3):
    box(f"tend{i}", 47.4, 49.5, 1.8+i*0.35, 1.82+i*0.35, Z1+1.7, Z1+1.72, MAT['steel'])
appliance("washer", 47.3, 47.9, 3.0, 3.6, Z1); appliance("dryer", 47.3, 47.9, 3.7, 4.3, Z1)
box("laund_top", 47.3, 48.5, 2.95, 4.65, Z1+0.85, Z1+0.9, MAT['white'])
for i in range(4):
    box(f"alac{i}", 47.3, 48.9, 4.8, 5.2, Z1+0.4+i*0.45, Z1+0.43+i*0.45, MAT['closetwood'])
    box(f"alac2_{i}", 47.3, 48.9, 6.2, 6.6, Z1+0.4+i*0.45, Z1+0.43+i*0.45, MAT['closetwood'])
# kitchen: counter along Y=4.7 wall, island facing comedor
box("kcounter", HX0+WT+0.1, 45.9, 4.78, 5.4, Z1, Z1+0.88, MAT['closetwood'])
box("kcounter_top", HX0+WT+0.08, 45.92, 4.76, 5.42, Z1+0.88, Z1+0.92, MAT['white'])
box("stove", 43.2, 43.9, 4.8, 5.4, Z1+0.92, Z1+0.94, MAT['black'])
appliance("fridge", 45.2, 45.9, 5.5, 6.3, Z1, MAT['steel']); box("fridge_up", 45.2, 45.9, 5.5, 6.3, Z1+0.85, Z1+1.9, MAT['steel'])
box("island", 42.3, 44.8, 6.35, 7.05, Z1, Z1+0.88, MAT['concrete_d'])
box("island_top", 42.2, 44.9, 6.3, 7.1, Z1+0.88, Z1+0.93, MAT['white'])
for i in range(3):
    cyl(f"kstool{i}", 42.8 + i*0.8, 7.45, Z1, Z1+0.7, 0.17, MAT['teak'])
# stairs (sube) X 48..49.7, Y 13.4..16 rising toward +Y
stairs("st1", 48.0, 13.45, 16.5, Z1, Z2, n=16, width=1.7, dir_y=1)
box("linos", 47.3, 48.0, 13.4, 16.5, Z1, Z1+2.1, MAT['closetwood'])
# baño visitas
toilet("wc3", 49.4, 16.75, Z1); vanity("van3", 47.4, 48.3, 17.1, HY1-WT, Z1)
# sala TV wall + plants
box("tvwall", 45.5, 47.8, 11.95, 12.05, Z1, Z1+2.4, MAT['darkwood']); box("tv", 46.0, 47.3, 11.9, 11.95, Z1+0.9, Z1+1.7, MAT['black'])
for k, (x, y) in enumerate(((42.0, 12.9), (49.3, 7.3))):
    cyl(f"pot{k}", x, y, Z1, Z1+0.45, 0.22, MAT['terracotta']); bush(f"potb{k}", x, y, r=0.4, seed=710+k, z=Z1+0.45)
LABELS[1] = [("dormitorio 1", 43.5, 3.2), ("walk-in", 46.6, 2.4), ("baño", 43.9, 1.0), ("pila", 49.1, 0.7), ("tendedero", 48.4, 2.15),
             ("lavandería", 48.5, 3.8), ("alacena", 48.1, 5.7), ("entrada", 49.5, 5.1), ("cocina", 43.8, 5.9), ("comedor", 45.8, 8.2),
             ("sala", 44.8, 10.5), ("jardín", 48.8, 10.1), ("dormitorio 2", 43.5, 14.8), ("walk-in", 46.6, 15.6), ("baño", 43.9, 17.0),
             ("sube", 48.8, 14.9), ("linos", 47.6, 15.0), ("baño", 48.2, 17.3), ("terraza", 40.0, 8.0), ("patio-jardín", 53.2, 10.0)]

# ---------- NIVEL 2 ----------
Zb, W2 = Z2, EAVE
box("fl2_all", SX0+WT, SX1-WT, SY0+WT, SY1-WT, Zb-0.01, Zb+0.02, MAT['floor2'])
box("fl2_d4", SX0+WT, 47.5, 1.7, 4.7, Zb+0.012, Zb+0.025, MAT['woodfloor'])
box("fl2_d3", SX0+WT, 47.5, 13.3, 16.3, Zb+0.012, Zb+0.025, MAT['woodfloor'])
box("fl2_b4", SX0+WT, 47.5, SY0+WT, 1.7, Zb+0.012, Zb+0.025, MAT['bathtile'])
box("fl2_b3", SX0+WT, 47.5, 16.3, SY1-WT, Zb+0.012, Zb+0.025, MAT['bathtile'])
# void over sala: remove floor there (X 44.1..49.75, Y 6.9..11.7) -> rebuild floor as pieces
bpy.data.objects.remove(bpy.data.objects["fl2_all"], do_unlink=True)
for nm, a in (("fl2_a", (SX0+WT, SX1-WT, SY0+WT, 6.9)), ("fl2_b", (SX0+WT, SX1-WT, 11.7, SY1-WT)), ("fl2_c", (SX0+WT, 44.1, 6.9, 11.7))):
    box(nm, *a, Zb-0.01, Zb+0.02, MAT['floor2'])
# slab2 also needs the void: rebuild slab2 as pieces
bpy.data.objects.remove(bpy.data.objects["slab2"], do_unlink=True)
for nm, a in (("slab2_a", (HX0+WT, HX1-WT, HY0+WT, 6.9)), ("slab2_b", (HX0+WT, HX1-WT, 11.7, HY1-WT)), ("slab2_c", (HX0+WT, 44.1, 6.9, 11.7))):
    box(nm, *a, Z2-0.3, Z2, MAT['concrete'])
bpy.data.objects.remove(bpy.data.objects["ceil1"], do_unlink=True)
for nm, a in (("ceil1_a", (HX0+0.1, HX1-0.1, HY0+0.1, 6.9)), ("ceil1_b", (HX0+0.1, HX1-0.1, 11.7, HY1-0.1)), ("ceil1_c", (HX0+0.1, 44.1, 6.9, 11.7))):
    box(nm, *a, Z2-0.31, Z2-0.30, MAT['white'])
railing("void_rail", [(44.1, 6.95), (44.1, 11.65)], Zb+0.02, h=1.05)
railing("void_rail2", [(44.1, 6.95), (49.7, 6.95)], Zb+0.02, h=1.05)
railing("void_rail3", [(44.1, 11.65), (49.7, 11.65)], Zb+0.02, h=1.05)
# partitions nivel 2
wall("n2_d4_bath", SX0+WT, 47.5, 1.7-0.06, 1.7+0.06, Zb, W2, gap=(46.3, 47.2), axis='x')
wall("n2_d4_cl", 47.5-0.06, 47.5+0.06, SY0+WT, 4.7, Zb, W2, gap=(3.7, 4.6))
wall("n2_p3", SX0+WT, SX1-WT, 4.7-0.06, 4.7+0.06, Zb, W2, gap=(43.0, 43.9), axis='x')
wall("n2_cl", 48.7-0.06, 48.7+0.06, SY0+WT, 4.7, Zb, W2)
wall("n2_closet", 47.5-0.06, 47.5+0.06, 4.7, 6.9, Zb, W2, gap=(5.5, 6.4))
wall("n2_d3_bath", SX0+WT, 47.5, 16.3-0.06, 16.3+0.06, Zb, W2, gap=(46.3, 47.2), axis='x')
wall("n2_d3_cl", 47.5-0.06, 47.5+0.06, 13.3, SY1-WT, Zb, W2, gap=(13.4, 14.3))
wall("n2_p4", SX0+WT, SX1-WT, 13.3-0.06, 13.3+0.06, Zb, W2, gap=(43.0, 43.9), axis='x')
wall("n2_cl3", 48.7-0.06, 48.7+0.06, 13.3, SY1-WT, Zb, W2)
wall("n2_st", 47.5-0.06, 47.5+0.06, 11.7, 13.3, Zb, W2)
bed("bed4", 44.6, 3.2, Zb, head='+x'); bed("bed3", 44.6, 14.8, Zb, head='+x')
closet_run("cl4", 47.6, 48.6, SY0+WT+0.05, 1.3, Zb); closet_run("cl4b", 47.6, 48.1, 1.3, 3.6, Zb, h=1.6)
closet_run("cl3", 47.6, 48.6, 16.7, SY1-WT-0.05, Zb); closet_run("cl3b", 47.6, 48.1, 14.4, 16.7, Zb, h=1.6)
closet_run("closet_gen", 47.6, 49.6, 4.8, 5.4, Zb)
shower("sh4", SX0+WT, 44.4, SY0+WT, 1.7-0.06, Zb, glass_axis='x'); vanity("van4", 44.6, 45.7, SY0+WT, 0.75, Zb)
box("vano4", 45.7, 46.4, SY0+WT, 1.64, Zb+0.03, Zb+0.1, MAT['grass']); toilet("wc4", 46.9, SY0+WT+0.1, Zb)
shower("sh3", SX0+WT, 44.4, 16.3+0.06, SY1-WT, Zb, glass_axis='x'); vanity("van5", 44.6, 45.7, 17.25, SY1-WT, Zb)
box("vano3", 45.7, 46.4, 16.36, SY1-WT, Zb+0.03, Zb+0.1, MAT['grass']); toilet("wc5", 46.9, SY1-WT-0.55, Zb)
# stair well opening in the level-2 floor over the stairs (X 48..49.7, Y 13.4..16.5)
bpy.data.objects.remove(bpy.data.objects["fl2_b"], do_unlink=True)
for nm, a in (("fl2_b1", (SX0+WT, 48.0, 11.7, SY1-WT)), ("fl2_b2", (48.0, SX1-WT, 16.5, SY1-WT)), ("fl2_b3", (49.7, SX1-WT, 11.7, 16.5)), ("fl2_b4", (48.0, 49.7, 11.7, 13.4))):
    box(nm, *a, Zb-0.01, Zb+0.02, MAT['floor2'])
for nm in ("slab2_b", "ceil1_b"):
    bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
for nm, a in (("slab2_b1", (HX0+WT, 48.0, 11.7, HY1-WT)), ("slab2_b2", (48.0, HX1-WT, 16.5, HY1-WT)), ("slab2_b3", (49.7, HX1-WT, 11.7, 16.5)), ("slab2_b4", (48.0, 49.7, 11.7, 13.4))):
    box(nm, *a, Z2-0.3, Z2, MAT['concrete'])
for nm, a in (("ceil1_b1", (HX0+0.1, 48.0, 11.7, HY1-0.1)), ("ceil1_b2", (48.0, HX1-0.1, 16.5, HY1-0.1)), ("ceil1_b3", (49.7, HX1-0.1, 11.7, 16.5)), ("ceil1_b4", (48.0, 49.7, 11.7, 13.4))):
    box(nm, *a, Z2-0.31, Z2-0.30, MAT['white'])
railing("st_rail", [(48.0, 13.4), (48.0, 16.5)], Zb+0.02, h=1.0)
# lounge chairs at the corridor facing the void
box("ldesk", 42.95, 43.5, 8.6, 10.2, Zb, Zb+0.75, MAT['teak'])
LABELS[2] = [("dormitorio 4", 44.6, 3.2), ("walk-in", 48.1, 2.4), ("baño", 45.1, 0.95), ("closet", 48.6, 5.1), ("vacío sobre sala", 47.0, 9.3),
             ("dormitorio 3", 44.6, 14.8), ("walk-in", 48.1, 16.4), ("baño", 45.1, 17.1), ("baja", 48.9, 13.9), ("balcón", 40.7, 9.0), ("terraza", 42.1, 3.0)]

# ------------------------------------------------------------------ cutaway for plan views
CUT = None
if VIEW == 'plan1':
    CUT = FFL + 2.3
elif VIEW == 'plan2':
    CUT = Z2 + 2.3
if CUT is not None:
    veg_mats = {'leaf', 'palmleaf', 'bush', 'trunk', 'grasshair', 'grassground'}
    # clear tall vegetation and the neighbour house that would hide the interiors
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH': continue
        if ob.name.startswith(('nh1', 'nh2')) or (VIEW == 'plan2' and ob.name.startswith(('roof_balcony', 'bbeam', 'bpost'))):
            bpy.data.objects.remove(ob, do_unlink=True); continue
        if ob.data.materials and ob.data.materials[0].name in ('leaf', 'palmleaf', 'trunk'):
            bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            xs = [v.x for v in bb]; ys = [v.y for v in bb]
            if max(xs) > 28 and min(xs) < 62 and max(ys) > -25 and min(ys) < 30:
                bpy.data.objects.remove(ob, do_unlink=True)
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH' or ob.data.users > 1 or ob.modifiers:
            continue
        if ob.data.materials and ob.data.materials[0].name in veg_mats:
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
        if max(xs) < 38.0 or min(xs) > 56.5 or max(ys) < -1.2 or min(ys) > 19.2:
            continue
        if min(zs) >= CUT - 0.001:
            bpy.data.objects.remove(ob, do_unlink=True)
        elif max(zs) > CUT:
            for v in ob.data.vertices:
                if v.co.z > CUT: v.co.z = CUT
    # soft top on cut walls: nothing else needed

# ------------------------------------------------------------------ world, camera, render (shared tail with new cameras)
tail = open(f"{HERE}/tail2.py").read()
tail = tail.replace("set_cam((26.7, 3.5, 1.75), (44.0, 11.6, 3.3), lens=24)", "set_cam((23.0, 7.6, 2.0), (44.5, 10.4, 4.6), lens=30)")
tail = tail.replace("set_cam((26.7, 3.0, 1.75), (44.0, 11.4, 3.3), lens=24)", "set_cam((23.0, 7.6, 2.0), (44.5, 10.4, 4.6), lens=30)")
tail = tail.replace("set_cam((40.6, 9.6, Z2+2.1), (14.0, 6.0, -1.2), lens=20, level=False)", "set_cam((40.3, 9.2, Z2+1.75), (12.0, 8.0, -1.0), lens=20, level=False)")
tail = tail.replace("set_cam((-30.0, -34.0, 36.0), (37.0, 9.0, 0.0), lens=38, level=False)", "set_cam((-28.0, -36.0, 38.0), (36.0, 9.0, 0.0), lens=38, level=False)")
tail = tail.replace("elif VIEW == 'street':", "elif VIEW == 'access':\n    set_cam((79.2, 9.1, 1.75), (54.0, 9.4, 3.8), lens=32)\nelif VIEW == 'plan1':\n    set_cam((30.5, -5.0, 25.0), (46.4, 9.0, FFL+0.3), lens=45, level=False)\nelif VIEW == 'plan2':\n    set_cam((30.5, -5.0, 28.5), (46.4, 9.0, Z2+0.3), lens=45, level=False)\nelif VIEW == 'street':")
tail = tail.replace("sky.sun_rotation = math.radians(225 if VIEW != 'pool' else 60)", "sky.sun_rotation = math.radians({'pool': 60, 'access': 35}.get(VIEW, 225))\n    if VIEW in ('plan1', 'plan2'):\n        sky.sun_elevation = math.radians(48); sky.sun_rotation = math.radians(200)")
exec(tail)
# ---- room labels on plan views
if VIEW in ('plan1', 'plan2'):
    from bpy_extras.object_utils import world_to_camera_view
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(OUT).convert("RGBA")
    W_, H_ = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    fs = max(13, int(H_ * 0.0145))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fs)
    zl = (FFL if VIEW == 'plan1' else Z2) + 0.05
    for text, lx, ly in LABELS[1 if VIEW == 'plan1' else 2]:
        p = world_to_camera_view(scene, camob, Vector((lx, ly, zl)))
        px, py = p.x * W_, (1 - p.y) * H_
        tw = dr.textlength(text, font=font); th = fs * 1.25
        dr.rounded_rectangle((px - tw/2 - 7, py - th/2 - 3, px + tw/2 + 7, py + th/2 + 3), radius=6, fill=(255, 255, 255, 215))
        dr.text((px - tw/2, py - th/2 + 1), text, font=font, fill=(43, 42, 40, 255))
    Image.alpha_composite(im, ov).convert("RGB").save(OUT)
    print("LABELS drawn", OUT)
