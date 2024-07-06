import bpy
from mathutils import Vector

# Constants
RELATIVE_OFFSET = -1.001

def get_part_center(part):

    # Deselect all, select and make active the part
    bpy.ops.object.select_all(action='DESELECT')
    part.select_set(True)
    bpy.context.view_layer.objects.active = part

    # Get the world-space coordinates of the bounding box vertices
    bounding_box_world_coords = [part.matrix_world @ Vector(coord) for coord in part.bound_box]

    # Calculate the center coordinates of the part
    center_x = sum([v.x for v in bounding_box_world_coords]) / 8
    center_y = sum([v.y for v in bounding_box_world_coords]) / 8
    center_z = sum([v.z for v in bounding_box_world_coords]) / 8

    part_center = (center_x, center_y, center_z)
    part_dimensions = (part.dimensions[0], part.dimensions[1], part.dimensions[2])
    return part_center, part_dimensions

def create_cutting_cube(part_center, part_dimensions, axis, cut_size):
    center = part_center

    # Create a cube to use for cutting
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    cube = bpy.context.active_object

    # Set the dimensions of the cube based on the cut axis
    if axis == 'x':
        cube.dimensions = [cut_size, part_dimensions[1] + 1, part_dimensions[2] + 1]
        cube.location.x = center[0] - cut_size/2 + part_dimensions[0]/2
        cube.location.y = center[1]
        cube.location.z = center[2]

    elif axis == 'y':
        cube.dimensions = [part_dimensions[0]+1, cut_size, part_dimensions[2]+1]
        cube.location.x = center[0]
        cube.location.y = center[1] - cut_size/2 + part_dimensions[1]/2
        cube.location.z = center[2]
        
    elif axis == 'z':
        cube.dimensions = [part_dimensions[0]+1, part_dimensions[1]+1, cut_size]
        cube.location.x = center[0]
        cube.location.y = center[1]
        cube.location.z = center[2] - cut_size/2 + part_dimensions[2]/2

    return cube

def apply_array_modifier(cube, axis, part_dimensions, cut_size):
    """Apply an array modifier to the cube."""
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.modifier_add(type='ARRAY')

    # Access the last added modifier (which should be the Array modifier)
    array_modifier = cube.modifiers[-1]  # Access the last modifier

    if axis == 'x':
        array_modifier.count = int(part_dimensions[0]/cut_size)+1
        array_modifier.relative_offset_displace[0] = RELATIVE_OFFSET
    elif axis == 'y':
        array_modifier.count = int(part_dimensions[1]/cut_size)+1
        array_modifier.relative_offset_displace[0] = 0
        array_modifier.relative_offset_displace[1] = RELATIVE_OFFSET
    elif axis == 'z':
        array_modifier.count = int(part_dimensions[2]/cut_size)+1
        array_modifier.relative_offset_displace[0] = 0
        array_modifier.relative_offset_displace[2] = RELATIVE_OFFSET
    else:
        raise ValueError(f"Invalid axis: {axis}")

    # Apply the modifier using its actual name
    bpy.ops.object.modifier_apply(modifier=array_modifier.name)
    
    return cube

def boolean_part(part, cube):
 
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select the cube and make it the active object
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube

    # Add a Boolean modifier to the cube
    bpy.ops.object.modifier_add(type='BOOLEAN')

    # Access the last added modifier, which is the Boolean modifier
    boolean_modifier = cube.modifiers[-1]

    # Configure the Boolean modifier
    boolean_modifier.operation = 'INTERSECT'
    boolean_modifier.solver = 'FAST'
    boolean_modifier.object = part

    # Apply the modifier
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
    #update viewport3D
    bpy.context.view_layer.update()

    
def separate_parts(parts):

    bpy.ops.object.select_all(action='DESELECT')
    parts.select_set(True)
    #make the part the active object
    bpy.context.view_layer.objects.active = parts
    original_name = parts.name
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')

    return bpy.context.selected_objects, original_name


def enumerate_parts(parts, original_name):     
    #TODO: fix the enumerator function and implement the cleanup afterwards of useless parts         
    """
    for i, part in enumerate(parts):
        if part.name[:4] != "Part":
            part.name = "Part_" + str(i+1)
        else:
            part.name += original_name + "_" + str(i+1)
    """
    pass


def cut_part(part, axis, cut_size, parts_collection):
     
    part_center, part_dimensions = get_part_center(part)
    cube = create_cutting_cube(part_center, part_dimensions, axis, cut_size)
    cubes = apply_array_modifier(cube, axis, part_dimensions, cut_size)
    cube_to_parts, original_name = separate_parts(cubes)
    enumerate_parts(cube_to_parts, original_name) 
    
    for cube in cube_to_parts:
        boolean_part(part, cube)
        parts_collection.objects.link(cube)
        bpy.context.collection.objects.unlink(cube)
        
    for part in parts_collection.objects:
        cube_to_parts, original_name = separate_parts(part)
        enumerate_parts(cube_to_parts, original_name) 
        

def create_collection(name):
    """Create a new collection and link it to the scene."""
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection

def delete_collection(collection):
    """Delete a collection and all its objects."""
    for obj in collection.objects:
        bpy.data.objects.remove(obj)
    bpy.data.collections.remove(collection)


def cubit(obj, print_size):
    
    # Create collections
    z_parts_collection = create_collection("z Parts")
    x_parts_collection = create_collection("x Parts")
    y_parts_collection = create_collection("y Parts")

    cut_part(obj, "z", print_size, z_parts_collection)
    #TODO: Implement the following 
    #check if the part should be cut
    #enumerate the parts



    for part in z_parts_collection.objects:
        cut_part(part,"x",print_size,x_parts_collection)
        #TODO: Implement the following
        #check if the part is too small or basically a cube so they will be discarted or set aside    
    delete_collection(z_parts_collection)
    for part in x_parts_collection.objects:
        cut_part(part,"y",print_size,y_parts_collection)
    delete_collection(x_parts_collection)
    obj.hide_viewport = True

