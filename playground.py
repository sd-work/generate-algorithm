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

        # About Real graph
        self.real_graph = Graph("real", [], [])
        self.nodes_in_playground = []  # 現状の構築物に存在するノード群
        self.edges_in_playground = []  # 現状の構築物に存在するエッジ群
        self.cycle_in_playground = []  # 現状の構築物に存在するサイクル群

        # About Virtual graph
        self.virtual_graph = Graph("virtual", [], [])
        self.nodes_in_virtual = []  # virtual graphに存在するノード群
        self.edges_in_virtual = []  # virtual graphに存在するエッジ群
        self.cycle_in_virtual = []  # virtual graphに存在するサイクル群

        self.adding_timber = None
        self.adding_timbers = []
        self.adding_target_line = None

    # 部材データを生成する TODO ここはスキャンした3Dデータに切り替える
    def generate_timber_info(self, num_timber):
        for id in range(num_timber):
            timber = Timber(id)
            timber.generate_timber_info(random.randint(700, 2000))
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

        # real graph layer
        rs.AddLayer("real_graph", [0, 0, 0], False, False, None)
        rs.AddLayer("r-node", [0, 0, 0], True, False, "real_graph")
        rs.AddLayer("r-edge", [0, 0, 0], True, False, "real_graph")
        rs.AddLayer("r-cycle", [0, 0, 0], True, False, "real_graph")

        # virtual graph layer
        rs.AddLayer("virtual_graph", [0, 0, 0], False, False, None)
        rs.AddLayer("v-node", [0, 0, 0], True, False, "virtual_graph")
        rs.AddLayer("v-edge", [0, 0, 0], True, False, "virtual_graph")
        rs.AddLayer("v-cycle", [0, 0, 0], True, False, "virtual_graph")

    def get_target_line(self):
        self.adding_target_line = TargetLine.get_target_line()

    def select_adding_timber(self):

        # 取得したターゲット曲線情報から、木材を追加するための新たなターゲット曲線情報を取得
        # target_length, self.adding_target_line = Optimization.edit_adding_timber_range(target_line, num_of_joint_pt)

        # 木材の参照長さに最も近似した長さの木材を検索し、取得する
        select_timber = Optimization.get_best_timber_in_database(self.timber_list_in_database, self.adding_target_line)

        self.adding_timber = select_timber
        self.adding_timber.target_line = self.adding_target_line  # ターゲット曲線を設定
        self.adding_timber.generate_timber()  # 木材を生成
        self.adding_timbers.append(self.adding_timber)

        #  ターゲット曲線から木材の生成パターンを判定する
        self.adding_timber.judge_timber_pattern(self.adding_target_line, self.timber_list_in_playground)

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
        print("num_joint_pts: {0}".format(num_joint_pts))

        num_nodes_in_playground = len(self.real_graph.nodes)

        for adding_timber in self.adding_timbers:

            """Get Node in Real graph"""
            node1 = Node(num_nodes_in_playground, adding_timber.center_line.First)
            node2 = Node(num_nodes_in_playground + 1, adding_timber.center_line.Last)

            # Regard GL point node as Joint point node
            if -50 <= node1.z <= 50:
                adding_timber.joint_pts_nodes.append(node1)

            if -50 <= node2.z <= 50:
                adding_timber.joint_pts_nodes.append(node2)

            # Draw node in doc
            node1.generate_node_point("r-node")
            node2.generate_node_point("r-node")

            # Maintain node information
            self.nodes_in_playground += node1, node2

            """Get Edge in Real graph """
            # If there are not joint point
            if num_joint_pts == 0:
                joint_pts_nodes = None

            # If there are some joint points
            else:
                # Get joint point nodes
                joint_pts_nodes = Graph.create_node_from_joint_pts(num_nodes_in_playground, joint_pts_info)

                # Maintain node information
                self.nodes_in_playground.extend(joint_pts_nodes)

            # Detecting edges in real graph
            self.real_graph.detect_edge_of_real_graph(num_joint_pts, node1, node2, self.edges_in_playground,
                                                      joint_pts_nodes, adding_timber)

        # Constructing Real Graphs
        self.real_graph.set_graph(self.nodes_in_playground, self.edges_in_playground)
        self.real_graph.create_graph()

        # Detecting cycles in real graph by using search method
        cycles = Search.detect_cycles_in_graph(self.real_graph)
        print("real cycles: {0}".format(cycles))

        # If some cycles are detected
        if cycles:
            # Drawing cycle mesh or polyline in doc
            new_cycles = self.real_graph.generate_cycle(cycles, self.nodes_in_playground, "r-cycle")

            # If a new real cycle is detected
            if new_cycles:

                # Maintain cycle information
                for real_cycle in new_cycles:
                    self.cycle_in_playground.append(real_cycle)

                    """Get virtual Node based on a new real cycle"""
                    virtual_node = Node("v" + str(len(self.cycle_in_playground)), real_cycle.centroid,
                                        real_cycle.composition_nodes,
                                        real_cycle.is_on_GL)

                    # Draw node in doc
                    virtual_node.generate_node_point("v-node")

                    # Maintain node information
                    self.nodes_in_virtual.append(virtual_node)

                    """Get virtual Edge"""
                    # Search edges of virtual graph
                    adding_virtual_nodes = self.virtual_graph.detect_edge_of_virtual_graph(virtual_node,
                                                                                           self.edges_in_playground,
                                                                                           self.edges_in_virtual)

                    # Maintain node information
                    for adding_virtual_node in adding_virtual_nodes:
                        if adding_virtual_node in self.nodes_in_virtual:
                            continue
                        else:
                            self.nodes_in_virtual.append(adding_virtual_node)

                    ###################################################################
                    # Judge whether nodes in virtual have two GL node TODO 処理方法を検討
                    gl_nodes = []

                    for v_node in self.nodes_in_virtual:
                        if v_node.is_on_GL:
                            gl_nodes.append(v_node)

                    if len(gl_nodes) == 2:
                        # Record the nodes to which each node is connected
                        if not (gl_nodes[1] in gl_nodes[0].connected_nodes):
                            gl_nodes[0].connected_nodes.append(gl_nodes[1])

                            if not (gl_nodes[0] in gl_nodes[1].connected_nodes):
                                gl_nodes[1].connected_nodes.append(gl_nodes[0])

                                id = str(gl_nodes[0].id) + "-" + str(gl_nodes[1].id)
                                edge = Edge(id, gl_nodes[0], gl_nodes[1], None)

                                # Maintain node information
                                if edge in self.edges_in_virtual:
                                    print("---pass---")
                                    pass
                                else:
                                    self.edges_in_virtual.append(edge)

                                    # Draw edge line in doc
                                    edge.generate_edge_line("v-edge")
                    ###################################################################

                    # Constructing Virtual Graphs
                    self.virtual_graph.set_graph(self.nodes_in_virtual, self.edges_in_virtual)
                    self.virtual_graph.create_graph()

                    # Append Virtual Node information
                    # 1. ノードを保持する履歴リストが空である場合
                    if not self.virtual_graph.virtual_node_history:
                        if virtual_node.having_edges_to_virtual_node:
                            for edge in virtual_node.having_edges_to_virtual_node:
                                some_history_list = []
                                history_list = []

                                if edge.start_node is virtual_node:
                                    previous_virtual_node = edge.end_node
                                else:
                                    previous_virtual_node = edge.start_node

                                history_list += previous_virtual_node, virtual_node
                                some_history_list.append(history_list)

                                # 各履歴を保持しておくリストに追加する
                                self.virtual_graph.virtual_node_history.append(some_history_list)
                        else:
                            some_history_list = []
                            history_list = [virtual_node]

                            some_history_list.append(history_list)

                            # 各履歴を保持しておくリストに追加する
                            self.virtual_graph.virtual_node_history.append(some_history_list)

                    # 2. 何らかのノード情報を履歴リストが既に持っている場合
                    else:
                        for node_history_list in self.virtual_graph.virtual_node_history:
                            for node_history in node_history_list:
                                node_history.append(virtual_node)

                    # debug
                    for node_history_list in self.virtual_graph.virtual_node_history:
                        for node_history in node_history_list:
                            print("---")
                            for node in node_history:
                                print("Node history: {0}".format(node.id))

                    # Detecting cycles in virtual graph by using search method
                    if self.virtual_graph.virtual_node_history:
                        find_cycles = Search.search_virtual_cycle(self.virtual_graph.virtual_node_history)

                        if find_cycles:
                            print("---Find new cycle---")
                            print(find_cycles)

                            # Drawing virtual cycle mesh in doc
                            new_cycles, delete_cycles = self.virtual_graph.generate_cycle(find_cycles,
                                                                                          self.nodes_in_virtual,
                                                                                          "v-cycle")

                            # 新しいvirtual cycle が検出された場合
                            if new_cycles:
                                # Maintain virtual cycle information
                                for virtual_cycle in new_cycles:
                                    self.cycle_in_virtual.append(virtual_cycle)

                                # 変数をリセットする
                                self.virtual_graph.virtual_node_history = []

                            # 古いサイクルがある場合、削除する
                            if delete_cycles:
                                for delete_cycle in delete_cycles:
                                    if delete_cycle in self.cycle_in_virtual:
                                        self.cycle_in_virtual.remove(delete_cycle)

                        print("virtual cycles: {0}".format(self.virtual_graph.cycles))

        # 新たに生成した部材を記録しておく
        for timber in self.adding_timbers:
            self.timber_list_in_playground.append(timber)

        # 部材の色分けを行う(全体の判定 -> 部分の判定)
        self.virtual_graph.color_code_timbers(self.timber_list_in_playground)

    def reset(self):
        # Print the information of adding timber
        # for timber in self.timber_list_in_playground:
        #     print("timber{0} has {1} joint points".format(timber.id, len(timber.joint_pts_nodes)))
        #     print("timber{0} has {1} rigid points".format(timber.id, len(timber.rigid_joints)))
        #     print("timber{0} has {1} nodes".format(timber.id, [node.point for node in timber.nodes]))
        #     print("")

        # reset
        self.adding_target_line.delete_line_guid()
        self.adding_timber = None
        self.adding_timbers = []
        self.adding_target_line = None

        print("")
