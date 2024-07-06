"""This module creates a new window and splits it into three areas, one for the 3D viewr, another for the outliner and the last one for the propterties editor, this gives the user only the minimal information required to use the intended Add-on"""
import bpy

def set_units():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 0.01
    scene.unit_settings.length_unit = 'CENTIMETERS'
    
def split_in_two():
    # Create a new window
    bpy.ops.wm.window_new()
    bpy.ops.screen.screen_full_area()  # Switch the context to the new window

    # Restore the layout
    bpy.ops.screen.back_to_previous()

    # Split the area
    bpy.ops.screen.area_split(direction='VERTICAL', factor=0.75)

    # Set the left area to 3D view
    bpy.context.window.screen.areas[0].type = 'VIEW_3D'

    # Set the top right area to Outliner
    bpy.context.window.screen.areas[1].type = 'OUTLINER'

    # Add a timer to delay the execution of the view_axis operator
    bpy.app.timers.register(set_view_axis, first_interval=0.1)

def set_view_axis():
    # Get the 3D view area
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Set the viewport display to orthographic
                    space.region_3d.view_perspective = 'ORTHO'
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            ctx = {
                                "window": bpy.context.window,
                                "area": area,
                                "region": region
                            }
                            bpy.ops.view3d.view_axis('INVOKE_DEFAULT', **ctx, type='RIGHT', align_active=True)
                            return None  # Unregister the timer
    return 0.1  # Keep the timer running
  


