# coding: utf-8

import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs
import math
import copy


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

        # About divided two edges
        self.divided_two_edges = None
        self.divided_pt = None

        # About section
        self.section_id = None  # user text
        self.diameter_of_section = None  # 断面曲線の直径(mで表記)

        # About layer
        self.layer = None

        # About line
        self.edge_line = LineCurve(node1.point, node2.point)  # Rhino common

        # About Timber
        self.timber = timber  # master timber instance
        self.split_timber = None  # split timber instance

        # About Guid
        self.edge_line_guid = None

        # Variables specific to virtual graph
        self.real_edge = None
        self.is_on_virtual_cycle = False  # EdgeがVirtual cycleを構成するエッジ上にのっているかどうかの判定フラグ

    def generate_edge_line(self, layer_name):
        # add edge line
        if layer_name == "r-edge":
            self.layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, layer_name)
        elif layer_name == "v-edge":
            self.layer = rs.AddLayer(str(self.id), [0, 0, 255], True, False, layer_name)
        else:
            pass
            # self.layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, layer_name)

        self.edge_line_guid = scriptcontext.doc.Objects.AddCurve(self.edge_line)
        # rs.ObjectLayer(self.edge_line_guid, self.layer)

    def delete_guid(self):
        rs.DeleteObject(self.edge_line_guid)
        # rs.DeleteLayer(self.layer)

        self.edge_line_guid = None
        self.layer = None

    def calc_diameter_of_section(self):
        # edgeが保持するsplit timberの中心線を分割し、その点座標を取得
        split_num = 10

        domain = self.split_timber.center_line.Domain
        range_domain = domain[1] - domain[0]
        unit_range_domain = range_domain / split_num

        # 基準ベクトルを作成
        domain_u = self.split_timber.surface.Domain(0)  # 高さ方向

        from_pt = self.split_timber.center_line.PointAtStart
        rc, u_parameter, v_parameter = self.split_timber.surface.ClosestPoint(from_pt)
        to_pt = self.split_timber.surface.PointAt(domain_u[0], v_parameter)

        origin_vec = Vector3d(from_pt - to_pt)
        origin_vec.Unitize()  # 正規化
        origin_vec = Vector3d.Multiply(origin_vec, 1000)  # 一般化

        # 中心線の分割点だけ処理を行い、断面情報を取得する
        section_list = []
        for i in range(split_num):
            test_pt = self.split_timber.center_line.PointAt((unit_range_domain * i) + domain[0])
            section_curve = self.split_timber.get_section_of_timber(test_pt, origin_vec)  # 任意の点での断面情報を取得する
            section_list.append(section_curve)

        diameter_list = []
        for crv in section_list:
            crv_length = crv.GetLength()
            diameter = crv_length / math.pi
            diameter_list.append(diameter)

        # 直径情報を保存する
        self.diameter_of_section = int(sum(diameter_list) / len(diameter_list))
        self.diameter_of_section = self.diameter_of_section * (10 ** -3)  # mに変換する

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

    def set_user_text(self):
        if self.edge_line_guid:
            rs.SetUserText(self.edge_line_guid, "joint", "3")  # joint
            rs.SetUserText(self.edge_line_guid, "sec", str(self.section_id))  # section id

    def get_free_end_coordinate(self):
        free_end_coordinate = None
        support_pt_coordinate = None

        if self.start_node.structural_type == 0:
            free_end_coordinate = self.start_node.point  # Point3d
            support_pt_coordinate = self.end_node.point  # Point3d

        if self.end_node.structural_type == 0:
            free_end_coordinate = self.end_node.point  # Point3d
            support_pt_coordinate = self.start_node.point  # Point3d

        return free_end_coordinate, support_pt_coordinate

    def divide_edge_two_edge(self):
        # split two edge in mid pt
        domain = self.edge_line.Domain
        t = (domain[1] - domain[0]) / 2
        self.divided_two_edges = self.edge_line.Split(t)

        # mid pt coordinate
        self.divided_pt = self.edge_line.PointAt(t)

        return self.divided_two_edges

















