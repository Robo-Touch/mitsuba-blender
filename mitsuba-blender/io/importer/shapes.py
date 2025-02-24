import time

if "bpy" in locals():
    import importlib
    if "bl_transform_utils" in locals():
        importlib.reload(bl_transform_utils)
    if "bl_import_ply" in locals():
        importlib.reload(bl_import_ply)
    if "bl_import_obj" in locals():
        importlib.reload(bl_import_obj)

import bpy
import bmesh
from mathutils import Matrix, Vector
import numpy as np

from . import bl_transform_utils
from . import bl_import_ply
from . import bl_import_obj

######################
##    Utilities     ##
######################

def _set_bl_mesh_shading(bl_mesh, flat_shading=True, flip_normals=False):
    ''' Set a Blender mesh shading mode.

    Params
    ------
    bl_mesh : The Blender mesh to operate on.
    flat_shading : boolean, optional
        Should the face normals be used instead of the vertex normals?
    flip_normals : boolean, optional
        Should the normals be flipped from the current normal direction?
    '''
    if flat_shading:
        bl_mesh.polygons.foreach_set('use_smooth', [False] * len(bl_mesh.polygons))
    else:
        bl_mesh.calc_normals()
        bl_mesh.polygons.foreach_set('use_smooth', [True] * len(bl_mesh.polygons))
    if flip_normals:
        bl_mesh.flip_normals()
    bl_mesh.update()

######################
##    Converters    ##
######################

def mi_ply_to_bl_shape(mi_context, mi_shape):
    assert mi_shape.has_property('filename')

    filename = mi_shape['filename']
    abs_path = mi_context.resolve_scene_relative_path(filename)

    # Load .PLY mesh from file
    bl_mesh = bl_import_ply.load_ply_mesh(abs_path, mi_shape.id())
    if not bl_mesh:
        mi_context.log(f'Cannot load PLY mesh file "{filename}".', 'ERROR')
        return None
    
    # Set face normals if requested
    _set_bl_mesh_shading(bl_mesh, mi_shape.get('face_normals', False))

    world_matrix = bl_transform_utils.mi_transform_to_bl_transform(mi_shape.get('to_world', None))

    return bl_mesh, mi_context.mi_space_to_bl_space(world_matrix)

def mi_obj_to_bl_shape(mi_context, mi_shape):
    start_time = time.time()

    assert mi_shape.has_property('filename')

    filename = mi_shape.get('filename')
    abs_path = mi_context.resolve_scene_relative_path(filename)

    # Load the mesh from the file
    bl_meshes = bl_import_obj.load(abs_path)
    # FIXME: Handle multiple objects if supported by Mistuba.
    if len(bl_meshes) > 1:
        mi_context.log('OBJ file containing more than one mesh. Only the first one will be loaded.', 'WARN')
    bl_mesh = bl_meshes[0]
    bl_mesh.name = mi_shape.id()

    # FIXME: Support UV flipping.

    # Set face normals if requested
    _set_bl_mesh_shading(bl_mesh, mi_shape.get('face_normals', False))

    world_matrix = bl_transform_utils.mi_transform_to_bl_transform(mi_shape.get('to_world', None))

    end_time = time.time()
    mi_context.log(f'Loaded OBJ mesh "{mi_shape.id()}". Took {end_time-start_time:.2f}s.', 'INFO')

    return bl_mesh, mi_context.mi_space_to_bl_space(world_matrix)

def mi_sphere_to_bl_shape(mi_context, mi_shape):
    bl_mesh = bpy.data.meshes.new(mi_shape.id())
    bl_bmesh = bmesh.new()

    if mi_shape.has_property('to_world'):
        world_matrix = mi_context.mi_space_to_bl_space(bl_transform_utils.mi_transform_to_bl_transform(mi_shape.get('to_world', None)))
        radius = 1.0
    else:
        # NOTE: We transform only the position vector to Blender space as the mesh is already correctly oriented.
        world_matrix = Matrix.Translation(mi_context.mi_space_to_bl_space(Vector(mi_shape.get('center', [0.0, 0.0, 0.0]))))
        radius = mi_shape.get('radius', 1.0)

    # Create a UV sphere mesh
    # NOTE: The 'diameter' parameter seems to be missnamed as it results in sphere twice as big as expected
    bmesh.ops.create_uvsphere(bl_bmesh, u_segments=32, v_segments=16, diameter=radius, calc_uvs=True)
    bl_bmesh.to_mesh(bl_mesh)
    bl_bmesh.free()

    _set_bl_mesh_shading(bl_mesh, flat_shading=False, flip_normals=mi_shape.get('flip_normals', False))

    # FIXME: Verify that the world matrix is correct
    return bl_mesh, world_matrix

