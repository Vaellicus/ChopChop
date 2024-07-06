import sys
import os

# Get the current directory of the script being run
current_dir = os.path.dirname(os.path.realpath(__file__))

# Add the current directory to the Python path
if current_dir not in sys.path:
    sys.path.append(current_dir)

from . import operators, ui

bl_info = {
    "name": "ChopChop Addon",
    "author": "Marco De Rossi Estrada",
    "version": (1, 0),
    "blender": (4, 00, 0),
    "location": "View3D > UI",
    "description": "Cut a large mesh into smaller pieces",
    "category": "Object"
}

def register():
    operators.register()
    ui.register()

def unregister():
    operators.unregister()
    ui.unregister()

if __name__ == "__main__":
    register()