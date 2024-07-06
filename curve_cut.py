import bpy
import bmesh
import mathutils
import time


def set_drawing(color):
    if bpy.context.active_object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    draw_cuts_collection = bpy.data.collections.get("draw cuts")
    
    if not draw_cuts_collection:
        draw_cuts_collection = bpy.data.collections.new("draw cuts")
        bpy.context.scene.collection.children.link(draw_cuts_collection)  # Add the new collection to the scene
    
    # Find the 3D View area
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    # Override the context
    override = bpy.context.copy()
    override['area'] = area
    space = area.spaces.active
    # Get the region_3d of the 3D View
    region_3d = space.region_3d
    # Set the view to orthographic
    region_3d.view_perspective = 'ORTHO'
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.length_unit = 'CENTIMETERS'
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.space_data.clip_end = 1000


    #add grease pen blank object
    bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1), type='EMPTY')
    bpy.context.active_object.name = "Cut line"
    gpencil = bpy.context.object  # Get the newly created Grease Pencil object
    # Add the Grease Pencil object to the "draw cuts" collection
    draw_cuts_collection.objects.link(gpencil)  # Link the object to the collection
    bpy.context.collection.objects.unlink(gpencil)  # Unlink the object from the current collection
    bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
    bpy.context.scene.tool_settings.gpencil_stroke_placement_view3d = 'SURFACE'
    gpencil.data.zdepth_offset = 0.4
    bpy.data.brushes["Pencil"].size = 1000
    bpy.data.brushes["Pencil"].gpencil_settings.input_samples = 1
    # Assign a color from the list to the grease pencil
    gpencil.color = color


def delete_far_points(gpencil_obj, selected_obj):
    threshold = 0.5  # The threshold distance for removing points
    # Create a BVH tree from the selected object
    bm = bmesh.new()
    bm.from_mesh(selected_obj.data)
    bm.transform(selected_obj.matrix_world)
    bvh = mathutils.bvhtree.BVHTree.FromBMesh(bm)

    # Iterate over the points in each stroke of each layer
    for layer in gpencil_obj.data.layers:
        for frame in layer.frames:
            for stroke in frame.strokes:
                points_to_remove = []
                for i, point in enumerate(stroke.points):
                    # Calculate the distance from the point to the selected object
                    nearest_point, _, _, _ = bvh.find_nearest(point.co)
                    distance = (nearest_point - point.co).length
                    # If the distance is greater than the threshold, mark the point for removal
                    if distance > threshold:
                        points_to_remove.append(i)
                # Remove the marked points
                for i in sorted(points_to_remove, reverse=True):
                    stroke.points.pop(index=i)
    bm.free()


#shrinkwap a gpencil around a mesh and apply it afterwards
def shrinkwrap_modifier(gpencil_obj, selected_obj):
    # Ensure we're in Object mode
    if bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select the grease pencil object
    gpencil_obj.select_set(True)
    bpy.context.view_layer.objects.active = gpencil_obj
    
    # Add the Shrinkwrap modifier using the low-level API
    sw_modifier = gpencil_obj.grease_pencil_modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')
    sw_modifier.target = selected_obj
    sw_modifier.wrap_method = 'TARGET_PROJECT'
    sw_modifier.offset = 0.2
    sw_modifier.wrap_mode = 'ABOVE_SURFACE'
    sw_modifier.smooth_factor = 1
    sw_modifier.smooth_step = 4
    
    # Update the dependency graph
    bpy.context.view_layer.update()

    bpy.ops.object.gpencil_modifier_apply(modifier="Shrinkwrap")


#refine and join the strokes
def refine_drawing(gpencil_obj, selected_obj):
    #make the grease pencil object active
    bpy.context.view_layer.objects.active = gpencil_obj
    delete_far_points(gpencil_obj, selected_obj)
    bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
    bpy.ops.gpencil.select_all(action='SELECT')
    bpy.ops.gpencil.stroke_join(type='JOIN')
    bpy.ops.gpencil.stroke_cyclical_set(type='CLOSE', geometry=True) 
    bpy.ops.gpencil.select_all(action='SELECT')  
    bpy.ops.gpencil.stroke_sample(length=0.1, sharp_threshold=0.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    shrinkwrap_modifier(gpencil_obj, selected_obj)
    # Find the 3D View area
    bpy.context.view_layer.objects.active = gpencil_obj
 
    bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
    bpy.ops.gpencil.select_all(action='SELECT')

    bpy.ops.gpencil.stroke_sample(length=0.3, sharp_threshold=0.0)
    shrinkwrap_modifier(gpencil_obj, selected_obj)    
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    # Override the context
    override = bpy.context.copy()
    override['area'] = area
    # Convert grease pencil to path
    bpy.ops.gpencil.convert(type='PATH', use_timing_data=False)
    # Deselect the grease pencil object
    gpencil_obj.select_set(False)

    # Set the only other selected object as the active object
    for obj in bpy.context.selected_objects:
        if obj != gpencil_obj:
            bpy.context.view_layer.objects.active = obj
            break

    # Convert the path to a mesh
    bpy.ops.object.convert(target='MESH')
    temp_mesh_obj = bpy.context.active_object  # Get the newly created mesh object
    # Delete the original path object
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    # Select the mesh object
    bpy.context.view_layer.objects.active = temp_mesh_obj
    temp_mesh_obj.select_set(True)
 

def chop_obj():
    """
    Consider using this to help with visualization
    # Assuming `obj` is the object you want to always appear on top
    obj.show_in_front = True
    """
    active_obj = bpy.context.object
    bpy.context.view_layer.objects.active = active_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.5) 
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.edge_face_add( )
    bpy.ops.mesh.inset(thickness=0.1, depth=0, release_confirm=True)
    #for loop that will repeat itself for every 0.1 of the border_thickness_tool   
    for i in range(0, round(bpy.context.scene.border_thickness/ 0.1)):
        bpy.ops.mesh.inset(thickness=0.1, depth=0, release_confirm=True)
        bpy.ops.mesh.remove_doubles(threshold=0.5)
  
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.inset(thickness=0.5, depth=1, release_confirm=True)
    bpy.ops.transform.resize(value=(1, 1, 0), orient_type='NORMAL')
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_context_move(TRANSFORM_OT_translate={"value":(0, 0, 0.01), "orient_type":'NORMAL'})
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.active_object.name = "Cut Mesh"
    obj_cuts_collection = bpy.data.collections.get("Cutting objects")

    if not obj_cuts_collection:
        obj_cuts_collection = bpy.data.collections.new("Cutting objects")
        bpy.context.scene.collection.children.link(obj_cuts_collection)  # Add the new collection to the scene
    
    obj_cuts_collection = bpy.data.collections.get("Cutting objects")
    active_object = bpy.context.active_object
    obj_cuts_collection.objects.link(active_object)  # Link the object to the collection
    bpy.context.collection.objects.unlink(active_object)  # Unlink the object from the current collection
    

def chopit(cut_obj, selected_object):
    # Assign boolean modifier to selected object
    bool_mod = selected_object.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cut_obj
    # Delete the "draw cuts" collection if it exists
    

    
