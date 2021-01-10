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

        # About divided two edges -> main edge
        self.divided_two_edges = None
        self.divided_two_edges_guid = []
        self.mid_pt = None

        # About split edge line of master edge
        self.segmented_pts = []  # 分割点
        self.segmented_pts_on_master_edge = []  # 分割点
        self.section_crv_list_on_segmented_pts = []  # 分割点における部材の断面曲線(Curve)
        self.mid_pt_on_split_edges_line = None

        self.split_edges = []
        self.split_edges_guid = []

        self.split_edges_master_edge = []
        self.split_edges_guid_master_edge = []

        # About section
        self.section_id = None  # user text
        self.diameter_of_section = None  # 断面曲線の直径(m系で表記)

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

    # edge line guidをDoc空間に描画する
    def generate_edge_line(self, layer_name):
        self.edge_line_guid = scriptcontext.doc.Objects.AddCurve(self.edge_line)

    # edge line guidをDoc空間から削除する
    def delete_guid(self):
        rs.DeleteObject(self.edge_line_guid)

        for split_edge in self.split_edges_guid:
            rs.DeleteObject(split_edge)

        for split_edge in self.split_edges_guid_master_edge:
            rs.DeleteObject(split_edge)

        for edge in self.divided_two_edges_guid:
            if edge:
                rs.DeleteObject(edge)

        self.edge_line_guid = None
        self.split_edges_guid = []
        self.split_edges_guid_master_edge = []
        self.segmented_pts = []
        self.section_crv_list_on_segmented_pts = []
        self.divided_two_edges = []
        self.layer = None

    # master edge lineをn分割し、それらをchild edge lineとして情報を保持する
    def split_master_edge_to_segmented_edges(self, split_num=10):
        """master edgeが保持するsplit timberの中心線を分割し、その点座標を取得"""
        # 中心線のDomainを取得し、unit domain rangeを取得
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

        # 中心線を分割数の数だけ処理を行い、分割点、断面曲線を取得する
        for i in range(split_num + 1):
            segmented_pt = self.split_timber.center_line.PointAt((unit_range_domain * i) + domain[0])
            section_curve = self.split_timber.get_section_of_timber(segmented_pt, origin_vec)  # 分割点での断面曲線を取得

            # 各情報を保持
            self.segmented_pts.append(segmented_pt)
            self.section_crv_list_on_segmented_pts.append(section_curve)

        # split edge guidを生成
        for i in range(len(self.segmented_pts) - 1):
            line = Line(self.segmented_pts[i], self.segmented_pts[i + 1])
            self.split_edges.append(line)

            line_guid = scriptcontext.doc.Objects.AddLine(line)
            self.split_edges_guid.append(line_guid)

        """master edge lineを分割し、その点座標を取得"""
        domain = self.edge_line.Domain
        unit_range_domain = (domain[1] - domain[0]) / split_num

        # master edgeを分割数の数だけ分割し、分割点・segmented edgeを取得する
        for i in range(split_num + 1):
            segmented_pt = self.edge_line.PointAt((unit_range_domain * i) + domain[0])

            # 情報を保持
            self.segmented_pts_on_master_edge.append(segmented_pt)

        # Sort
        from_pt = self.segmented_pts[0]
        to_pt1 = self.segmented_pts_on_master_edge[0]
        to_pt2 = self.segmented_pts_on_master_edge[-1]

        dis1 = Point3d.DistanceTo(from_pt, to_pt1)
        dis2 = Point3d.DistanceTo(from_pt, to_pt2)

        if dis1 < dis2:
            pass
        else:
            self.segmented_pts_on_master_edge.reverse()

        # split edge on master edgeを生成
        for i in range(len(self.segmented_pts_on_master_edge) - 1):
            line = Line(self.segmented_pts_on_master_edge[i], self.segmented_pts_on_master_edge[i + 1])
            self.split_edges_master_edge.append(line)

            line_guid = scriptcontext.doc.Objects.AddLine(line)
            self.split_edges_guid_master_edge.append(line_guid)

    def calc_diameter_of_section(self, index):

        # Todo 円周長さから求めるのではなく、断面曲線から直接長さを取得する
        section_crv = self.section_crv_list_on_segmented_pts[index]
        crv_length = section_crv.GetLength()
        diameter = crv_length / math.pi  # 直径(mm系)
        diameter = diameter * (10 ** -3)  # m(メートル)に変換する
        diameter = round(diameter, 3)  # 小数点以下3桁(小数点第四位を四捨五入)

        return diameter

    def calc_average_diameter_of_section(self):
        diameter_list = []

        for crv in self.section_crv_list_on_segmented_pts:
            # Todo 円周長さから求めるのではなく、断面曲線から直接長さを取得する
            crv_length = crv.GetLength()
            diameter = crv_length / math.pi
            diameter_list.append(diameter)

        # 直径情報を保存する
        self.diameter_of_section = int(sum(diameter_list) / len(diameter_list))
        self.diameter_of_section = self.diameter_of_section * (10 ** -3)  # m(メートル)に変換する
        self.diameter_of_section = round(self.diameter_of_section, 3)  # 小数点以下3桁(小数点第四位を四捨五入)

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

    def get_boundary_pt(self):
        boundary_pt = None

        if self.start_node.structural_type == 1:
            boundary_pt = self.start_node.point

        elif self.end_node.structural_type == 1:
            boundary_pt = self.end_node.point

        return boundary_pt

    def divide_edge_two_edge(self, split_num):
        """Master Line Frame"""
        # get mid point of master edge
        domain = self.edge_line.Domain
        unit_range_domain = (domain[1] - domain[0]) / split_num
        index = int(round(split_num / 2))
        self.mid_pt = self.edge_line.PointAt(unit_range_domain * index)

        # split master edge to 2 edge on mid pt
        self.divided_two_edges = self.edge_line.Split(unit_range_domain * index)

        for divided_edge in self.divided_two_edges:
            edge_guid = scriptcontext.doc.Objects.AddCurve(divided_edge)
            self.divided_two_edges_guid.append(edge_guid)

        # main master edgeを2分割し、分割された2つのedge lineをlayerに割り当てる
        master_split_layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, "split_main")

        for i, divided_edge_guid in enumerate(self.divided_two_edges_guid):
            layer_name = "s" + "-" + str(self.id) + "-" + str(i)
            layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_split_layer)

            rs.ObjectLayer(divided_edge_guid, layer)  # set object layer
            rs.ObjectColor(divided_edge_guid, [0, 0, 255])  # Blue

        """Segmented Polyline Frame"""
        # get mid point of split edges line
        index = int(round(split_num / 2))
        self.mid_pt_on_split_edges_line = self.segmented_pts[index]  # 分割数を10として設定しているから5


