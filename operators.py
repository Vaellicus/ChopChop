import bpy
import sys
import os
import itertools
import curve_cut
import make_hollow
import cubit

# Get the current directory of the script being run
current_dir = os.path.dirname(os.path.realpath(__file__))

# Add the current directory to the Python path
if current_dir not in sys.path:
    sys.path.append(current_dir)


class ImportMeshPropertiesGroup(bpy.types.PropertyGroup):
    # Define properties here

    def import_into_scene(self, context):
        # Get the path to the object file
        obj_path = bpy.path.abspath(self.import_object)
        # Import the object into the scene
        bpy.ops.wm.obj_import(filepath = obj_path)
        # Set the selected object to the newly imported object
        imported_obj = bpy.context.active_object
        context.scene.mesh_selector_tool.selected_object = imported_obj

    def setup_mesh(self, context):
        #deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        obj = context.scene.mesh_selector_tool.selected_object
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
        bpy.ops.object.location_clear(clear_delta=False)
        x_dim, y_dim, z_dim = obj.dimensions.x, obj.dimensions.y, obj.dimensions.z
        largest_dim = max(x_dim, y_dim, z_dim)
        if z_dim != largest_dim:
            if x_dim == largest_dim:
                bpy.ops.transform.rotate(value=1.5708, orient_axis='Y', orient_type='GLOBAL')
            elif y_dim == largest_dim:
                bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL')
                
        # Move the object to the origin
        
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        lowest_point = min([v.co.z for v in obj.data.vertices])
        obj.location.z -= lowest_point
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        #update model_height prop with height of model
        bpy.context.scene.model_height = obj.dimensions.z
        bpy.context.view_layer.update()
                
    
    def update_functions(self, context):
        if not bpy.context.scene.mesh_importer_tool.import_object:
            return
        self.import_into_scene(context)
        bpy.context.scene.mesh_importer_tool.import_object= ""
        self.setup_mesh(context)
        

    import_object: bpy.props.StringProperty(
        name="",
        subtype="FILE_PATH",
        update=update_functions,
        description="Select the mesh to import",
    )  # type: ignore


def set_selected_object_color(self, context):

    selected_obj = self.selected_object
    for obj in context.scene.objects:
        if obj != selected_obj:
            obj.color = (1, 1, 1, 1)  # RGBA
    if selected_obj:
        # Set the viewport display color to blue
        selected_obj.color = (0, 0, 1, 1)  # RGBA



class SelectMeshProperties(bpy.types.PropertyGroup):

    def update_functions(self, context):
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.length_unit = 'CENTIMETERS'
        bpy.context.scene.unit_settings.scale_length = 0.01
        bpy.context.space_data.clip_end = 1000
        
        
        if self.selected_object:
            bpy.context.space_data.shading.color_type = 'OBJECT'
            set_selected_object_color(self, context)
            #update the z_dim prop
            bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            #update the model height tool with the new selected object
            bpy.context.scene.model_height = self.selected_object.dimensions.z
        

    selected_object : bpy.props.PointerProperty(
        name = "",
        type = bpy.types.Object,
        update = update_functions,
    ) # type: ignore


def update_model_height(self, context):
    selected_object = bpy.context.scene.mesh_selector_tool.selected_object
    desired_height = context.scene.model_height


    if selected_object.type == 'MESH':
        current_height = calculate_model_height(selected_object)
        scale_factor = desired_height / current_height if current_height > 0 else 1
        selected_object.scale = [scale_factor * axis for axis in selected_object.scale]

def calculate_model_height(obj):
    # Assuming the object's origin is at its base, and we're only scaling in Z
    dimensions = obj.dimensions
    return dimensions.z

class ModelHeightTool(bpy.types.Operator):
    bl_idname = "object.model_height"
    bl_label = "Set the model height"
    bpy.types.Scene.model_height = bpy.props.FloatProperty(
        description="Set the height of the selected model",
        default=200,  # Default value
        min=10,  # Minimum value
        max=1000.0,  # Maximum value
        precision=1,  # Limit to 1 decimal place
        update=update_model_height  # Link to the update function
    )


class SetDrawOperator(bpy.types.Operator):
    bl_idname = "object.set_drawing"
    bl_label = "New Cut Line"
    bl_description = "Draw a new cut line. You have to select an object first"

    # Define a list of 5 bright colors (RGBA)
    colors = itertools.cycle([
        (1, 0, 0, 1),  # Red
        (0, 1, 0, 1),  # Green
        (1, 1, 0, 1),  # Yellow
        (1, 0, 1, 1)   # Magenta
    ])

    @classmethod
    def poll(cls, context):
        if context.scene.mesh_selector_tool.selected_object is None:
            return False
        else:
            return True

    def execute(self, context):
        bpy.context.space_data.shading.color_type = 'OBJECT'
        # Assign a color from the list to the grease pencil
        color = next(self.colors)
        curve_cut.set_drawing(color)
        return {'FINISHED'}

