# coding: utf-8

import copy
import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs


class Graph:

    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        self.contiguous_list = []
        self.cycles = []
        self.cycles_guid = []

    def set_graph(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def create_graph(self):
        self.contiguous_list = []

        for node in self.nodes:
            self.contiguous_list.append(node.connected_nodes)

        print(self.contiguous_list)

    def get_edge_from_test_point(self, test_pt):
        edge_to_get = None
        min_distance = 10000

        for edge in self.edges:
            distance = edge.edge_line.DistanceTo(test_pt, True)

            if distance < min_distance:
                min_distance = distance
                edge_to_get = edge
            else:
                continue

        return edge_to_get

    @staticmethod
    def get_closest_node_from_test_point(test_pt, reference_pts):
        node_to_get = None
        min_distance = 10000

        for reference_pt in reference_pts:
            distance = Point3d.DistanceTo(test_pt, reference_pt.point)

            if distance < min_distance:
                min_distance = distance
                node_to_get = reference_pt
            else:
                continue

        return node_to_get

    def generate_cycle(self, cycles, nodes_in_playground):

        for cycle in cycles:
            if cycle in self.cycles:
                continue

            self.cycles.append(cycle)

            layer = rs.AddLayer(str(len(self.cycles)), [255, 125, 0], True, False, "cycle")

            mesh_cycle = Mesh()
            mesh_cycle.Vertices.Add(nodes_in_playground[cycle[0]].point)
            mesh_cycle.Vertices.Add(nodes_in_playground[cycle[1]].point)
            mesh_cycle.Vertices.Add(nodes_in_playground[cycle[2]].point)

            mesh_cycle.Faces.AddFace(0, 1, 2)

            mesh_cycle.Normals.ComputeNormals()
            mesh_cycle.Compact()

            mesh_cycle_guid = scriptcontext.doc.Objects.AddMesh(mesh_cycle)
            self.cycles_guid.append(mesh_cycle_guid)

            rs.ObjectLayer(self.cycles_guid, layer)
