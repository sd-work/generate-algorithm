# coding: utf-8

import copy
import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs

from .node import Node
from .edge import Edge


class Cycle:

    def __init__(self, id, cycle, composition_nodes, is_on_gl=False):
        self.id = id
        self.id_text_guid = None
        self.cycle_mesh_guid = None
        self.centroid = None
        self.cycle = cycle
        self.composition_nodes = composition_nodes  # node instance
        self.is_on_GL = is_on_gl

    def generate_cycle_mesh(self, layer_name):
        # Generating cycle mesh
        cycle_mesh = Mesh()

        print("composition_nodes num: {0}".format(len(self.composition_nodes)))

        for node in self.composition_nodes:
            cycle_mesh.Vertices.Add(node.point)

        if len(self.composition_nodes) == 3:
            cycle_mesh.Faces.AddFace(0, 1, 2)
        elif len(self.composition_nodes) == 4:
            cycle_mesh.Faces.AddFace(0, 1, 2, 3)

        else:  # メッシュの構成点が5つ以上の場合
            # TODO メッシュの最小分割面は三角形になるので、それを念頭においておく
            # TODO Message: AddFace() takes at most 4 arguments (6 given)
            if len(self.composition_nodes) == 5:
                cycle_mesh.Faces.AddFace(0, 1, 2, 3, 4)

            elif len(self.composition_nodes) == 6:
                cycle_mesh.Faces.AddFace(0, 1, 2, 5)
                cycle_mesh.Faces.AddFace(2, 3, 4, 5)

            elif len(self.composition_nodes) == 7:
                cycle_mesh.Faces.AddFace(0, 1, 2, 3, 4, 5, 6)

        cycle_mesh.Normals.ComputeNormals()
        cycle_mesh.Compact()

        # Calculating the center of gravity
        self.centroid = AreaMassProperties.Compute(cycle_mesh).Centroid
        self.centroid = Point3d(self.centroid)

        # Draw cycle mesh in doc
        if layer_name == "r-cycle":
            layer = rs.AddLayer(self.id, [255, 125, 0], True, False, layer_name)
        elif layer_name == "v-cycle":
            layer = rs.AddLayer(self.id, [0, 125, 255], True, False, layer_name)
        else:
            layer = None

        self.cycle_mesh_guid = scriptcontext.doc.Objects.AddMesh(cycle_mesh)
        rs.ObjectLayer(self.cycle_mesh_guid, layer)

    def delete_cycle_guid(self):
        rs.DeleteObject(self.cycle_mesh_guid)

    @staticmethod
    def determine_subset_of_two_cycles(test_cycle_nodes, generated_cycles):
        delete_cycles = []

        for generated_cycle in generated_cycles:
            temp_test_composition_nodes = copy.copy(test_cycle_nodes)
            temp_generated_composition_nodes = copy.copy(generated_cycle.composition_nodes)

            for generated_composition_node in generated_cycle.composition_nodes:

                if generated_composition_node in temp_test_composition_nodes:
                    temp_test_composition_nodes.remove(generated_composition_node)  # delete from list
                    temp_generated_composition_nodes.remove(generated_composition_node)  # delete from list

            # print(temp_test_composition_nodes)
            # print(temp_generated_composition_nodes)

            # judge subset of test_cycle and generated cycle
            if (len(temp_test_composition_nodes) >= 1) and (not temp_generated_composition_nodes):
                # Delete old cycle
                generated_cycle.delete_cycle_guid()
                delete_cycles.append(generated_cycle)

        return delete_cycles
