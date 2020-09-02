# coding: utf-8

import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs

class Edge:

    def __init__(self, id, node1, node2, timber):
        self.id = id
        if node1.id < node2.id:
            self.start_node = node1
            self.end_node = node2
        else:
            self.start_node = node2
            self.end_node = node1
            self.id = str(self.start_node.id) + "-" + str(self.end_node.id)

        self.edge_line = Line(node1.point, node2.point)
        self.edge_line_guid = None
        self.timber = timber

        # Variables specific to virtual graph
        self.real_edge = None


    def generate_edge_line(self, layer_name):
        # add edge line
        if layer_name == "r-edge":
            layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, layer_name)
        elif layer_name == "v-edge":
            layer = rs.AddLayer(str(self.id), [0, 0, 255], True, False, layer_name)
        else:
            layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, layer_name)

        self.edge_line_guid = scriptcontext.doc.Objects.AddLine(self.edge_line)
        rs.ObjectLayer(self.edge_line_guid, layer)

    def delete_guid(self):
        rs.DeleteObject(self.edge_line_guid)

