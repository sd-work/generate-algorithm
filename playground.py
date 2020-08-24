# coding: utf-8

import scriptcontext
import rhinoscript.utility
import Rhino
from Rhino.Geometry import *
from Rhino.DocObjects import *
import rhinoscriptsyntax as rs
import math
import random
import sys
import codecs
from timber import *
from target_line import *
from optiimization import *

from graph.graph import Graph
from graph.node import Node
from graph.edge import Edge
from graph.search import Search

num_joint_pts = 0
joint_pts_info = []


class Playground:

    def __init__(self):
        self.timber_list_in_database = []  # データベース上にある部材
        self.timber_list_in_playground = []  # 遊び場を構成している部材
        self.target_line_in_playground = []  # 遊び場を構成しているターゲット曲線
        self.nodes_in_playground = []  # 現状の構築物に存在するノード群
        self.edges_in_playground = []  # 現状の構築物に存在するエッジ群

        self.adding_timber = None
        self.adding_timbers = []
        self.adding_target_line = None

        self.graph = Graph([], [])

    # 部材データを生成する TODO ここはスキャンした3Dデータに切り替える
    def generate_timber_info(self, num_timber):
        for id in range(num_timber):
            timber = Timber(id)
            timber.generate_timber_info(random.randint(1200, 2000))
            self.timber_list_in_database.append(timber)

            # 木材の情報をcsvファイルとして書き出す
            timber.export_csv_file("timber_" + str(id + 1))

    def export_csv_file(self):
        path = r"G:\マイドライブ\2020\04_Master\2006_Generation-algorithm\RhinoPython\csv\timber_info.csv"

        with open(path, "w") as csv_file:
            writer = csv.writer(csv_file)

            for timber in self.timber_list_in_database:
                # TODO サーバーとやりとりをするので、データベース上に使用した材かどうかの記述をするように変更する
                writing_info = [timber.id, timber.length, timber.path_to_csv.encode("utf-8")]
                writer.writerow(writing_info)

        self.timber_list_in_database = []  # reset

    def open_csv_file(self):
        path = r"G:\マイドライブ\2020\04_Master\2006_Generation-algorithm\RhinoPython\csv\timber_info.csv"

        with codecs.open(path, "r", "utf-8") as csv_file:
            reader = csv.reader(csv_file)
            for info in reader:
                if not info:
                    continue
                self.timber_list_in_database.append(Timber(info[0], info[1], info[2], "playground"))

    @staticmethod
    def create_playground_layer():
        # playground layer
        rs.AddLayer("playground", [0, 0, 0], True, False, None)

        # graph layer
        rs.AddLayer("graph", [0, 0, 0], False, False, None)
        rs.AddLayer("node", [0, 0, 0], True, False, "graph")
        rs.AddLayer("edge", [0, 0, 0], True, False, "graph")
        rs.AddLayer("cycle", [0, 0, 0], True, False, "graph")

    def select_adding_timber(self, target_line, num_of_joint_pt):

        # 取得したターゲット曲線情報から、木材を追加するための新たなターゲット曲線情報を取得
        target_length, self.adding_target_line = Optimization.edit_adding_timber_range(target_line, num_of_joint_pt)

        # 木材の参照長さに最も近似した長さの木材を検索し、取得する
        select_timber = Optimization.get_best_timber_in_database(self.timber_list_in_database, target_length)

        self.adding_timber = select_timber
        self.adding_timber.target_line = self.adding_target_line  # ターゲット曲線を設定
        self.adding_timber.generate_timber()  # 木材を生成
        self.adding_timbers.append(self.adding_timber)

        #  ターゲット曲線から木材の生成パターンを判定する
        self.adding_timber.judge_timber_pattern(target_line, self.timber_list_in_playground)

        # 遊び場を構成しているターゲット曲線群に追加
        self.target_line_in_playground.append(self.adding_target_line)

    def transform_timber(self):
        # translate
        origin_p = self.adding_timber.center_line.First  # timberの端点
        transform_p = self.adding_target_line.start_p  # ターゲット曲線の端点
        self.adding_timber.translate_timber(origin_p, transform_p)

        # rotation
        vector_timber = Rhino.Geometry.Vector3d(
            self.adding_timber.center_line.Last - self.adding_timber.center_line.First)
        angle = Vector3d.VectorAngle(vector_timber, self.adding_target_line.vector)
        axis = Vector3d.CrossProduct(vector_timber, self.adding_target_line.vector)
        rotation_center = self.adding_timber.center_line.First
        self.adding_timber.rotate_timber(angle, axis, rotation_center)

    def minimized_joint_area(self):
        global num_joint_pts, joint_pts_info

        # ターゲット曲線の情報から接合点、ベクトルを計算し、取得する
        joint_pts_info = Optimization.get_joint_pts_info(self.adding_timbers, self.timber_list_in_playground)

        # number of joint points is 1
        if len(joint_pts_info) == 1:
            num_joint_pts = 1

            joint_pt = joint_pts_info[0][1]
            unit_move_vec = joint_pts_info[0][2]
            self_timber = joint_pts_info[0][3]
            other_timber = joint_pts_info[0][4]

            # optimization
            flag = self_timber.minimized_joint_area(other_timber, joint_pt, unit_move_vec)
            if flag is False:
                return flag
            else:
                joint_pts_info[0][1] = flag[1]
                return True

        # number of joint points is 2
        elif len(joint_pts_info) == 2:
            num_joint_pts = 2
            self_timber = joint_pts_info[0][3]

            # optimization
            flag = self_timber.bridge_joint_area(joint_pts_info)
            if flag is False:
                return flag
            else:
                joint_pts_info[0][1] = flag[0]
                joint_pts_info[1][1] = flag[1]
                return True

        else:
            num_joint_pts = 0
            # print("There are not joint points.")
            return True

    def determine_status_of_structure(self):
        num_nodes_in_playground = len(self.graph.nodes)

        for adding_timber in self.adding_timbers:
            ### Get node ###
            node1 = Node(num_nodes_in_playground, adding_timber.center_line.First)
            node2 = Node(num_nodes_in_playground + 1, adding_timber.center_line.Last)

            # Maintain node information
            self.nodes_in_playground += node1, node2

            # Draw node in doc
            node1.generate_node_point()
            node2.generate_node_point()

            ### Get edge ###
            if num_joint_pts == 0:
                id = str(node1.id) + "-" + str(node2.id)
                edge = Edge(id, node1, node2)

                # Maintain node information
                self.edges_in_playground.append(edge)

                # Record the nodes to which each node is connected
                node1.connected_nodes.append(node2.id)
                node2.connected_nodes.append(node1.id)

                # Draw edge line in doc
                edge.generate_edge_line()

            # TODO GLでノードを作るときの判定を追加する
            elif num_joint_pts == 1 or num_joint_pts == 2:

                # Get joint point nodes
                joint_pts_nodes = []

                for i, joint_pt_info in enumerate(joint_pts_info):
                    joint_pt = joint_pt_info[1]
                    joint_pt_node = Node(num_nodes_in_playground + 2 + i, joint_pt)
                    joint_pts_nodes.append(joint_pt_node)

                    # Maintain node information
                    self.nodes_in_playground.append(joint_pt_node)

                    # Draw node in doc
                    joint_pt_node.generate_node_point()

                # Get edge(adding timber node and joint point node)
                delete_old_edges = []

                for i in range(num_joint_pts):
                    joint_pt_node = joint_pts_nodes[i]
                    edge_to_get = self.graph.get_edge_from_test_point(joint_pt_node.point)
                    print("edge to get: {0}".format(edge_to_get.id))

                    if num_joint_pts == 1:
                        id = str(node1.id) + "-" + str(joint_pt_node.id)
                        edge1 = Edge(id, node1, joint_pt_node)

                        id = str(node2.id) + "-" + str(joint_pt_node.id)
                        edge2 = Edge(id, node2, joint_pt_node)

                        # Maintain node information
                        self.edges_in_playground += edge1, edge2

                        # Record the nodes to which each node is connected
                        node1.set_connected_nodes(joint_pt_node.id)
                        node2.set_connected_nodes(joint_pt_node.id)

                        # Draw edge line in doc
                        edge1.generate_edge_line()
                        edge2.generate_edge_line()

                        # Record the nodes to which joint point is connected
                        joint_pt_node.set_connected_nodes(
                            [node1.id, node2.id, edge_to_get.start_node.id, edge_to_get.end_node.id])

                    elif num_joint_pts == 2:

                        node_to_get = Graph.get_closest_node_from_test_point(joint_pt_node.point, [node1, node2])

                        id = str(node_to_get.id) + "-" + str(joint_pt_node.id)
                        edge1 = Edge(id, node_to_get, joint_pt_node)

                        if i == 0:
                            joint_pt_node2 = joint_pts_nodes[1]
                        else:
                            joint_pt_node2 = joint_pts_nodes[0]

                        id = str(joint_pt_node.id) + "-" + str(joint_pt_node2.id)
                        edge2 = Edge(id, joint_pt_node, joint_pt_node2)

                        # Maintain node information
                        if i == 0:
                            self.edges_in_playground.append(edge1)
                        else:
                            self.edges_in_playground += edge1, edge2

                        # Record the nodes to which each node is connected
                        node_to_get.set_connected_nodes(joint_pt_node.id)
                        joint_pt_node.set_connected_nodes(joint_pt_node2.id)

                        # Draw edge line in doc
                        if i == 0:
                            edge1.generate_edge_line()
                        else:
                            edge1.generate_edge_line()
                            edge2.generate_edge_line()

                        # Record the nodes to which joint point is connected
                        joint_pt_node.set_connected_nodes(
                            [node_to_get.id, joint_pt_node2.id, edge_to_get.start_node.id, edge_to_get.end_node.id])

                    ### Get edge(Already generated timber node and joint point node) ###
                    id = str(edge_to_get.start_node.id) + "-" + str(joint_pt_node.id)
                    edge1 = Edge(id, edge_to_get.start_node, joint_pt_node)

                    id = str(edge_to_get.end_node.id) + "-" + str(joint_pt_node.id)
                    edge2 = Edge(id, edge_to_get.end_node, joint_pt_node)

                    # Maintain node information
                    self.edges_in_playground += edge1, edge2

                    # Draw edge line in doc
                    edge1.generate_edge_line()
                    edge2.generate_edge_line()

                    ## Record the nodes to which each node is connected
                    # Start node that an edge has
                    temp_connected_nodes = []
                    if len(edge_to_get.start_node.connected_nodes) == 4:
                        for connected_node in edge_to_get.start_node.connected_nodes:
                            if connected_node == edge_to_get.end_node.id:
                                continue
                            else:
                                temp_connected_nodes.append(connected_node)

                        temp_connected_nodes.append(joint_pt_node.id)

                        # Set connected nodes information to an edge
                        edge_to_get.start_node.set_connected_nodes(temp_connected_nodes)

                    else:
                        # Set connected nodes information to an edge
                        edge_to_get.start_node.set_connected_nodes(joint_pt_node.id)

                    # End node that an edge has
                    temp_connected_nodes = []
                    if len(edge_to_get.end_node.connected_nodes) == 4:
                        for connected_node in edge_to_get.end_node.connected_nodes:
                            if connected_node == edge_to_get.start_node.id:
                                continue
                            else:
                                temp_connected_nodes.append(connected_node)

                        temp_connected_nodes.append(joint_pt_node.id)

                        # Set connected nodes information to an edge
                        edge_to_get.end_node.set_connected_nodes(temp_connected_nodes)

                    else:
                        # Set connected nodes information to an edge
                        edge_to_get.end_node.set_connected_nodes(joint_pt_node.id)

                    # Judge whether joint point nodes have two GL node
                    gl_nodes = joint_pt_node.judge_node_on_ground(self.nodes_in_playground)

                    if gl_nodes:
                        id = str(gl_nodes[0].id) + "-" + str(gl_nodes[1].id)
                        edge = Edge(id, gl_nodes[0], gl_nodes[1])

                        # Maintain node information
                        self.edges_in_playground.append(edge)

                        # Draw edge line in doc
                        edge.generate_edge_line()

                    # delete old edge
                    if num_joint_pts == 1:
                        edge_to_get.delete_guid()
                        self.edges_in_playground.remove(edge_to_get)
                    elif num_joint_pts == 2:
                        if i == 0:
                            delete_old_edges.append(edge_to_get)
                        else:
                            delete_old_edges.append(edge_to_get)

                            for old_edge in delete_old_edges:
                                old_edge.delete_guid()
                                self.edges_in_playground.remove(old_edge)

        # Constructing Graphs
        self.graph.set_graph(self.nodes_in_playground, self.edges_in_playground)
        self.graph.create_graph()

        # Detecting cycles in graph using search method
        cycles = Search.detect_cycles_in_graph(self.graph.contiguous_list)
        print("cycles: {0}".format(cycles))

        if cycles:
            self.graph.generate_cycle(cycles, self.nodes_in_playground)

    def reset(self, explode_target_lines):
        # 生成した部材を記録しておく
        for timber in self.adding_timbers:
            self.timber_list_in_playground.append(timber)

        # reset
        self.adding_timber = None
        self.adding_timbers = []
        self.adding_target_line = None
        rs.DeleteObjects(explode_target_lines)

        print("")
