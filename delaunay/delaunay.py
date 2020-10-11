# coding: utf-8

import copy
import Rhino
from Rhino.Geometry import *
import scriptcontext
import rhinoscriptsyntax as rs
from graph.edge import Edge

from .point import Point
from .triangle import Triangle

# from point import Point
# from triangle import Triangle


def delaunay_triangulation(gl_nodes):
    gl_points_list = []  # Pointインスタンスを保持しておくリスト
    temp_points_list = []  # Pointインスタンスを一次的に保持するリスト
    divided_triangle_list = []  # 三角形分割された三角形を保持するリスト

    # ドロネー分割する点群を取得する
    # for gl_node in gl_nodes:
    #     point = Point(gl_node.coordinate_on_GL, gl_node)
    #
    #     temp_points_list.append(point)
    #     gl_points_list.append(point)

    for point in gl_nodes:
        point = Point(point)
        temp_points_list.append(point)
        gl_points_list.append(point)

    # はじめの外接円を構成する点のインスタンス作成。この範囲内に点群を収めておく必要あり
    P1 = Point([-100000, -100000, 0])
    P2 = Point([100000, -100000, 0])
    P3 = Point([0, 73000, 0])

    triangle = Triangle(P1, P2, P3)
    triangle.cul_center_coordinate_and_radius()

    divided_triangle_list.append(triangle)

    # ドロネー分割のメインアルゴリズム
    for index in range(len(temp_points_list)):

        # 追加するPointを選択
        select_point = temp_points_list.pop(0)

        # debug
        # rs.AddPoint(select_point.coordinate)

        temp_divided_triangle = []
        delete_triangle_list = []

        for triangle in divided_triangle_list:
            # 三角形の外接円内に新たに追加するPointが内包されているかどうかを判定
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

                # 分割に使用した三角形はのちに削除する
                delete_triangle_list.append(triangle)
            else:
                continue

        # 分割に使用した三角形は削除する
        for triangle in delete_triangle_list:
            divided_triangle_list.remove(triangle)

        # 重複している三角形を削除 -> 複数の外接円に選択した点が内包されている場合に重複する三角形が発生する
        for new_triangle in temp_divided_triangle:
            delete_flag = False

            for check_triangle in temp_divided_triangle:
                if new_triangle == check_triangle:
                    continue

                if new_triangle.center_p == check_triangle.center_p:
                    # Delete check triangle
                    temp_divided_triangle.remove(check_triangle)

                    delete_flag = True

            # Delete new triangle if delete flag is true
            if delete_flag:
                temp_divided_triangle.remove(new_triangle)

        # 新たに生成された三角形をリストに追加する
        divided_triangle_list.extend(temp_divided_triangle)

    # 最初の大きな三角形を構成する頂点を含む三角形は必要ないので、はじく
    desired_triangle_list = []
    for triangle in divided_triangle_list:
        if P1 in triangle.vertex or P2 in triangle.vertex or P3 in triangle.vertex:
            continue
        desired_triangle_list.append(triangle)

        # debug
        triangle.draw_divide_triangle()

    # 三角形を構成する頂点情報から隣接関係を取り出し、virtual nodeにその情報を渡す
    for gl_point in gl_points_list:
        for triangle in desired_triangle_list:

            if gl_point in triangle.vertex:
                temp_vertex = copy.copy(triangle.vertex)
                temp_vertex.remove(gl_point)

                for connected_pt in temp_vertex:
                    if connected_pt in gl_point.connected_points:
                        continue
                    else:
                        gl_point.connected_points.append(connected_pt)

    # return_edges = []
    # for point in gl_points_list:
    #
    #     current_virtual_node = point.virtual_node
    #
    #     for connected_pt in point.connected_points:
    #         connected_node = connected_pt.virtual_node
    #
    #         # Record the nodes to which each node is connected
    #         if not (connected_node in current_virtual_node.connected_nodes):
    #             current_virtual_node.connected_nodes.append(connected_node)  # about Node
    #
    #             if not (current_virtual_node in connected_node.connected_nodes):
    #                 connected_node.connected_nodes.append(current_virtual_node)  # about Node
    #
    #                 # Edge Instance
    #                 id = str(current_virtual_node.id) + "-" + str(connected_node.id)
    #                 edge_on_gl = Edge(id, current_virtual_node, connected_node, None)
    #
    #                 return_edges.append(edge_on_gl)
    #
    #                 # Virtual Nodeが保持するエッジ群に新たに生成したエッジ情報を格納する
    #                 current_virtual_node.set_having_edge([edge_on_gl])
    #                 connected_node.set_having_edge([edge_on_gl])
    #
    #                 # Virtual Nodeへのエッジ情報を格納する
    #                 current_virtual_node.set_having_edges_to_virtual_node([edge_on_gl])
    #                 connected_node.set_having_edges_to_virtual_node([edge_on_gl])
    #
    # return return_edges


