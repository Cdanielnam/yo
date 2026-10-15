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
