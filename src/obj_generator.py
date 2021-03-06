#!/usr/bin/python
# -*- coding: utf-8 -*-
from filereader3db import *
import os
import numpy as np


class Vertex:
    def __init__(self, x, y, z):
        self.vertices = np.array([x, y, z, 1])

    def scale_vertex(self, scale):
        identity = np.identity(4)
        for i in range(3):
            identity[i][i] = scale

        self.vertices = identity.dot(self.vertices)

    def get_formatted_vertex_list(self):
        return f"{format(self.vertices[0], 'f')} {format(self.vertices[1], 'f')} {format(self.vertices[2], 'f')} "

    def __str__(self):
        return f"Vertex X={self.vertices[0]} Y={self.vertices[1]} Z={self.vertices[2]}"

    def __repr__(self):
        return f"Vertex X={self.vertices[0]} Y={self.vertices[1]} Z={self.vertices[2]}"

    def translate(self, matrix: np.ndarray):
        self.vertices = matrix.dot(self.vertices)


class TextureCoords:

    def __init__(self, u, v):
        self.u = u
        self.v = v

    def get_formatted_texture_coord_list(self):
        return f"{format(self.u, 'f')} {format(self.v, 'f')}"

    def __str__(self):
        return f"TextureCoord U={self.u} V={self.v}"

    def __repr__(self):
        return f"TextureCoord U={self.u} V={self.v}"


class Material:

    def __init__(self, material: Dict):
        self.diffuse = Vertex(*self.get_constant(material['Diffuse']))
        self.ambient = Vertex(*self.get_constant(material['Ambient']))
        self.specular = Vertex(*self.get_constant(material['Specular']))
        if 'Shininess' in material:
            self.shininess = self.get_constant(material['Shininess'])[0]
        else:
            self.shininess = None
        self.name = str(material['name']).replace(" ", "_").replace("#", "_")
        self.id = get_as_int_list(material['Material identifier']['value'])[0]
        self.has_texture = False
        if 'Map' in material['Diffuse']:
            basename = get_as_string(material['Diffuse']['Map']['Name']['value']).split(".")
            if len(basename) > 1:
                filename = basename[0]
                self.diffuse_map = filename + "_color.tga"
                self.bump_map = filename + "_bump.tga"
                self.has_texture = True

    def get_constant(self, material):
        if "Constant" in material:
            return get_as_float_list(material['Constant']['value'])
        else:
            return get_as_float_list(material['value'])


class FaceGroup:

    def __init__(self, face_group):
        self.vertex_chain = get_as_int_list(face_group['Face vertex chain']['value'])
        self.material_index = get_as_int_list(face_group['Material']['value'])[0]


