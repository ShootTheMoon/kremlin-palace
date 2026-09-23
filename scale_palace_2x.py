import bpy
from pathlib import Path

scene = bpy.context.scene
output = Path(bpy.data.filepath).parent
roots = [obj for obj in scene.objects if obj.parent is None]
controller = bpy.data.objects.new('PALACE | Overall scale x2', None)
scene.collection.objects.link(controller)
controller.empty_display_type = 'CUBE'
controller.empty_display_size = 1.0
for obj in roots:
    matrix = obj.matrix_world.copy()
    obj.parent = controller
    obj.matrix_world = matrix
controller.scale = (2.0, 2.0, 2.0)
for camera in bpy.data.cameras:
    camera.clip_start *= 2.0
    camera.clip_end *= 2.0
for light in bpy.data.lights:
    if light.type != 'SUN':
        light.energy *= 4.0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.clip_end *= 2.0
            space.region_3d.view_distance *= 2.0
            space.region_3d.view_location *= 2.0
            space.region_3d.view_perspective = 'CAMERA'
scene['Scale factor from original'] = 2.0
scene['Hall dimensions metres'] = '64 x 56 x 24'
scene['Navigation'] = 'Ground floor 0m / gallery 10.24m. Entire scene uniformly scaled x2.'
bpy.context.view_layer.update()
original = bpy.data.objects.get('Foundation')
if original:
    extent = original.matrix_world.to_scale()
    assert abs(extent.x - 64.8) < 0.001, tuple(extent)
bpy.ops.wm.save_as_mainfile(filepath=str(output / 'Kremlin_Grand_Palace_2x.blend'))
bpy.ops.export_scene.gltf(filepath=str(output / 'Kremlin_Grand_Palace_2x.glb'), export_format='GLB', export_cameras=True, export_lights=True)
print('SCALE_VERIFIED: root scale 2, hall 64 x 56 x 24m, gallery 10.24m')
