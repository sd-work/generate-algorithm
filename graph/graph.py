# coding: utf-8

import copy
import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs

from .node import Node
from .edge import Edge
from .cycle import Cycle


class Graph:

    def __init__(self, id, nodes, edges):
        self.id = id
        self.nodes = nodes
        self.edges = edges
        self.contiguous_list = []

        self.cycles = []
        self.cycles_instance = []

        self.virtual_node_history = []  # 次の新しいvirtual cycleを検出するまでのvirtual nodeを保持しておく
        self.virtual_edge_history = []  # 次の新しいvirtual cycleを検出するまでのvirtual edgeを保持しておく

    def set_graph(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def create_graph(self):
        self.contiguous_list = []

        for node in self.nodes:
            node.sort_connected_nodes()
            self.contiguous_list.append(node.connected_nodes)

        # debug
        temp_contiguous_list = []
        for node in self.contiguous_list:
            temp = []
            for r_connected_node in node:
                temp.append(r_connected_node.id)
            temp_contiguous_list.append(temp)
        # print("contiguous_list: {0}".format(temp_contiguous_list))

    @staticmethod
    def create_node_from_joint_pts(num_nodes_in_structure, joint_pts_info):
        joint_pts_nodes = []

        for i, joint_pt_info in enumerate(joint_pts_info):
            joint_pt = joint_pt_info[1]
            joint_pt_node = Node(num_nodes_in_structure + 2 + i, joint_pt)
            joint_pts_nodes.append(joint_pt_node)

            # Draw node point in doc
            joint_pt_node.generate_node_point("node")

        return joint_pts_nodes

    @staticmethod
    def get_closest_edge_from_test_point(test_pt, edges):
        edge_to_get = None
        min_distance = 10000

        for edge in edges:
            rc, t = edge.edge_line.ClosestPoint(test_pt)

            if t:
                local_pt = edge.edge_line.PointAt(t)

                # Distance test point to local point which is on edge line
                distance = Point3d.DistanceTo(test_pt, local_pt)

                if distance < min_distance:
                    min_distance = distance
                    edge_to_get = edge
                else:
                    continue

        return edge_to_get

    @staticmethod
    def detect_edges_of_structure(num_joint_pts, node1, node2, edges_in_structure, joint_pts_nodes=None, timber=None):
        bolts = []  # ボルト群

        rs.EnableRedraw(False)

        # There are not joint points
        if num_joint_pts == 0:
            id = str(node1.id) + "-" + str(node2.id)
            edge = Edge(id, node1, node2, timber)

            # Draw edge line in doc
            edge.generate_edge_line("edge")

            """About connection of between new node"""
            node1.connected_nodes.append(node2)
            node2.connected_nodes.append(node1)

            """About split timber instance"""
            edge.timber = timber  # master timber
            edge.split_timber = timber  # child timber

            """About timber instance"""
            # Record the nodes and edges which adding timber has
            timber.set_nodes([node1, node2])  # both ends node
            timber.set_having_edge([edge])

            """About structure instance"""
            edges_in_structure.append(edge)

        # There are some joint points
        else:
            delete_old_edges = []
            temp_split_timbers = []  # adding timberを分割した時のsplit timber instanceを格納しておく
            end_point_nodes = [node1, node2]  # both ends point of adding timbers

            if num_joint_pts == 2:
                nodes_to_get = Graph.get_closest_node_from_test_point(joint_pts_nodes, end_point_nodes)
            else:
                nodes_to_get = []

            # 接合部の数だけ処理を行う
            for i in range(num_joint_pts):
                ends_of_bolt = []  # ボルトの両端部の座標値
                joint_pt_node = joint_pts_nodes[i]  # joint point node
                test_pt = joint_pt_node.point  # Point3d
                edge_to_get = Graph.get_closest_edge_from_test_point(test_pt, edges_in_structure)
                # print("edge to get: {0}".format(edge_to_get.id))

                """ Get edge(adding timber node and joint point node) """
                # 接合数が1つの場合
                if num_joint_pts == 1:
                    """About split timber instance and generate edge instance"""
                    # Split the timber at the joint point
                    split_timbers, end_of_bolt = timber.split_timber_surface(test_pt, timber)

                    # ボルトの2つの端点のうちの1つ(1つ目)を格納する
                    ends_of_bolt.append(end_of_bolt)

                    # joint pt nodeにボルトの端点情報(1つ目)を保持させる
                    joint_pt_node.ends_pt_of_bolt_1 = end_of_bolt
                    joint_pt_node.ends_pt_of_bolt.append(ends_of_bolt)

                    # 接合点は部材と部材が接している部分ではなく、接合点から一番近い中心線上のある点
                    joint_pt_node.structural_type = 2  # 接合点
                    joint_pt_node.contact_pt = joint_pt_node.point  # 部材1と部材2の接地点
                    joint_pt_node.point = end_of_bolt  # 接合点 -> この接合点はTimberの中心線上に存在

                    id = str(node1.id) + "-" + str(joint_pt_node.id)
                    edge1 = Edge(id, node1, joint_pt_node, timber)

                    id = str(node2.id) + "-" + str(joint_pt_node.id)
                    edge2 = Edge(id, node2, joint_pt_node, timber)

                    # Draw edge line guid in doc
                    edge1.generate_edge_line("edge")
                    edge2.generate_edge_line("edge")

                    # Record the split timber in edge and Record the edges which split timber has
                    Edge.record_split_timber_to_edge(edge1, edge2, split_timbers)

                    """About connection of both ends node and joint point"""
                    # Record the nodes to which each node is connected
                    node1.set_connected_nodes(joint_pt_node)
                    node2.set_connected_nodes(joint_pt_node)

                    """About joint point node"""
                    # Record the nodes to which joint point is connected and Record the edges which Node has
                    joint_pt_node.set_connected_nodes([node1, node2, edge_to_get.start_node, edge_to_get.end_node])
                    joint_pt_node.set_having_edge([edge1, edge2])

                    # Todo record adding timber information
                    joint_pt_node.set_timbers_on_contact_pt([timber])

                    """About timber instance"""
                    # Record the nodes and edges which adding timber has
                    timber.set_nodes([node1, node2, joint_pt_node])
                    timber.set_joint_pt_nodes([joint_pt_node])
                    timber.set_having_edge([edge1, edge2])

                    """About structure instance"""
                    # Maintain node information
                    edges_in_structure += edge1, edge2

                # 接合数が2つの場合
                elif num_joint_pts == 2:
                    node_to_get = nodes_to_get[joint_pt_node]

                    if i == 0:
                        joint_pt_node2 = joint_pts_nodes[1]
                    else:
                        joint_pt_node2 = joint_pts_nodes[0]

                    """About split timber instance and generate edge instance"""
                    if i == 0:
                        # Split timber
                        split_timbers, end_of_bolt = timber.split_timber_surface(test_pt, timber)

                        # 分割したsplit timber instanceを格納しておく
                        temp_split_timbers += split_timbers

                        # ボルトの2つの端点のうちの1つ(1つ目)を格納する
                        ends_of_bolt.append(end_of_bolt)
                        joint_pt_node.ends_pt_of_bolt_1 = end_of_bolt
                    else:
                        rc, u1, v1 = Surface.ClosestPoint(temp_split_timbers[0].surface, test_pt)
                        rc, u2, v2 = Surface.ClosestPoint(temp_split_timbers[1].surface, test_pt)

                        to_point1 = temp_split_timbers[0].surface.PointAt(u1, v1)
                        to_point2 = temp_split_timbers[1].surface.PointAt(u2, v2)

                        dis1 = Point3d.DistanceTo(test_pt, Point3d(to_point1[0], to_point1[1], to_point1[2]))
                        dis2 = Point3d.DistanceTo(test_pt, Point3d(to_point2[0], to_point2[1], to_point2[2]))

                        if dis1 < dis2:
                            temp_parent_timber = temp_split_timbers[0]
                        else:
                            temp_parent_timber = temp_split_timbers[1]

                        # Split timber
                        split_timbers, end_of_bolt = timber.split_timber_surface(test_pt, temp_parent_timber)

                        # ボルトの2つの端点のうちの1つ(1つ目)を格納する
                        ends_of_bolt.append(end_of_bolt)
                        joint_pt_node.ends_pt_of_bolt_1 = end_of_bolt

                        # 分割したsplit timber instanceを格納しておく
                        temp_split_timbers += split_timbers

                        # Delete parent timber guid form doc
                        temp_parent_timber.delete_timber_guid()

                        # Remove temp parent timber from instance variable which adding timber has
                        temp_split_timbers.remove(temp_parent_timber)

                        # 分割したsplit timber instanceを格納しておく
                        temp_split_timbers += split_timbers

                    # joint pt nodeにボルトの端点情報(1つ目)を保持させる
                    joint_pt_node.ends_pt_of_bolt.append(ends_of_bolt)

                    # 接合点は部材と部材が接している部分ではなく、接合点から一番近い中心線上のある点
                    joint_pt_node.structural_type = 2  # 接合点
                    joint_pt_node.contact_pt = joint_pt_node.point  # 部材1と部材2の接地点

                    if i == 0:  # Todo ここの設定が重要になる
                        joint_pt_node.point = ends_of_bolt[0]  # ボルトの両端部の1端がindex0でもう一方がindex1
                    else:
                        joint_pt_node.point = ends_of_bolt[0]  # ボルトの両端部の1端がindex0でもう一方がindex1
                        joint_pt_node2.point = bolts[0][0]  # これは1つ前のボルトの1端(adding timber側)

                    id = str(node_to_get.id) + "-" + str(joint_pt_node.id)
                    edge1 = Edge(id, node_to_get, joint_pt_node, timber)

                    id = str(joint_pt_node.id) + "-" + str(joint_pt_node2.id)
                    edge2 = Edge(id, joint_pt_node, joint_pt_node2, timber)

                    # Draw edge line in doc
                    if i == 0:
                        # Draw edge line guid in doc
                        edge1.generate_edge_line("edge")
                    else:
                        # Draw edge line guid in doc
                        edge1.generate_edge_line("edge")
                        edge2.generate_edge_line("edge")

                    # Record the split timber in edge and Record the edges which split timber has
                    Edge.record_split_timber_to_edge(edge1, edge2, split_timbers)

                    """About connection of between a end point and joint point"""
                    node_to_get.set_connected_nodes(joint_pt_node)

                    """About joint point node"""
                    joint_pt_node.set_connected_nodes(
                        [node_to_get, joint_pt_node2, edge_to_get.start_node, edge_to_get.end_node])

                    # Todo record adding timber information
                    joint_pt_node.set_timbers_on_contact_pt([timber])

                    """About timber instance | joint point node | structure instance"""
                    if i == 0:
                        # About timber instance
                        timber.set_nodes([node1, node2, joint_pt_node])
                        timber.set_joint_pt_nodes([joint_pt_node])
                        timber.set_having_edge([edge1])

                        # About joint point node
                        joint_pt_node.set_having_edge([edge1])

                        # About structure instance
                        edges_in_structure.append(edge1)
                    else:
                        # About timber instance
                        timber.set_nodes([joint_pt_node])
                        timber.joint_pts_nodes.append(joint_pt_node)
                        timber.set_having_edge([edge1, edge2])

                        # About joint point node
                        joint_pts_nodes[0].set_having_edge([edge2])
                        joint_pt_node.set_having_edge([edge1, edge2])

                        # About structure instance
                        edges_in_structure += edge1, edge2

                """ Get edge(Already generated timber node and joint point node) """
                already_generated_timber = edge_to_get.timber

                """About split timber instance"""
                temp_parent_timber = edge_to_get.split_timber
                split_timbers, end_of_bolt = already_generated_timber.split_timber_surface(test_pt, temp_parent_timber)

                # ボルトの2つの端点のうちの1つ(2つ目)を格納する
                ends_of_bolt.append(end_of_bolt)

                # joint pt nodeにボルトの端点情報(2つ目)を保持させる
                joint_pt_node.ends_pt_of_bolt_2 = end_of_bolt

                # 接合点は部材と部材が接している部分ではなく、接合点から一番近い中心線上のある点
                # Todo joint point nodeにbolt end point変数をつくり、そこに値を格納する
                # Todo コピーしてしまうと同一のjoint pointとしてみなせなくなるため？
                joint_pt_node = copy.copy(joint_pt_node)  # ここでjoint point nodeを複製する
                joint_pt_node.structural_type = 2  # 接合点
                joint_pt_node.contact_pt = joint_pt_node.point  # 部材1と部材2の接地点
                joint_pt_node.point = end_of_bolt  # 接合点 -> この接合点はTimberの中心線上に存在

                id = str(edge_to_get.start_node.id) + "-" + str(joint_pt_node.id)
                edge1 = Edge(id, edge_to_get.start_node, joint_pt_node, already_generated_timber)

                id = str(edge_to_get.end_node.id) + "-" + str(joint_pt_node.id)
                edge2 = Edge(id, edge_to_get.end_node, joint_pt_node, already_generated_timber)

                # Draw edge line in doc
                edge1.generate_edge_line("edge")
                edge2.generate_edge_line("edge")

                # Record the split timber in edge and Record the edges which split timber has
                Edge.record_split_timber_to_edge(edge1, edge2, split_timbers)

                """About connection of both ends point and joint point"""
                # Start node that an edge has
                temp_connected_nodes = []

                if len(edge_to_get.start_node.connected_nodes) == 4:
                    for r_connected_node in edge_to_get.start_node.connected_nodes:
                        if r_connected_node == edge_to_get.end_node:  # edge_to_get.end_node.id
                            continue
                        else:
                            temp_connected_nodes.append(r_connected_node)

                    temp_connected_nodes.append(joint_pt_node)

                    # Set connected nodes information to an edge
                    edge_to_get.start_node.set_connected_nodes(temp_connected_nodes)

                    # Set new having edge information to node instance
                    edge_to_get.start_node.having_edges.remove(edge_to_get)  # delete old edge from having edge list
                    edge_to_get.start_node.set_having_edge([edge1])  # set new having edge to node instance

                else:
                    # Set connected nodes information to an edge
                    edge_to_get.start_node.set_connected_nodes(joint_pt_node)

                # End node that an edge has
                temp_connected_nodes = []

                if len(edge_to_get.end_node.connected_nodes) == 4:
                    for r_connected_node in edge_to_get.end_node.connected_nodes:
                        if r_connected_node == edge_to_get.start_node:  # edge_to_get.start_node.id
                            continue
                        else:
                            temp_connected_nodes.append(r_connected_node)

                    temp_connected_nodes.append(joint_pt_node)

                    # Set connected nodes information to an edge
                    edge_to_get.end_node.set_connected_nodes(temp_connected_nodes)

                    # Set new having edge information to node instance
                    edge_to_get.end_node.having_edges.remove(edge_to_get)  # delete old edge from having edge list
                    edge_to_get.end_node.set_having_edge([edge2])  # set new having edge to node instance
                else:
                    # Set connected nodes information to an edge
                    edge_to_get.end_node.set_connected_nodes(joint_pt_node)

                """About joint point node"""
                joint_pt_node.set_having_edge([edge1, edge2])

                # Todo record adding timber information
                joint_pt_node.set_timbers_on_contact_pt([already_generated_timber])

                """About timber instance"""
                already_generated_timber.set_nodes([joint_pt_node])
                already_generated_timber.set_joint_pt_nodes([joint_pt_node])

                # About edge
                edge1.is_on_virtual_cycle = edge_to_get.is_on_virtual_cycle
                edge2.is_on_virtual_cycle = edge_to_get.is_on_virtual_cycle
                already_generated_timber.edges.remove(edge_to_get)  # remove 'edge to get' id from edges list
                already_generated_timber.set_having_edge([edge1, edge2])

                """About structure instance"""
                edges_in_structure += edge1, edge2

                """Delete old edge"""
                if num_joint_pts == 1:
                    edge_to_get.delete_guid()
                    edges_in_structure.remove(edge_to_get)

                    del edge_to_get

                elif num_joint_pts == 2:
                    if i == 0:
                        delete_old_edges.append(edge_to_get)
                    else:
                        delete_old_edges.append(edge_to_get)

                        for old_edge in delete_old_edges:
                            old_edge.delete_guid()
                            edges_in_structure.remove(old_edge)

                            del old_edge

                """Maintain ends point of bolt information"""
                bolts.append(ends_of_bolt)

        rs.EnableRedraw(True)

        return bolts

    def detect_edge_of_virtual_graph(self, virtual_node, edges_in_structure, edges_in_virtual):
        adding_virtual_nodes = []
        missing_edges = []
        new_virtual_connected_nodes = []

        for real_node in virtual_node.nodes_of_real_graph:
            for r_connected_node in real_node.connected_nodes:

                # If the selected node is the node that is shaping the cycle->接続先のノードがサイクルを構成するノードの時
                if r_connected_node in virtual_node.nodes_of_real_graph:

                    # Get Missing edge
                    edge_id = [real_node.id, r_connected_node.id]
                    edge_id.sort()

                    if edge_id in missing_edges:
                        continue
                    else:
                        missing_edges.append(edge_id)

                else:
                    new_connected_node = None

                    # if connected node is a part of real graph node of generated virtual node
                    is_new_connected_node_virtual_node = False

                    for v_node in self.nodes:
                        if not v_node.nodes_of_real_graph:  # virtual nodeが葉(子ノードを持たないノード)である場合
                            continue
                        else:
                            # virtual nodeを構成するreal nodeが他のvirtual nodeを構成するreal nodeに接続している場合
                            if r_connected_node in v_node.nodes_of_real_graph:
                                new_connected_node = v_node  # 接続先は既に生成されているvirtual node
                                is_new_connected_node_virtual_node = True

                                new_virtual_connected_nodes.append(new_connected_node)  # TODO 削除に使う
                                break

                    # 接続先が葉ノードの場合
                    if not is_new_connected_node_virtual_node:
                        new_connected_node = Node(r_connected_node.id, r_connected_node.point)  # 新たなinstanceとして生成

                        new_virtual_connected_nodes.append(new_connected_node)  # TODO 削除に使う

                        # Draw virtual node in doc
                        new_connected_node.generate_node_point("v-node")

                    # Get timber id which a real edge has
                    if real_node.id < r_connected_node.id:
                        check_edge_id = str(real_node.id) + "-" + str(r_connected_node.id)
                    else:
                        check_edge_id = str(r_connected_node.id) + "-" + str(real_node.id)

                    timber = None
                    real_edge = None
                    for edge in edges_in_structure:
                        if check_edge_id == edge.id:
                            real_edge = edge
                            timber = real_edge.timber
                            break

                    # is_generated = Edge.check_edge_in_edge_list(virtual_node, new_connected_node, edges_in_virtual)
                    #
                    # if is_generated:
                    #     print("debug")
                    #     continue

                    # The Edge consists of virtual node and new connected node
                    id = str(virtual_node.id) + "-" + str(new_connected_node.id)
                    v_edge = Edge(id, virtual_node, new_connected_node, timber)  # 新たにinstance作ってるから

                    # connecting real edge information to virtual edge
                    v_edge.real_edge = real_edge
                    virtual_node.having_edges.append(v_edge)

                    # 着目しているエッジがVirtual cycleを構成するエッジの一部である場合->葉ノードへの接続でない場合
                    if is_new_connected_node_virtual_node:
                        virtual_node.set_having_edges_to_virtual_node([v_edge])
                        new_connected_node.set_having_edges_to_virtual_node([v_edge])
                    else:
                        virtual_node.set_having_edges_to_leaf_node([v_edge])  # virtual node -> 葉ノード
                        new_connected_node.set_having_edges_to_virtual_node([v_edge])  # 葉ノード -> virtual node

                    # Record the nodes to which each node is connected
                    if not (new_connected_node in virtual_node.connected_nodes):
                        virtual_node.connected_nodes.append(new_connected_node)
                    if not (virtual_node in new_connected_node.connected_nodes):
                        new_connected_node.connected_nodes.append(virtual_node)

                    # 新たに生成されたvirtual node
                    adding_virtual_nodes.append(new_connected_node)

                    # Draw virtual edge line in doc
                    v_edge.generate_edge_line("v-edge")

                    # Maintain edge information
                    edges_in_virtual.append(v_edge)

        # print("length new_virtual_connected_nodes: {0}".format(len(new_virtual_connected_nodes)))

        # Delete old edges
        for new_virtual_connected_node in new_virtual_connected_nodes:
            for having_edge in new_virtual_connected_node.having_edges:
                for r_node in virtual_node.nodes_of_real_graph:
                    for connected_node in r_node.connected_nodes:
                        if str(connected_node.id) in str(having_edge.id):
                            # delete old edge and connected node information
                            for i, v_connected_node in enumerate(new_virtual_connected_node.connected_nodes):
                                if v_connected_node.id == connected_node.id:
                                    # delete node
                                    new_virtual_connected_node.connected_nodes.pop(i)

                                    # delete edge from doc
                                    having_edge.delete_guid()

                                    # delete a edge from edge list which a node have
                                    new_virtual_connected_node.having_edges.remove(having_edge)

                                    if having_edge in new_virtual_connected_node.having_edges_to_virtual_node:
                                        new_virtual_connected_node.having_edges_to_virtual_node.remove(having_edge)

                                    if having_edge in new_virtual_connected_node.having_edges_to_leaf_node:
                                        new_virtual_connected_node.having_edges_to_leaf_node.remove(having_edge)

                                    # delete edge instance from edges_in_virtual
                                    edges_in_virtual.remove(having_edge)

                                    break
                            else:
                                continue
                            break
                    else:
                        continue
                    break
                else:
                    continue
                break

        for new_virtual_connected_node in new_virtual_connected_nodes:
            # print("Check node: {0}".format(new_virtual_connected_node.id))
            for having_edge in new_virtual_connected_node.having_edges:
                for check_node in new_virtual_connected_nodes:
                    if new_virtual_connected_node == check_node:
                        continue

                    # あるvirtual nodeが保持するエッジが、new virtual connected nodeのいずれかのノードに接続している場合
                    if str(check_node.id) in str(having_edge.id):
                        # delete old edge and connected node information
                        for i, v_connected_node in enumerate(new_virtual_connected_node.connected_nodes):
                            if v_connected_node.id == check_node.id:
                                # delete node
                                new_virtual_connected_node.connected_nodes.pop(i)
                                check_node.connected_nodes.remove(new_virtual_connected_node)

                                # delete edge from doc
                                having_edge.delete_guid()

                                # delete a edge from edge list which a node have
                                new_virtual_connected_node.having_edges.remove(having_edge)
                                if having_edge in check_node.having_edges:
                                    check_node.having_edges.remove(having_edge)

                                if having_edge in new_virtual_connected_node.having_edges_to_virtual_node:
                                    new_virtual_connected_node.having_edges_to_virtual_node.remove(having_edge)
                                    check_node.having_edges_to_virtual_node.remove(having_edge)

                                if having_edge in new_virtual_connected_node.having_edges_to_leaf_node:
                                    new_virtual_connected_node.having_edges_to_leaf_node.remove(having_edge)
                                    check_node.having_edges_to_leaf_node.remove(having_edge)  # TODO

                                # delete edge instance from edges_in_virtual
                                edges_in_virtual.remove(having_edge)
                                break
                        else:
                            continue
                        break
                else:
                    continue
                break

        # Calculate missing edges
        for missing_edge in missing_edges:
            missing_edge_id = str(missing_edge[0]) + "-" + str(missing_edge[1])

            for edge in edges_in_structure:
                if missing_edge_id == edge.id:
                    virtual_node.missing_edges.append(edge)

                    # # エッジはVirtual cycleを構成するエッジの一部である場合
                    # edge.is_on_virtual_cycle = True

                    if edge.timber:
                        # missing edgeが保持するTimberに剛接合点(virtual_node)情報をリンクさせる
                        edge.timber.rigid_joints.append(virtual_node)

                    break

        return adding_virtual_nodes

    @staticmethod
    def get_closest_node_from_test_point(joint_pts_nodes, reference_pts):
        reference_pt_joint_pt = {}

        for reference_pt in reference_pts:
            min_distance = 10000
            selected_joint_pt = None

            for joint_pt in joint_pts_nodes:
                distance = Point3d.DistanceTo(reference_pt.point, joint_pt.point)

                if distance < min_distance:
                    min_distance = distance
                    selected_joint_pt = joint_pt

            reference_pt_joint_pt[selected_joint_pt] = reference_pt

        return reference_pt_joint_pt

    def generate_cycle(self, cycles, nodes_in_playground, layer_name):

        return_cycles = []
        delete_cycles = []

        for index, cycle in enumerate(cycles):
            # 既に同じサイクルを検出し、情報を保持している場合 -> TODO リストの順番が同じ＋要素数も同じである場合は判定される
            if cycle in self.cycles:
                continue

            # Maintain cycle information
            self.cycles.append(cycle)

            num_node_on_gl = 0
            cycle_nodes_instance = []

            # サイクルを構成するノードinstanceを取得する
            for node_id in cycle:
                if layer_name == "r-cycle":
                    node_instance = nodes_in_playground[node_id]
                    cycle_nodes_instance.append(node_instance)

                    # judge node on the GL
                    if -60 < node_instance.z < 60:
                        num_node_on_gl += 1

                elif layer_name == "v-cycle":
                    for node_in_playground in nodes_in_playground:
                        if node_in_playground.id == node_id:
                            node_instance = node_in_playground
                            cycle_nodes_instance.append(node_instance)

                            # judge node on the GL
                            if -60 < node_instance.z < 60:
                                num_node_on_gl += 1

            # サイクルがGLに接地しているかどうかを判定する
            if num_node_on_gl == 2:
                is_on_gl = True
            else:
                is_on_gl = False

            # cycle instanceを生成する
            if layer_name == "r-cycle":
                cycle = Cycle(str(len(self.cycles)), cycle, cycle_nodes_instance, is_on_gl)  # instance

            elif layer_name == "v-cycle":
                # 新たに生成するサイクルと既に生成されているサイクルの内包関係を調べ、必要がある場合は更新を行う
                delete_cycles = Cycle.determine_subset_of_two_cycles(cycle_nodes_instance, self.cycles_instance)

                if delete_cycles:
                    for delete_cycle in delete_cycles:
                        if delete_cycle.cycle in self.cycles:
                            print("---Delete cycle---")
                            print(delete_cycle.cycle)

                            self.cycles.remove(delete_cycle.cycle)  # Delete cycle from list
                            self.cycles_instance.remove(delete_cycle)  # Delete cycle instance from list
                            delete_cycles.append(delete_cycle)

                # cycle instance
                cycle = Cycle("v-" + str(len(self.cycles)), cycle, cycle_nodes_instance, is_on_gl)

                # TODO is_on_virtual_cycleを判定する
                for virtual_node in cycle.composition_nodes:
                    # virtual node to virtual nodeはTrue
                    for having_edge_to_virtual_node in virtual_node.having_edges_to_virtual_node:
                        if having_edge_to_virtual_node.real_edge:
                            having_edge_to_virtual_node.real_edge.is_on_virtual_cycle = True

                    # missing edgeはTrue
                    for missing_edge in virtual_node.missing_edges:
                        missing_edge.is_on_virtual_cycle = True

            # Generate cycle mesh in doc
            if layer_name == "r-cycle":
                cycle.generate_cycle_mesh(layer_name)

            elif layer_name == "v-cycle":
                cycle.generate_cycle_polyline(layer_name)

            # cycle instanceを保持する
            self.cycles_instance.append(cycle)
            return_cycles.append(cycle)

        if layer_name == "r-cycle":
            return return_cycles
        elif layer_name == "v-cycle":
            return return_cycles, delete_cycles

    # 部材の色分けを行う(全体の判定)
    def color_code_timbers(self, timber_list_in_playground):

        check_timber_list_in_playground = copy.copy(timber_list_in_playground)

        # 1. 全体の判定
        # virtual graph内でサイクルを構成しているノードが保持しているTimberは青色に設定
        for virtual_cycle in self.cycles_instance:
            for virtual_node in virtual_cycle.composition_nodes:
                for missing_edge in virtual_node.missing_edges:  # TODO ここで何回も同じ処理している
                    if missing_edge.timber is None:  # Edge is on GL
                        continue
                    else:
                        # 1. Edgeが保持しているMaster Timberの色を変更する
                        rs.ObjectColor(missing_edge.timber.surface_guid, [157, 204, 255])  # 青色
                        missing_edge.timber.status = 2  # 青色

                        # 2. Master Timberが保持しているsplit timberの色を変更する
                        for split_timber in missing_edge.timber.split_timbers:
                            rs.ObjectColor(split_timber.surface_guid, [225, 225, 0])  # 黄色
                            split_timber.status = 1  # 黄色

                        # 2-1. 三角形を構成しているエッジを構成しているsplit timberは青色
                        rs.ObjectColor(missing_edge.split_timber.surface_guid, [157, 204, 255])  # 青色
                        missing_edge.split_timber.status = 2  # 青色

                        # 2-2. 三角形間に結ばれるエッジを構成しているsplit timberは青色
                        for v_edge in virtual_node.having_edges_to_virtual_node:
                            if v_edge.real_edge:
                                if v_edge.real_edge.split_timber.surface_guid:
                                    rs.ObjectColor(v_edge.real_edge.split_timber.surface_guid, [157, 204, 255])  # 青色
                                    v_edge.real_edge.split_timber.status = 2  # 青色

                        # # 2-3. 端部は黄色に変更
                        # for v_edge in virtual_node.having_edges_to_leaf_node:
                        #     if v_edge.real_edge.split_timber.surface_guid:
                        #         rs.ObjectColor(v_edge.real_edge.split_timber.surface_guid, [225, 225, 0])  # 黄色
                        #         v_edge.real_edge.split_timber.status = 1  # 黄色

                        # 色分けを行った部材はリストから消去する
                        if missing_edge.timber in check_timber_list_in_playground:
                            check_timber_list_in_playground.remove(missing_edge.timber)

        # 2. 部分の判定
        # 全体の判定では処理されなかった部材の色分けを行う
        # print("Num of timber: {0}".format(len(check_timber_list_in_playground)))

        for timber in check_timber_list_in_playground:
            timber.color_code_timber()

