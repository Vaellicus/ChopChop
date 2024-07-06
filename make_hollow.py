import bpy

def make_hollow_part(obj, thickness):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    #Make a copy of the mesh
    bpy.ops.object.duplicate()
    #store the copy in a variable
    core = bpy.context.selected_objects[0]
    #rename the copy
    core.name = "Core"
    #make a second copy
    bpy.ops.object.duplicate()
    #store the second copy in a variable
    limit = bpy.context.selected_objects[0]
    #rename the second copy
    limit.name = "Limit"
    #deselect everything
    bpy.ops.object.select_all(action='DESELECT')
    #select the core
    bpy.context.view_layer.objects.active = core
    #Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    #change to vertex select mode
    bpy.ops.mesh.select_mode(type="VERT")
    #Select all the vertices
    bpy.ops.mesh.select_all(action='SELECT')

    for x in range(10):
        bpy.ops.transform.shrink_fatten(value=-thickness/10)
        bpy.ops.mesh.remove_doubles(threshold=thickness/(10-x))
        bpy.ops.mesh.vertices_smooth(factor=0.5)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='REMESH')
    bpy.context.object.modifiers["Remesh"].voxel_size = 1
    bpy.ops.object.modifier_apply(modifier="Remesh")

    bpy.ops.object.select_all(action='DESELECT')
    #now we select the limit
    bpy.context.view_layer.objects.active = limit
    #add decimate modifier and reduce to 0.5
    bpy.ops.object.modifier_add(type='DECIMATE')
    bpy.context.object.modifiers["Decimate"].ratio = 0.5
    #apply the modifier
    bpy.ops.object.modifier_apply(modifier="Decimate")
    #Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    #change to vertex select mode
    bpy.ops.mesh.select_mode(type="VERT")
    #Select all the vertices
    bpy.ops.mesh.select_all(action='SELECT')
    #shrink the mesh by the thickness
    bpy.ops.transform.shrink_fatten(value=-thickness)
    #deselect everything
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='REMESH')
    bpy.context.object.modifiers["Remesh"].voxel_size = 1
    bpy.ops.object.modifier_apply(modifier="Remesh")
    bpy.ops.object.select_all(action='DESELECT')
    #select the core
    
    bpy.context.view_layer.objects.active = core
    #add a boolean modifier to the core and then intercect it with the limit
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers["Boolean"].object = limit
    #use fast solver for the boolean operation 
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    #apply the modifier
    bpy.ops.object.modifier_apply(modifier="Boolean")
    #deselect everything
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = core
    #Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    #change to vertex select mode
    bpy.ops.mesh.select_mode(type="VERT")
    #Select all the vertices
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth(factor=0.5)
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')
    limit.select_set(True)
    #select the limit
    bpy.context.view_layer.objects.active = limit
    #delete the limit
    bpy.ops.object.delete()
    #select the core and the original object and join them
    bpy.ops.object.select_all(action='DESELECT')
    core.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()