class BorderThicknessTool(bpy.types.Operator):
    bl_idname = "object.border_thickness_tool"  # Add this line
    bl_label = "Set cut border thickness"
    bpy.types.Scene.border_thickness = bpy.props.FloatProperty(
        name="",
        description="Set the thickness of the initial border around the cutting object",
        default=2.0,  # Default value
        min=0.5,  # Minimum value
        max=10.0,  # Maximum value
        precision=1  # Limit to 1 decimal place
    )
    def execute(self, context):
        # Correctly access the property value with context.scene.border_thickness
        print("Border Thickness:", context.scene.border_thickness)
        return {'FINISHED'}
    

class MakeCutMeshOperator(bpy.types.Operator):
    bl_idname = "object.chop_obj"
    bl_label = "Make Choping Objects"
    bl_description = "Create a cutting object from the drawing. You have to create a Cut Line first"

    @classmethod
    def poll(cls, context):
        # Check if selected_object is not None
        object_selected = context.scene.mesh_selector_tool.selected_object is not None

        # Check if "draw cuts" collection exists and is not empty
        collection_exists = False

        if "draw cuts" in bpy.data.collections:
            collection = bpy.data.collections["draw cuts"]
            for obj in collection.objects:
                if obj.type == 'GPENCIL':
                    for layer in obj.data.layers:
                        for frame in layer.frames:
                            if frame.strokes:
                                collection_exists = True
                                break

        # The operator can be executed if both conditions are True
        return object_selected and collection_exists
    
    def execute(self, context):
        bpy.ops.ed.undo_push(message="MakeCutMeshOperator")
        #set object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        #Deselct all objects
        bpy.ops.object.select_all(action='DESELECT')
        object_selected = context.scene.mesh_selector_tool.selected_object
        bpy.context.view_layer.objects.active = object_selected
        object_selected.select_set(True)
        #Apply all transformations to object_selected
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.select_all(action='DESELECT')
        
        draw_cuts_collection = bpy.data.collections.get("draw cuts")

        for gpencil_obj in [obj for obj in draw_cuts_collection.objects if obj.type == 'GPENCIL']:

            curve_cut.refine_drawing(gpencil_obj,object_selected)
            curve_cut.chop_obj()

        draw_cuts_collection = bpy.data.collections.get("draw cuts")

        if draw_cuts_collection:
            bpy.data.collections.remove(draw_cuts_collection)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.ed.undo_push(message="MakeCutMeshOperator")

        return {'FINISHED'}

class ChopitMeshOperator(bpy.types.Operator):
    bl_idname = "object.chopit"
    bl_label = "Chop it"
    bl_description = "Chop the selected mesh object using the Chop Objects created. You have to create a Chop Object first"
    selected_object = None

    @classmethod
    def poll(cls, context):
        # Check if selected_object is not None
        object_selected = context.scene.mesh_selector_tool.selected_object is not None
        # Check if "Cutting objects" collection exists and is not empty
        collection_exists = False

        if "Cutting objects" in bpy.data.collections:
            collection = bpy.data.collections["Cutting objects"]
            collection_exists = any(obj.type == 'MESH' for obj in collection.objects)

        # The operator can be executed if both conditions are True
        return object_selected and collection_exists
    
    def execute(self, context):
        bpy.ops.ed.undo_push(message="ChopitMeshOperator")
        # Get the selected object from the property group
        self.selected_object = context.scene.mesh_selector_tool.selected_object
        bpy.ops.object.mode_set(mode='OBJECT')
        #Deselct all objects
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = self.selected_object
        #select the object
        self.selected_object.select_set(True)
        #Apply all transformations to object_selected
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        # Call the chopit function
        draw_cuts_collection = bpy.data.collections.get("Cutting objects")

        if draw_cuts_collection:
            for cut_obj in draw_cuts_collection.objects:
                if cut_obj and cut_obj.type == 'MESH':
                    curve_cut.chopit(cut_obj, self.selected_object)

        # Apply all boolean modifiers in the selected object
        context.view_layer.objects.active = self.selected_object

        for modifier in self.selected_object.modifiers:
            if modifier.type == 'BOOLEAN':
                bpy.ops.object.modifier_apply(modifier=modifier.name)

        obj_cuts_collection = bpy.data.collections.get("Cutting objects")

        if obj_cuts_collection:
            bpy.data.collections.remove(obj_cuts_collection)
            
        # Split the selected object into loose parts
        bpy.ops.object.select_all(action='DESELECT')
        self.selected_object.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode='OBJECT')
        set_selected_object_color(self, context)
        context.scene.mesh_selector_tool.z_dim = self.selected_object.dimensions.z 
        bpy.ops.ed.undo_push(message="ChopitMeshOperator")

        return {'FINISHED'}
    
class ExportProperties(bpy.types.PropertyGroup):
    export_folder: bpy.props.StringProperty(
        name="",
        subtype='DIR_PATH',
        description="Select the destination folder for exporting",
    )  # type: ignore

