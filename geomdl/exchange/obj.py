"""
.. module:: exchange.obj
    :platform: Unix, Windows
    :synopsis: Provides exchange capabilities for OBJ file format

.. moduleauthor:: Onur R. Bingol <contact@onurbingol.net>

"""

import struct
from . import exc_helpers
from .. import linalg
from .. import entity
from .. import tessellate
from ..base import export, GeomdlError


@export
def import_obj(file_name, **kwargs):
    """ Reads .obj files and generates faces.

    Keyword Arguments:
        * ``callback``: reference to the function that processes the faces for customized output

    The structure of the callback function is shown below:

    .. code-block:: python

        def my_callback_function(face_list):
            # "face_list" will be a list of elements.Face class instances
            # The function should return a list
            return list()

    :param file_name: file name
    :type file_name: str
    :return: output of the callback function (default is a list of faces)
    :rtype: list
    """
    def default_callback(face_list):
        return face_list

    # Keyword arguments
    callback_func = kwargs.get('callback', default_callback)

    # Read and process the input file
    content = exc_helpers.read_file(file_name)
    content_arr = content.split("\n")

    # Initialize variables
    on_face = False
    vertices = []
    triangles = []
    faces = []

    # Index values
    vert_idx = 1
    tri_idx = 1
    face_idx = 1

    # Loop through the data
    for carr in content_arr:
        carr = carr.strip()
        data = carr.split(" ")
        data = [d.strip() for d in data]
        if data[0] == "v":
            if on_face:
                on_face = not on_face
                face = entity.Face(*triangles, id=face_idx)
                faces.append(face)
                face_idx += 1
                vertices[:] = []
                triangles[:] = []
                vert_idx = 1
                tri_idx = 1
            vertex = entity.Vertex(*data[1:], id=vert_idx)
            vertices.append(vertex)
            vert_idx += 1
        if data[0] == "f":
            on_face = True
            triangle = entity.Triangle(*[vertices[int(fidx) - 1] for fidx in data[1:]], id=tri_idx)
            triangles.append(triangle)
            tri_idx += 1

    # Process he final face
    if triangles:
        face = entity.Face(*triangles, id=face_idx)
        faces.append(face)

    # Return the output of the callback function
    return callback_func(faces)


@export
def export_obj_str(surface, **kwargs):
    """ Exports surface(s) as a .obj file (string).

    Keyword Arguments:
        * ``vertex_spacing``: size of the triangle edge in terms of surface points sampled. *Default: 2*
        * ``vertex_normals``: if True, then computes vertex normals. *Default: False*
        * ``parametric_vertices``: if True, then adds parameter space vertices. *Default: False*

    :param surface: surface or surfaces to be saved
    :type surface: abstract.Surface or multi.SurfaceContainer
    :return: contents of the .obj file generated
    :rtype: str
    """
    # Get keyword arguments
    vertex_spacing = int(kwargs.get('vertex_spacing', 1))
    include_vertex_normal = kwargs.get('vertex_normals', False)
    include_param_vertex = kwargs.get('parametric_vertices', False)

    # Input validity checking
    if surface.pdimension != 2:
        raise GeomdlError("Can only export surfaces")
    if vertex_spacing < 1:
        raise GeomdlError("Vertex spacing should be bigger than zero")

    # Create the string and start adding triangulated surface points
    line = "# Generated by geomdl\n"
    vertex_offset = 0  # count the vertices to update the face numbers correctly

    # Initialize lists for geometry data
    str_v = []  # vertices
    str_vn = []  # vertex normals
    str_vp = []  # parameter space vertices
    str_f = []  # faces

    # Loop through SurfaceContainer object
    for srf in surface:
        # Tessellate surface
        vertices, triangles = tessellate.make_triangle_mesh(srf.evalpts, srf.sample_size.u, srf.sample_size.v)

        # Collect vertices
        for vert in vertices:
            temp = "v " + str(vert.x) + " " + str(vert.y) + " " + str(vert.z) + "\n"
            str_v.append(temp)

        # Collect parameter space vertices
        if include_param_vertex:
            for vert in vertices:
                temp = "vp " + str(vert.uv[0]) + " " + str(vert.uv[1]) + "\n"
                str_vp.append(temp)

        # Compute vertex normals
        if include_vertex_normal:
            for vert in vertices:
                sn = exc_helpers.surface_normal(srf, vert.uv, True)
                temp = "vn " + str(sn[1][0]) + " " + str(sn[1][1]) + " " + str(sn[1][2]) + "\n"
                str_vn.append(temp)

        # Collect faces (1-indexed)
        for t in triangles:
            vl = t.data
            temp = "f " + \
                   str(vl[0] + 1 + vertex_offset) + " " + \
                   str(vl[1] + 1 + vertex_offset) + " " + \
                   str(vl[2] + 1 + vertex_offset) + "\n"
            str_f.append(temp)

        # Update vertex offset
        vertex_offset = len(str_v)

    # Write all collected data to the return string
    for lv in str_v:
        line += lv
    for lvn in str_vn:
        line += lvn
    for lvp in str_vp:
        line += lvp
    for lf in str_f:
        line += lf

    return line


@export
def export_obj(surface, file_name, **kwargs):
    """ Exports surface(s) as a .obj file.

    Keyword Arguments:
        * ``vertex_spacing``: size of the triangle edge in terms of surface points sampled. *Default: 2*
        * ``vertex_normals``: if True, then computes vertex normals. *Default: False*
        * ``parametric_vertices``: if True, then adds parameter space vertices. *Default: False*

    :param surface: surface or surfaces to be saved
    :type surface: abstract.Surface or multi.SurfaceContainer
    :param file_name: name of the output file
    :type file_name: str
    :raises GeomdlException: an error occurred writing the file
    """
    return exc_helpers.write_file(file_name, export_obj_str(surface, **kwargs))
