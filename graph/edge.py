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
        self.timber = timber  # Timber instance
        self.split_timber = None  # split timber surface

        # Variables specific to virtual graph
        self.real_edge = None
        self.is_on_virtual_cycle = False  # EdgeがVirtual cycleを構成するエッジ上にのっているかどうかの判定フラグ

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

        self.edge_line_guid = None

    @staticmethod
    def check_edge_in_edge_list(node1, node2, edge_list):
        if node1.id < node2.id:
            start_node = node1
            end_node = node2
        else:
            start_node = node2
            end_node = node1

        check_id = str(start_node.id) + "-" + str(end_node.id)

        for edge in edge_list:
            if check_id == edge.id:
                print("Already generated")
                return True

        return False

    @staticmethod
    def record_split_timber_to_edge(edge1, edge2, split_timbers):
        test_pt = edge1.start_node.point

        rc, u1, v1 = Surface.ClosestPoint(split_timbers[0].surface, test_pt)
        rc, u2, v2 = Surface.ClosestPoint(split_timbers[1].surface, test_pt)

        to_point1 = split_timbers[0].surface.PointAt(u1, v1)
        to_point2 = split_timbers[1].surface.PointAt(u2, v2)

        dis1 = Point3d.DistanceTo(test_pt, Point3d(to_point1[0], to_point1[1], to_point1[2]))
        dis2 = Point3d.DistanceTo(test_pt, Point3d(to_point2[0], to_point2[1], to_point2[2]))

        if dis1 < dis2:
            # print("edge1 id: {0} | split timber: {1}".format(edge1.id, split_timbers[0].id))
            # print("edge2 id: {0} | split timber: {1}".format(edge2.id, split_timbers[1].id))

            # TODO Record the split timber in edge
            edge1.split_timber = split_timbers[0]
            edge2.split_timber = split_timbers[1]

            # TODO Record the edges which split timber has
            split_timbers[0].set_having_edge([edge1])
            split_timbers[1].set_having_edge([edge2])

            # rs.ObjectColor(edge1.split_timber.surface_guid, [223, 51, 78])  # 赤色

        else:
            # print("edge1 id: {0} | split timber: {1}".format(edge1.id, split_timbers[1].id))
            # print("edge2 id: {0} | split timber: {1}".format(edge2.id, split_timbers[0].id))

            # TODO Record the split timber in edge
            edge1.split_timber = split_timbers[1]
            edge2.split_timber = split_timbers[0]

            # TODO Record the edges which split timber has
            split_timbers[0].set_having_edge([edge2])
            split_timbers[1].set_having_edge([edge1])

            # rs.ObjectColor(edge1.split_timber.surface_guid, [223, 51, 78])  # 赤色
