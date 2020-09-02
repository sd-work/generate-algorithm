# coding: utf-8

import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs

from .node import Node
from .edge import Edge


class Cycle:

    def __init__(self, id, composition_nodes, is_on_gl=False):
        self.id = id
        self.id_text_guid = None
        self.cycle_mesh_guid = None
        self.centroid = None
        self.composition_nodes = composition_nodes
        self.is_on_GL = is_on_gl

    def generate_cycle_mesh(self, layer_name):
        # Generating cycle mesh
        cycle_mesh = Mesh()

        for node in self.composition_nodes:
            cycle_mesh.Vertices.Add(node.point)

        if len(self.composition_nodes) == 3:
            cycle_mesh.Faces.AddFace(0, 1, 2)
        elif len(self.composition_nodes) == 4:
            cycle_mesh.Faces.AddFace(0, 1, 2, 3)

        cycle_mesh.Normals.ComputeNormals()
        cycle_mesh.Compact()

        # Calculating the center of gravity
        self.centroid = AreaMassProperties.Compute(cycle_mesh).Centroid
        self.centroid = Point3d(self.centroid)

        # Draw cycle mesh in doc
        if layer_name == "r-cycle":
            layer = rs.AddLayer(str(len(self.id)), [255, 125, 0], True, False, layer_name)
        else:
            layer = rs.AddLayer(str(len(self.id)), [0, 125, 255], True, False, layer_name)

        self.cycle_mesh_guid = scriptcontext.doc.Objects.AddMesh(cycle_mesh)
        rs.ObjectLayer(self.cycle_mesh_guid, layer)

