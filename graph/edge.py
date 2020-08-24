# coding: utf-8

import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs

class Edge:

    def __init__(self, id, node1, node2):
        self.id = id
        self.start_node = node1
        self.end_node = node2
        self.edge_line = Line(node1.point, node2.point)
        self.edge_line_guid = None
        self.weight = 0

    def generate_edge_line(self):
        # add edge line
        self.edge_line_guid = scriptcontext.doc.Objects.AddLine(self.edge_line)
        rs.ObjectLayer(self.edge_line_guid, "edge")

    def delete_guid(self):
        rs.DeleteObject(self.edge_line_guid)

