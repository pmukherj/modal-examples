import bpy
import sys
import os
from pathlib import Path


for obj in bpy.data.objects:
    if obj.type == "CAMERA":
        if (obj.hide_render):
            print (f"CSKAM:{obj.name}:CSKAM")
            continue
    obj.hide_render = obj.hide_get()