# coding: utf-8

import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs


class Node:

    def __init__(self, id, point, nodes_of_real_graph=None, is_on_gl=False):
        self.id = id
        self.point = point  # rhino common
        self.x = point.X
        self.y = point.Y
        self.z = point.Z
        self.coordinate_on_GL = [self.x, self.y, 0]  # Nodeの点を地面に投影した点
        self.connected_nodes = []  # Nodeが接続しているNode instances

        self.having_edges = []  # Nodeが保持しているエッジ群
        self.is_on_GL = is_on_gl  # NodeがGLに接続しているかどうかを判定するフラグ

        # About guid
        self.point_guid = None
        self.dot_text_guid = None

        # About structural model
        self.structural_type = -1  # 0: 自由端 1: 支点 2: 接合点

        # About contact point which is joint point
        self.contact_pt = None
        self.timbers_on_contact_pt = []  # timbers which is on joint point

        # About bolt
        self.bolt = None  # 接合点である場合、接合部におけるBolt instance情報を保持する
        self.ends_pt_of_bolt = []  # boltの両端部の座標値
        self.ends_pt_of_bolt_1 = None  # boltの端部1
        self.ends_pt_of_bolt_2 = None  # boltの端部2

        # Variables specific to virtual graph
        # self.nodes_of_real_graph = nodes_of_real_graph  # Nodes of Real graph that make up a node of Virtual graph
        # self.missing_edges = []  # Missing edges when trying to convert a real graph to a virtual graph
        # self.having_edges_to_virtual_node = []  # virtual node to virtual node which created by 3 real graph node
        # self.having_edges_to_leaf_node = []  # virtual node to leaf node

    # Rhino空間上に描画する
    def generate_node_point(self, layer_name):
        # add node point
        self.point_guid = scriptcontext.doc.Objects.AddPoint(self.point)
        rs.ObjectLayer(self.point_guid, layer_name)

        # add dot text
        layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, layer_name)
        self.dot_text_guid = scriptcontext.doc.Objects.AddTextDot(str(self.id), self.point)
        rs.ObjectLayer(self.dot_text_guid, layer)

    def set_timbers_on_contact_pt(self, timbers):
        for timber in timbers:
            if timber in self.timbers_on_contact_pt:
                continue
            else:
                self.timbers_on_contact_pt.append(timber)

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

    def judge_node_on_ground(self):
        gl_nodes = []

        for node in self.connected_nodes:
            if -60 < node.z < 60:
                gl_nodes.append(node)

        if len(gl_nodes) == 2:
            # Record the nodes to which each node is connected
            gl_nodes[0].connected_nodes.append(gl_nodes[1])
            gl_nodes[0].connected_nodes.sort()

            gl_nodes[1].connected_nodes.append(gl_nodes[0])
            gl_nodes[1].connected_nodes.sort()

            return gl_nodes
        else:
            return False

    def set_having_edge(self, edges):
        for edge in edges:
            if edge in self.having_edges:
                continue
            else:
                self.having_edges.append(edge)

    def set_having_edges_to_virtual_node(self, edges):
        for edge in edges:
            if edge in self.having_edges_to_virtual_node:
                continue
            else:
                self.having_edges_to_virtual_node.append(edge)

    def set_having_edges_to_leaf_node(self, edges):
        for edge in edges:
            if edge in self.having_edges_to_leaf_node:
                continue
            else:
                self.having_edges_to_leaf_node.append(edge)