def mi_disk_to_bl_shape(mi_context, mi_shape):
    bl_mesh = bpy.data.meshes.new(mi_shape.id())
    bl_bmesh = bmesh.new()

    # Create a disk
    bmesh.ops.create_circle(bl_bmesh, cap_ends=True, cap_tris=True, segments=32, radius=1.0, calc_uvs=True)
    bl_bmesh.to_mesh(bl_mesh)
    bl_bmesh.free()

    _set_bl_mesh_shading(bl_mesh, flip_normals=mi_shape.get('flip_normals', False))

    # FIXME: The world matrix seems off
    world_matrix = bl_transform_utils.mi_transform_to_bl_transform(mi_shape.get('to_world', None))

    return bl_mesh, mi_context.mi_space_to_bl_space(world_matrix)

def mi_rectangle_to_bl_shape(mi_context, mi_shape):
    bl_mesh = bpy.data.meshes.new(mi_shape.id())
    bl_bmesh = bmesh.new()

    # Create a rectangle
    bmesh.ops.create_grid(bl_bmesh, x_segments=1, y_segments=1, size=1.0, calc_uvs=True)
    bl_bmesh.to_mesh(bl_mesh)
    bl_bmesh.free()

    _set_bl_mesh_shading(bl_mesh, flip_normals=mi_shape.get('flip_normals', False))
    
    # FIXME: The world matrix seems off
    world_matrix = bl_transform_utils.mi_transform_to_bl_transform(mi_shape.get('to_world', None))

    return bl_mesh, mi_context.mi_space_to_bl_space(world_matrix)

def mi_cube_to_bl_shape(mi_context, mi_shape):
    bl_mesh = bpy.data.meshes.new(mi_shape.id())
    bl_bmesh = bmesh.new()

    # Create a cube
    bmesh.ops.create_cube(bl_bmesh, size=2.0, calc_uvs=True)
    bl_bmesh.to_mesh(bl_mesh)
    bl_bmesh.free()

    _set_bl_mesh_shading(bl_mesh, flip_normals=mi_shape.get('flip_normals', False))

    # FIXME: The world matrix seems off
    world_matrix = bl_transform_utils.mi_transform_to_bl_transform(mi_shape.get('to_world', None))

    return bl_mesh, mi_context.mi_space_to_bl_space(world_matrix)

def mi_serialized_to_bl_shape(mi_context, mi_shape):
    import mitsuba as mi
    from mitsuba.python import traverse
    start_time = time.time()

    # only safe way is to create a shape using mitsuba
    assert mi_shape.has_property('filename')

    filename = mi_shape.get('filename')
    abs_path = mi_context.resolve_scene_relative_path(filename)

    # no need to parse the trafo as this is taken care of after the mesh is loaded
    mi_shape_dict = {
        "type": mi_shape.plugin_name(),
        "filename": abs_path,
        "shape_index": mi_shape.get('shape_index')
    }

    mi_shape_inst = mi.load_dict(mi_shape_dict)
    params = traverse(mi_shape_inst)
    vert_count = params["vertex_count"]
    face_count = params["face_count"]
    verts = np.array(params["vertex_positions"])
    faces = np.array(params["faces"])

    bl_mesh = bpy.data.meshes.new(mi_shape.id())
    
    # https://docs.blender.org/api/current/bpy.types.Mesh.html#bpy.types.Mesh.from_pydata
    verts = verts.reshape((vert_count, 3))
    faces = faces.reshape((face_count, 3))
    verts_pydata = []
    for i in range(vert_count):
        verts_pydata.append(tuple(verts[i]))
    face_pydata = []
    for i in range(face_count):
        face_pydata.append(tuple(faces[i]))

    # When an empty iterable is passed in, the edges are inferred from the polygons
    edges = []
    bl_mesh.from_pydata(verts_pydata, edges, face_pydata)
    bl_mesh.calc_normals()
    
    end_time = time.time()
    mi_context.log(f'Loaded serialized mesh "{mi_shape.id()}". Took {end_time-start_time:.2f}s.', 'INFO')

    world_matrix = bl_transform_utils.mi_transform_to_bl_transform(mi_shape.get('to_world', None))

    return bl_mesh, world_matrix
    
######################
##   Main import    ##
######################

_shape_converters = {
    'ply': mi_ply_to_bl_shape,
    'obj': mi_obj_to_bl_shape,
    'sphere': mi_sphere_to_bl_shape,
    'disk': mi_disk_to_bl_shape,
    'rectangle': mi_rectangle_to_bl_shape,
    'cube': mi_cube_to_bl_shape,
    "serialized": mi_serialized_to_bl_shape
}

def mi_shape_to_bl_shape(mi_context, mi_shape):
    shape_type = mi_shape.plugin_name()
    if shape_type not in _shape_converters:
        mi_context.log(f'Mitsuba Shape type "{shape_type}" not supported.', 'ERROR')
        return None
    
    # Create the Blender object
    bl_mesh, world_matrix = _shape_converters[shape_type](mi_context, mi_shape)

    return bl_mesh, world_matrix
