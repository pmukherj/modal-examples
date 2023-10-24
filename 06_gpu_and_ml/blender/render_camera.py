import bpy
import sys
import os
from pathlib import Path

def enable_gpus(device_type, use_cpus=False):
    preferences = bpy.context.preferences
    cycles_preferences = preferences.addons["cycles"].preferences
    cycles_preferences.refresh_devices()
    devices = cycles_preferences.devices

    if not devices:
        raise RuntimeError("Unsupported device type")

    activated_gpus = []
    for device in devices:
        if device.type == "CPU":
            device.use = use_cpus
            print ("WARNING: No GPU found. Using CPU!")
        else:
            device.use = True
            activated_gpus.append(device.name)

            print('activated gpu', device.name)


    cycles_preferences.compute_device_type = device_type
    bpy.context.scene.cycles.device = "GPU"

    return next(iter(activated_gpus), None)

filename = Path(bpy.data.filepath)
filename = filename.stem
renderPath = bpy.path.abspath("//Renders\\" + filename + "\\")
print('Render path: ' + renderPath)

for obj in bpy.data.objects:
    if obj.type == "CAMERA":
        if (obj.hide_render):
            print (f"CSKAM:{obj.name}:CSKAM")
            continue
    obj.hide_render = obj.hide_get()


for obj in bpy.data.objects:
    if obj.type != "CAMERA":
        continue
    
    if obj.hide_render == True:
        continue

    print(f'SKETUP:{obj.name}:SKETUP')
    sys.stdout.flush()
    bpy.context.scene.camera = obj
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_percentage = 5

    bpy.context.scene.render.filepath = renderPath + "\\" + obj.name
    print (f"RENSKDERING:{obj.name}:RENSKDERING:")
    sys.stdout.flush()
    bpy.ops.render.render(animation=False, write_still=True)
    print(f'DOSKNE:{obj.name}:DOSKNE')
    sys.stdout.flush()