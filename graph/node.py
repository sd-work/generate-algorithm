# coding: utf-8

import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs



class Node:

    def __init__(self, id, point):
        self.id = id
        self.point = point  # rhino common
        self.point_guid = None
        self.dot_text_guid = None
        self.x = point.X
        self.y = point.Y
        self.z = point.Z
        self.connected_nodes = []

    # Rhino空間上に描画する
    def generate_node_point(self):
        # add node point
        self.point_guid = scriptcontext.doc.Objects.AddPoint(self.point)
        rs.ObjectLayer(self.point_guid, "node")

        # add dot text
        layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, "node")
        self.dot_text_guid = scriptcontext.doc.Objects.AddTextDot(str(self.id), self.point)
        rs.ObjectLayer(self.dot_text_guid, layer)

    def set_connected_nodes(self, nodes):
        if isinstance(nodes, list):
            self.connected_nodes = []
            self.connected_nodes = nodes
            self.connected_nodes.sort()
        else:
            self.connected_nodes = []
            self.connected_nodes.append(nodes)

    def sort_connected_nodes(self):
        self.connected_nodes.sort()

    def judge_node_on_ground(self, nodes_in_playground):
        gl_nodes = []
        for node_id in self.connected_nodes:
            if -30 < nodes_in_playground[node_id].z < 30:
                gl_nodes.append(nodes_in_playground[node_id])

        if len(gl_nodes) == 2:
            # Record the nodes to which each node is connected
            gl_nodes[0].connected_nodes.append(gl_nodes[1].id)
            gl_nodes[0].connected_nodes.sort()

            gl_nodes[1].connected_nodes.append(gl_nodes[0].id)
            gl_nodes[1].connected_nodes.sort()

            return gl_nodes

        else:
            return False




