def get_adjacent_relationships(test_node, gl_nodes, generated_triangles):
    gl_points_list = []
    triangle_list = []

    # 新たに追加する点(ノード)
    test_pt = Point(test_node.coordinate_on_GL, test_node)

    # 隣接関係を判定する点群(ノード群)を取得する
    for gl_node in gl_nodes:
        point = Point(gl_node.coordinate_on_GL, gl_node)
        gl_points_list.append(point)

    # 隣接関係を判定する
    if len(gl_points_list) == 3:
        # test pointと2つの生成済みpointから1つの三角形を生成する
        new_triangle = Triangle(gl_points_list[0], gl_points_list[1], gl_points_list[2])

        # 三角形情報を格納しておく
        triangle_list.append(new_triangle)

    elif len(gl_points_list) > 3:
        flag = True

        # 新たに追加する点が生成済みの三角形内に内包されているかどうかの判定
        for triangle in generated_triangles:
            judge = triangle.judge_test_point_in_triangle(test_pt)

            if judge:
                # 新たに追加するPointを頂点として使用し、元の三角形を分割。そして新たな三角形を生成する
                new_triangle1 = Triangle(triangle.p1, triangle.p2, test_pt)
                new_triangle2 = Triangle(triangle.p2, triangle.p3, test_pt)
                new_triangle3 = Triangle(triangle.p1, triangle.p3, test_pt)

                # 新たに生成された三角形をリストに追加する
                triangle_list += new_triangle1, new_triangle2, new_triangle3

                # 分割に使用した三角形はのちに削除する
                generated_triangles.remove(triangle)
                triangle.delete_triangle_guid()

                flag = False

                break

        # 新たに追加する点が生成済みの三角形内に内包されていない場合
        connected_pts = []

        if flag:
            for pt in gl_points_list:
                if pt == test_pt:
                    continue

                # Judge intersection of line and generated_triangles
                line = Line(test_pt.point, pt.point)

                if generated_triangles:
                    for triangle in generated_triangles:
                        intersections = Intersect.Intersection.CurveLine(triangle.polyline_curve, line, 0.001, 0.0)

                        if intersections:
                            # 交差点が2点以上ある場合は、接続点として認めない
                            if len(intersections) >= 2:
                                continue

                            # Test pointが接続しているノード点としてノード情報を格納しておく
                            connected_pts.append(pt)

            # 接続点の数から新たに三角形を生成する
            if len(connected_pts) == 2:
                # test pointと2つのconnected pointから1つの三角形を生成する
                new_triangle = Triangle(connected_pts[0], connected_pts[1], test_pt)

                # 三角形情報を格納しておく
                triangle_list.append(new_triangle)

            elif len(connected_pts) == 3:
                sort_connected_pts = []

                for pt in connected_pts:
                    distance = Point3d.DistanceTo(test_pt.point, pt.point)
                    sort_connected_pts.append([distance, pt])

                # Distanceが短い順にSortする
                sorted(sort_connected_pts, key=lambda x: x[0])

                # test pointと2つのconnected pointから1つの三角形を生成する
                new_triangle1 = Triangle(sort_connected_pts[0][1], connected_pts[1][1], test_pt)
                new_triangle2 = Triangle(sort_connected_pts[0][1], connected_pts[2][1], test_pt)

                # 三角形情報を格納しておく
                triangle_list += new_triangle1, new_triangle2

    # 三角形を構成する頂点情報から隣接関係を取り出し、virtual nodeにその情報を渡す
    for gl_point in gl_points_list:
        for triangle in triangle_list:
            if gl_point in triangle.vertex:
                temp_vertex = copy.copy(triangle.vertex)
                temp_vertex.remove(gl_point)

                for connected_pt in temp_vertex:
                    if connected_pt in gl_point.connected_points:
                        continue
                    else:
                        gl_point.connected_points.append(connected_pt)

    # 隣接関係を取得する
    return_edges = []
    for gl_point in gl_points_list:

        # 着目するVirtual Node
        current_virtual_node = gl_point.virtual_node

        for connected_pt in gl_point.connected_points:
            connected_node = connected_pt.virtual_node

            # Record the nodes to which each node is connected
            if not (connected_node in current_virtual_node.connected_nodes):
                current_virtual_node.connected_nodes.append(connected_node)  # about Node

                if not (current_virtual_node in connected_node.connected_nodes):
                    connected_node.connected_nodes.append(current_virtual_node)  # about Node

                    # Edge Instance
                    id = str(current_virtual_node.id) + "-" + str(connected_node.id)
                    edge_on_gl = Edge(id, current_virtual_node, connected_node, None)

                    # 戻り値として返す要素を保持しておく
                    return_edges.append(edge_on_gl)

                    # Virtual Nodeが保持するエッジ群に新たに生成したエッジ情報を格納する
                    current_virtual_node.set_having_edge([edge_on_gl])
                    connected_node.set_having_edge([edge_on_gl])

                    # Virtual Nodeへのエッジ情報を格納する
                    current_virtual_node.set_having_edges_to_virtual_node([edge_on_gl])
                    connected_node.set_having_edges_to_virtual_node([edge_on_gl])

    return return_edges, triangle_list

# if __name__ == "__main__":
#     points = rs.GetObjects("pick up some points", rs.filter.point)
#
#     select_pt = rs.GetObject("pick up test point", rs.filter.point)
#     generated_triangles = rs.GetObjects("Pick up generated triangle", rs.filter.curve)
#
#     # Convert
#     test_pt = rs.coerce3dpoint(select_pt)
#     test_pt = [test_pt[0], test_pt[1], test_pt[2]]
#
#     temp_point_list = []
#     for p in points:
#         p = rs.coerce3dpoint(p)
#         temp_point_list.append([p[0], p[1], p[2]])
#
#     # delaunay_triangulation(temp_point_list)
#
#     test_function(test_pt, temp_point_list, generated_triangles)