class ExportAllMeshesOperator(bpy.types.Operator):
    bl_idname = "object.export_all_meshes"
    bl_label = "Export All Meshes"
    bl_description = "Export all mesh objects in the scene to the specified folder"
        
    @classmethod
    def poll(cls, context):
        return bool(context.scene.folder_selector_tool.export_folder)

    def execute(self, context):
        export_folder = bpy.path.abspath(context.scene.folder_selector_tool.export_folder)

        # Create the export folder if it doesn't exist
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Export each mesh object in the current view layer
        for obj in context.view_layer.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.wm.obj_export(filepath=os.path.join(export_folder, f"{obj.name}.obj"), export_uv=False, export_normals=True, export_colors=False, export_materials=False, export_selected_objects = True)
                obj.select_set(False)

        self.report({'INFO'}, "Meshes exported successfully.")
        return {'FINISHED'}

class ShellThicknessTool(bpy.types.Operator):
    bl_idname = "object.shell_thickness_tool"  # Add this line
    bl_label = "Set Printer Dimensions"
    bpy.types.Scene.shell_thickness = bpy.props.FloatProperty(
        name="",
        description="Set the thickness for hollowing the object",
        default=3.0,  # Default value
        min=0.5,  # Minimum value
        max=10.0,  # Maximum value
    )
    def execute(self, context):
        # You can access the property value with self.shell_thickness
        print("Shell Thickness:", self.shell_thickness)
        return {'FINISHED'}

class MakeHollowOperator(bpy.types.Operator):
    bl_idname = "object.make_hollow"
    bl_label = "Make Hollow"

    @classmethod
    def poll(cls, context):
        # Check if selected_object is not None
        object_is_selected = context.scene.mesh_selector_tool.selected_object is not None
        return object_is_selected
    def execute(self, context):
        # Call the make_hollow function
        make_hollow.make_hollow_part(context.scene.mesh_selector_tool.selected_object, context.scene.shell_thickness)
        return {'FINISHED'}


class PrinterDimTool(bpy.types.Operator):
    bl_idname = "object.min_printer_dim"
    bl_label = "Set Printer Dimensions"
    
    # Define the property
    bpy.types.Scene.min_printer_dim = bpy.props.FloatProperty(
        name="",
        description="Set the minimum printer dimension",
        default=20.0,  # Default value
        min=10.0,  # Minimum value
        max=100.0,  # Maximum value
    )

    def execute(self, context):
        # You can access the property value with self.min_dim
        print("Minimum Dimension:", self.min_dim)
        return {'FINISHED'}

class CubitOperator(bpy.types.Operator):
    bl_idname = "object.cubit"
    bl_label = "Cut into cubes"
    bl_description = "cuts the selected object into managable cubes"

    @classmethod
    def poll(cls, context):
        # Check if selected_object is not None
        object_is_selected = context.scene.mesh_selector_tool.selected_object is not None
        return object_is_selected
    
    def execute(self, context):
        bpy.ops.ed.undo_push(message="CubitOperator")
        cubit.cubit(context.scene.mesh_selector_tool.selected_object, context.scene.min_printer_dim)
        bpy.context.space_data.shading.color_type = 'RANDOM'

        return {'FINISHED'}

def register():

    bpy.utils.register_class(ImportMeshPropertiesGroup)
    bpy.types.Scene.mesh_importer_tool = bpy.props.PointerProperty(type=ImportMeshPropertiesGroup)
    bpy.utils.register_class(SelectMeshProperties)
    bpy.types.Scene.mesh_selector_tool = bpy.props.PointerProperty(type=SelectMeshProperties)
    bpy.utils.register_class(ModelHeightTool)
    bpy.utils.register_class(ExportProperties)
    bpy.types.Scene.folder_selector_tool = bpy.props.PointerProperty(type=ExportProperties)
    bpy.utils.register_class(SetDrawOperator)
    bpy.utils.register_class(BorderThicknessTool)
    bpy.utils.register_class(MakeCutMeshOperator)
    bpy.utils.register_class(ChopitMeshOperator)
    bpy.utils.register_class(ExportAllMeshesOperator)
    bpy.utils.register_class(ShellThicknessTool)
    bpy.utils.register_class(MakeHollowOperator)
    bpy.utils.register_class(CubitOperator)

def unregister():

    bpy.utils.unregister_class(ImportMeshPropertiesGroup)
    bpy.utils.unregister_class(ModelHeightTool)
    bpy.utils.unregister_class(SetDrawOperator)
    bpy.utils.unregister_class(BorderThicknessTool)
    bpy.utils.unregister_class(MakeCutMeshOperator)
    bpy.utils.unregister_class(ChopitMeshOperator)
    del bpy.types.Scene.mesh_selector_tool
    del bpy.types.Scene.folder_selector_tool
    bpy.utils.unregister_class(SelectMeshProperties)
    bpy.utils.unregister_class(ExportProperties)
    bpy.utils.unregister_class(ExportAllMeshesOperator)
    del bpy.types.Scene.mesh_importer_tool
    bpy.utils.unregister_class(ShellThicknessTool)
    bpy.utils.unregister_class(MakeHollowOperator)
    bpy.utils.unregister_class(CubitOperator)

