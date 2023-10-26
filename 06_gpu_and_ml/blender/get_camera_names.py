import bpy
import sys
import os
from pathlib import Path

for obj in bpy.data.objects:
    if obj.type == "CAMERA":
        print (f"CSKAM:{obj.name}:CSKAM")