# coding: utf-8

import copy
import Rhino
import scriptcontext
import rhinoscriptsyntax as rs
from .triangle import Triangle
from .point import Point
from graph.edge import Edge

# from point import Point
# from triangle import Triangle


def delaunay_triangulation(gl_nodes):
    temp_points = []  # Pointインスタンスを保持するリスト
    divided_triangle_list = []  # 三角形分割された三角形を保持するリスト
    base_points_list = []

    # ドロネー分割する点群を取得する
    for gl_node in gl_nodes:
        point = Point(gl_node.coordinate_on_GL, gl_node)

        temp_points.append(point)
        base_points_list.append(point)

    # for point in gl_nodes:
    #     point = Point(point)
    #     temp_points.append(point)
    #     base_points_list.append(point)

    # はじめの外接円を構成する点のインスタンス作成。この範囲内に点群を収めておく必要あり
    P1 = Point([-100000, -100000, 0])
    P2 = Point([100000, -100000, 0])
    P3 = Point([0, 73000, 0])

    triangle = Triangle(P1, P2, P3)
    triangle.cul_center_coordinate_and_radius()

    divided_triangle_list.append(triangle)

    # ドロネー分割のメインアルゴリズム
    for _ in range(len(temp_points)):

        # 追加するPointを選択
        select_point = temp_points.pop(0)

        temp_divided_triangle = []
        for triangle in divided_triangle_list:
            # 三角形の外接円内に新たに追加するPointが内包されているかどうかを判定。内包されている場合はindexを保存。
            judge = triangle.judge_test_point_in_circumscribed_circle(select_point)

            if judge:
                # 新たに追加するPointを頂点として使用し、元の三角形を分割。そして新たな三角形を生成する
                new_triangle1 = Triangle(triangle.p1, triangle.p2, select_point)
                new_triangle2 = Triangle(triangle.p2, triangle.p3, select_point)
                new_triangle3 = Triangle(triangle.p1, triangle.p3, select_point)
                new_triangle1.cul_center_coordinate_and_radius()
                new_triangle2.cul_center_coordinate_and_radius()
                new_triangle3.cul_center_coordinate_and_radius()

                # 新たに生成された三角形をリストに追加する
                temp_divided_triangle += new_triangle1, new_triangle2, new_triangle3

                # 分割に使用した三角形は削除する
                divided_triangle_list.remove(triangle)
            else:
                continue

        # 新たに生成された三角形をリストに追加する
        for new_triangle in temp_divided_triangle:
            divided_triangle_list.append(new_triangle)

    # 重複している三角形を削除
    for new_triangle in divided_triangle_list:
        for check_triangle in divided_triangle_list:
            if new_triangle == check_triangle:
                continue
            if new_triangle.center_p == check_triangle.center_p:
                divided_triangle_list.remove(check_triangle)

    # 最初の大きな三角形を構成する頂点を含む三角形は必要ないので、はじく
    desired_triangle_list = []
    for triangle in divided_triangle_list:
        if P1 in triangle.vertex or P2 in triangle.vertex or P3 in triangle.vertex:
            continue
        desired_triangle_list.append(triangle)

        # debug
        triangle.draw_divide_triangle()

    # 三角形を構成する頂点情報から隣接関係を取り出し、virtual nodeにその情報を渡す
    for point in base_points_list:
        for triangle in desired_triangle_list:

            if point in triangle.vertex:
                temp_vertex = copy.copy(triangle.vertex)
                temp_vertex.remove(point)

                for connected_pt in temp_vertex:
                    if connected_pt in point.connected_points:
                        continue
                    point.connected_points.append(connected_pt)

    return_edges = []
    for point in base_points_list:

        current_virtual_node = point.virtual_node

        for connected_pt in point.connected_points:
            connected_node = connected_pt.virtual_node

            # Record the nodes to which each node is connected
            if not (connected_node in current_virtual_node.connected_nodes):
                current_virtual_node.connected_nodes.append(connected_node)  # about Node

                if not (current_virtual_node in connected_node.connected_nodes):
                    connected_node.connected_nodes.append(current_virtual_node)  # about Node

                    # Edge Instance
                    id = str(current_virtual_node.id) + "-" + str(connected_node.id)
                    edge_on_gl = Edge(id, current_virtual_node, connected_node, None)

                    return_edges.append(edge_on_gl)

                    # Virtual Nodeが保持するエッジ群に新たに生成したエッジ情報を格納する
                    current_virtual_node.set_having_edge([edge_on_gl])
                    connected_node.set_having_edge([edge_on_gl])

                    # Virtual Nodeへのエッジ情報を格納する
                    current_virtual_node.set_having_edges_to_virtual_node([edge_on_gl])
                    connected_node.set_having_edges_to_virtual_node([edge_on_gl])

    return return_edges

# if __name__ == "__main__":
#     points = rs.GetObjects("pick up some points", rs.filter.point)
#
#     temp_points = []
#     for p in points:
#         p = rs.coerce3dpoint(p)
#         temp_points.append([p[0], p[1], p[2]])
#
#     delaunay_triangulation(temp_points)
