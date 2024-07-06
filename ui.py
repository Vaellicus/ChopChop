import bpy
import sys
import os


# Get the current directory of the script being run
current_dir = os.path.dirname(os.path.realpath(__file__))

# Add the current directory to the Python path
if current_dir not in sys.path:
    sys.path.append(current_dir)

import operators

class SimplePanel(bpy.types.Panel):
    bl_label = "ChopChop Addon"
    bl_idname = "OBJECT_PT_simple_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ChopChop'


    def draw(self, context):
        #TODO: Change UI settings, shading type to "object" mode so the colors will show in the 3d viwer
        layout = self.layout
        row = layout.row()
        row.label(text="Import an object to chop")
        row = layout.row()
        row.prop(context.scene.mesh_importer_tool, "import_object")
        row = layout.row()
        row.label(text="Select an object to chop")
        row = layout.row()
        row.prop(context.scene.mesh_selector_tool, "selected_object")
        row = layout.row()
        row.label(text="Height of the model:")
        row = layout.row()
        row.prop(context.scene, "model_height", text="")
        row.label(text="cm")
        row = layout.row()
        row.operator("object.set_drawing")
        row = layout.row()
        row.label(text="Thickness of the cut border:")
        row = layout.row()
        row.prop(context.scene, "border_thickness")
        row.label(text="cm")
        row = layout.row()
        row.operator("object.chop_obj")
        row = layout.row()
        row.operator("object.chopit")
        row = layout.row()
        row.label(text="Select a folder to export")
        row = layout.row()
        row.prop(context.scene.folder_selector_tool, "export_folder")
        row = layout.row()
        row.operator("object.export_all_meshes")
        row = layout.row()
        row.label(text="Thickness of the model:")
        row = layout.row()
        row.prop(context.scene, "shell_thickness")
        row.label(text="cm")
        row = layout.row()
        row.operator("object.make_hollow")
        row = layout.row()
        row.label(text="Smalles dimension of the Printer:")
        row = layout.row()
        row.prop(context.scene, "min_printer_dim")
        row.label(text="cm")
        row = layout.row()
        row.operator("object.cubit")

      

def register():

    bpy.utils.register_class(SimplePanel)
    

def unregister():

    bpy.utils.unregister_class(SimplePanel)