class ObjModel:

    def __init__(self):
        self.vertices = []
        self.face_groups = []
        self.surface_normals = []
        self.vertex_batch_list = []
        self.texture_coord_list = []
        self.vertex_normals = []
        self.texture_batch_list = []
        self.materials: List[Material] = []

    def export_to_obj(self, mesh, path, scale=1, translation_matrix=np.identity(4)):
        # mesh = self.model['\\']['openFLAME 3D N-mesh']

        self.create_vertices(mesh)

        self.create_face_groups(mesh)

        self.create_normals(mesh)

        self.create_texture_coordinates(mesh)

        self.vertex_batch_list = get_as_int_list(mesh['Vertices']['Vertex batch list']['value'])

        basename = str(os.path.basename(path)).split(".")[0]
        material_filename = basename + ".mtl"
        self.create_materials(mesh)

        with open(path, "w") as outfile:
            outfile.write(f"mtllib {material_filename}\n\n")
            for vertex in self.vertices:
                vertex.translate(translation_matrix)
                vertex.scale_vertex(scale)
                s = "v " + vertex.get_formatted_vertex_list()
                outfile.write(s + "\n")

            outfile.write(f"#{len(self.vertices)} Vertices \n\n")

            for texture_coord in self.texture_coord_list:
                s = "vt " + texture_coord.get_formatted_texture_coord_list()
                outfile.write(s + "\n")
            outfile.write(f"#{len(self.texture_coord_list)} Texture Coordinates \n\n")

            for vertex in self.surface_normals:
                s = "vn " + vertex.get_formatted_vertex_list()
                outfile.write(s + "\n")

            outfile.write(f"#{len(self.surface_normals)} Normals \n\n")

            triangles = 0
            outfile.write(f"o {basename}\n")
            for face_group_index in range(len(self.face_groups)):
                face_group: FaceGroup = self.face_groups[face_group_index]
                chain = face_group.vertex_chain
                outfile.write(f"g FaceGroup{face_group_index}\n")
                outfile.write(f"usemtl {self.materials[face_group.material_index].name}\n")
                for i, index in enumerate(range(0, len(chain), 3)):
                    vertex_1 = self.vertex_batch_list[chain[index]] + 1
                    vertex_2 = self.vertex_batch_list[chain[index + 1]] + 1
                    vertex_3 = self.vertex_batch_list[chain[index + 2]] + 1
                    uv_1 = self.texture_batch_list[chain[index]] + 1
                    uv_2 = self.texture_batch_list[chain[index + 1]] + 1
                    uv_3 = self.texture_batch_list[chain[index + 2]] + 1
                    normal_1 = self.vertex_normals[vertex_1 - 1] + 1
                    normal_2 = self.vertex_normals[vertex_2 - 1] + 1
                    normal_3 = self.vertex_normals[vertex_3 - 1] + 1
                    outfile.write(
                        f"f {vertex_1}/{uv_1}/{normal_1} {vertex_2}/{uv_2}/{normal_2} {vertex_3}/{uv_3}/{normal_3} \n")
                    triangles += 1

            outfile.write("#%d Faces" % triangles)

        with open(os.path.join(os.path.dirname(path), material_filename), "w") as outfile:
            for mat in self.materials:
                outfile.write(f"newmtl {mat.name}\n")
                outfile.write(f"Ka {mat.ambient.get_formatted_vertex_list()}\n")
                outfile.write(f"Kd {mat.diffuse.get_formatted_vertex_list()}\n")
                outfile.write(f"Ks {mat.specular.get_formatted_vertex_list()}\n")
                outfile.write(f"illum 2\n")
                if mat.shininess:
                    outfile.write(f"Ns {mat.shininess * 50}\n")

                if mat.has_texture:
                    outfile.write(f"map_Kd {mat.diffuse_map}\n")
                    outfile.write(f"map_Bump {mat.bump_map}\n")

                outfile.write("\n")

    def create_normals(self, mesh):
        data = get_as_float_list(mesh['Normals']['Surface normal list']['value'])
        for i in range(0, len(data), 3):
            self.surface_normals.append(Vertex(float(data[i]), float(data[i + 1]), float(data[i + 2])))
        self.vertex_normals = get_as_int_list(mesh['Vertices']['Vertex normal']['value'])

    def create_face_groups(self, mesh):
        face_group_count = get_as_int_list(mesh['Face groups']['Count']['value'])[0]
        for i in range(face_group_count):
            face_group = mesh['Face groups'][f'Group{i}']
            self.face_groups.append(FaceGroup(face_group))

    def create_vertices(self, mesh):
        data = get_as_float_list(mesh['Vertices']['Object vertex list']['value'])
        for i in range(0, len(data), 3):
            self.vertices.append(Vertex(float(data[i]), float(data[i + 1]), float(data[i + 2])))
        self.texture_batch_list = get_as_int_list(mesh['Vertices']['Texture batch list']['value'])

    def create_texture_coordinates(self, mesh):
        data = get_as_float_list(mesh['Vertices']['Texture vertex list']['value'])
        for i in range(0, len(data), 2):
            self.texture_coord_list.append(TextureCoords(float(data[i]), float(data[i + 1])))

    def create_materials(self, mesh):
        material_lib = mesh['Material library']
        for key in material_lib.keys():
            if key not in ['name', 'value', 'text', 'Material count']:
                self.materials.append(Material(material_lib[key]))
