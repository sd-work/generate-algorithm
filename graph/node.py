# coding: utf-8

import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs


class Node:

    def __init__(self, id, point, nodes_of_real_graph=None, is_on_gl=False):
        self.id = id
        self.point = point  # rhino common
        self.point_guid = None
        self.dot_text_guid = None
        self.x = point.X
        self.y = point.Y
        self.z = point.Z
        self.connected_nodes = []  # node instances

        self.having_edges = []  # Nodeが保持しているエッジ群
        self.is_on_GL = is_on_gl  # NodeがGLに説獄しているかどうかを判定するフラグ

        # Variables specific to virtual graph
        self.nodes_of_real_graph = nodes_of_real_graph  # Nodes of Real graph that make up a node of Virtual graph
        self.missing_edges = []  # Missing edges when trying to convert a real graph to a virtual graph

    # Rhino空間上に描画する
    def generate_node_point(self, layer_name):
        # add node point
        self.point_guid = scriptcontext.doc.Objects.AddPoint(self.point)
        rs.ObjectLayer(self.point_guid, layer_name)

        # add dot text
        layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, layer_name)
        self.dot_text_guid = scriptcontext.doc.Objects.AddTextDot(str(self.id), self.point)
        rs.ObjectLayer(self.dot_text_guid, layer)

    def set_connected_nodes(self, nodes):
        if isinstance(nodes, list):
            self.connected_nodes = []
            self.connected_nodes = nodes
        else:
            self.connected_nodes = []
            self.connected_nodes.append(nodes)

            # if nodes in self.connected_nodes:
            #     pass
            # else:
            #     self.connected_nodes.append(nodes)

    def sort_connected_nodes(self):
        temp_connected_nodes = []

        for connected_node in self.connected_nodes:
            temp_connected_nodes.append([connected_node.id, connected_node])

        # sort
        temp_connected_nodes.sort(key=lambda x: x[0])

        self.connected_nodes = []
        for connected_node in temp_connected_nodes:
            self.connected_nodes.append(connected_node[1])

    def judge_node_on_ground(self, nodes_in_playground):
        gl_nodes = []

        for node in self.connected_nodes:
            if -40 < nodes_in_playground[node.id].z < 40:
                gl_nodes.append(nodes_in_playground[node.id])

        if len(gl_nodes) == 2:
            # Record the nodes to which each node is connected
            gl_nodes[0].connected_nodes.append(gl_nodes[1])
            gl_nodes[0].connected_nodes.sort()

            gl_nodes[1].connected_nodes.append(gl_nodes[0])
            gl_nodes[1].connected_nodes.sort()

            return gl_nodes

        else:
            return False


