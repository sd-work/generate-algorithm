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
import time
import csv
import target_line
reload(target_line)

import timber
reload(timber)

from timber import *
from target_line import TargetLine
from optiimization import *
from bolt import Bolt

from graph.graph import Graph
from graph.node import Node
from graph.edge import Edge
from graph.search import Search

from delaunay.delaunay import delaunay_triangulation
from delaunay.delaunay import get_adjacent_relationships

from structural_analysis.structural_analysis import Structure

num_joint_pts = 0
joint_pts_info = []


class Playground:

    def __init__(self):
        self.timber_list_in_database = []  # データベース上にある部材

        # About adding timber
        self.adding_timber = None
        self.adding_timbers = []
        self.adding_target_line = None

        # About Structure model
        self.structure = Structure()  # 構造体モデル(化)
        self.timbers_in_structure = []  # 遊び場を構成している部材
        self.nodes_in_structure = []  # 構造体が保持するノード群
        self.edges_in_structure = []  # 構造体が保持するエッジ群
        self.main_edges_in_structure = []  # 構造体が保持する主構造のエッジ群
        self.sub_edges_in_structure = []  # 構造体が保持するサブ構造のエッジ群
        self.bolts_in_structure = []  # 構造体が保持するボルト群(今回はボルトも部材の1つとしてカウントする )

        # About Boundary
        self.boundary_pts = []

        # About Nodal Load
        self.free_end_coordinates = []  # 荷重をかける座標点群
        self.support_pt_coordinates = []  # サブ構造の支点座標群
        self.mid_pt_coordinates = []  # 主構造のedgeの中心点座標群
        self.mid_pt_coordinates_on_split_edges = []  # 主構造のedgeを分割し、連結したsplit edges lineの中心点座標群

        # About section list
        self.edge_section_list = []  # 各edgeのsecのindex番号を格納

    # 00. 部材データを生成する Todo ここはスキャンした3Dデータに切り替える
    def generate_timber_info(self, num_timber):
        for id in range(num_timber):
            timber = Timber(id)
            timber.generate_timber_info(random.randint(700, 2000))
            self.timber_list_in_database.append(timber)

            # 木材の情報をcsvファイルとして書き出す
            timber.export_csv_file("timber_" + str(id + 1))

    # 00. 生成した部材データをCSVファイルとして出力する
    def export_csv_file(self):
        path = r"G:\マイドライブ\2021\04_Master\2104_GenerationAlgorithm\RhinoPython\csv\timber_info.csv"

        with open(path, "w") as csv_file:
            writer = csv.writer(csv_file)

            for timber in self.timber_list_in_database:
                # TODO サーバーとやりとりをするので、データベース上に使用した材かどうかの記述をするように変更する
                writing_info = [timber.id, timber.length, timber.path_to_csv.encode("utf-8")]
                writer.writerow(writing_info)

        self.timber_list_in_database = []  # reset

    # 01. Layerを生成する
    @staticmethod
    def create_playground_layer():
        # playground layer
        rs.AddLayer("playground", [0, 0, 0], True, False, None)

        # structure model layer
        rs.AddLayer("structure_model", [0, 0, 0], False, False, None)
        rs.AddLayer("node", [0, 0, 0], True, False, "structure_model")
        rs.AddLayer("edge", [0, 0, 0], True, False, "structure_model")
        rs.AddLayer("split_edge", [0, 0, 0], True, False, "structure_model")
        rs.AddLayer("split_master_edge", [0, 0, 0], True, False, "structure_model")
        rs.AddLayer("bolt", [0, 0, 0], True, False, "structure_model")

        rs.AddLayer("main", [0, 0, 0], True, False, "edge")
        rs.AddLayer("sub", [0, 0, 0], True, False, "edge")
        rs.AddLayer("split_main", [0, 0, 0], True, False, "edge")

        rs.AddLayer("main_split", [0, 0, 0], True, False, "split_edge")
        rs.AddLayer("sub_split", [0, 0, 0], True, False, "split_edge")

        rs.AddLayer("master_main_split", [0, 0, 0], True, False, "split_master_edge")
        rs.AddLayer("master_sub_split", [0, 0, 0], True, False, "split_master_edge")

    # 01. Instance情報から、構造体を復元する
    def restore_playground_instance(self):
        # About Timber
        for timber in self.timbers_in_structure:
            timber.restore_timber_instance()  # draw
            timber.set_user_text()  # set user text

        # About structure model
        for node in self.nodes_in_structure:
            node.generate_node_point("node")  # draw

        for edge in self.edges_in_structure:
            edge.generate_edge_line("edge")  # draw
            edge.set_user_text()

            # About split edges line on timber center line
            if edge.split_edges_guid:
                edge.split_edges_guid = []

            # About split edges line on master edge
            if edge.split_edges_guid_master_edge:
                edge.split_edges_guid_master_edge = []

            # About divided edges of main master edge
            if edge.divided_two_edges_guid:
                edge.divided_two_edges_guid = []

        self.structure.set_edges_to_main_sub_layer()  # layerを振り分ける

        for bolt in self.bolts_in_structure:
            bolt.draw_line_guid("bolt")
            bolt.set_user_text()  # ばねモデルの剛性を設定

    # 02. 部材データ(CSV)を読み込む
    def open_csv_file(self):
        path = r"G:\マイドライブ\2021\04_Master\2104_GenerationAlgorithm\RhinoPython\csv\timber_info.csv"

        # 遊び場を構成している部材群を初期化する
        # self.timbers_in_structure = []

        with codecs.open(path, "r", "utf-8") as csv_file:
            reader = csv.reader(csv_file)
            for info in reader:
                if not info:
                    continue
                self.timber_list_in_database.append(Timber(info[0], info[1], info[2], "playground"))

    # 03. Target Lineを取得する(Rhino Pythonから取得)
    def get_target_line(self):
        self.adding_target_line = TargetLine.get_target_line()

    # 03. Target Lineを取得する(ARから取得)
    def get_target_line_from_pts(self, target_line_gh):
        target_line_guid = rs.AddLine(target_line_gh[0], target_line_gh[1])
        self.adding_target_line = TargetLine(target_line_guid)  # TargetLine instance

        # if target_line_gh:
        #     print(type(target_line_gh))
        #     rs.DeleteObject(target_line_gh)

    # 04. 取得したTarget Lineから、部材を選定する Todo いずれはデータベースから検索する
    def select_adding_timber(self, target_line_guid=None):

        # 取得したターゲット曲線情報から、木材を追加するための新たなターゲット曲線情報を取得
        # target_length, self.adding_target_line = Optimization.edit_adding_timber_range(target_line, num_of_joint_pt)

        # 既に生成されている木材のidリストを作成する
        used_timbers_id = [timber.id for timber in self.timbers_in_structure]

        # 木材の参照長さに最も近似した長さの木材を検索し、取得する
        if target_line_guid:
            self.adding_target_line = TargetLine(target_line_guid)

            select_timber = Optimization.get_best_timber_in_database(self.timber_list_in_database,
                                                                     self.adding_target_line,
                                                                     used_timbers_id)
        else:
            select_timber = Optimization.get_best_timber_in_database(self.timber_list_in_database,
                                                                     self.adding_target_line,
                                                                     used_timbers_id)

        self.adding_timber = select_timber  # adding timberの設定
        self.adding_timber.target_line = self.adding_target_line  # ターゲット曲線を設定
        self.adding_timber.generate_timber()  # 木材を生成
        self.adding_timbers.append(self.adding_timber)

        #  ターゲット曲線から木材の生成パターンを判定する
        self.adding_timber.judge_timber_pattern(self.adding_target_line, self.timbers_in_structure)

    # 05. 移動や回転を行い、木材を所定の位置に配置する
    def transform_timber(self):
        # translate
        origin_p = self.adding_timber.center_line.PointAtStart  # timberの端点
        transform_p = self.adding_target_line.start_p  # ターゲット曲線の端点
        self.adding_timber.translate_timber(origin_p, transform_p)

        # rotation
        vector_timber = Rhino.Geometry.Vector3d(
            self.adding_timber.center_line.PointAtEnd - self.adding_timber.center_line.PointAtStart)
        angle = Vector3d.VectorAngle(vector_timber, self.adding_target_line.vector)
        axis = Vector3d.CrossProduct(vector_timber, self.adding_target_line.vector)
        rotation_center = self.adding_timber.center_line.PointAtStart
        self.adding_timber.rotate_timber(angle, axis, rotation_center)

    # 06. 木材の表面の最適化を行う
    def minimized_joint_area(self, connected_timber_ids=None):
        global num_joint_pts, joint_pts_info

        # ターゲット曲線の情報から接合点、ベクトルを計算し、取得する
        joint_pts_info = Optimization.get_joint_pts_info(self.adding_timbers, self.timbers_in_structure,
                                                         connected_timber_ids)

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

    # 07. モデル化した構造体モデルから現状の構造体の状況を計算する
    def analysis_structure(self, index):

        num_nodes_in_structure = len(self.nodes_in_structure)

        # 新たに生成した部材を記録しておく
        for timber in self.adding_timbers:
            self.timbers_in_structure.append(timber)

        """Get node in structure"""
        # About both ends of timber
        node1 = Node(num_nodes_in_structure, self.adding_timber.center_line.PointAtStart)
        node2 = Node(num_nodes_in_structure + 1, self.adding_timber.center_line.PointAtEnd)

        node1.structural_type = 0  # 自由端
        node2.structural_type = 0  # 自由端

        # judge whether node1 and node2 is support point
        if -100 <= node1.z <= 100:
            node1.structural_type = 1  # 支点
            self.adding_timber.is_generated_from_GL = True

            # Maintain node information
            self.structure.set_support_pt_nodes([node1])

        if -100 <= node2.z <= 100:
            node2.structural_type = 1  # 支点
            self.adding_timber.is_generated_from_GL = True

            # Maintain node information
            self.structure.set_support_pt_nodes([node2])

        # Draw node point in doc
        node1.generate_node_point("node")
        node2.generate_node_point("node")

        # Maintain node information
        self.nodes_in_structure += node1, node2

        # About joint points
        # If there are not joint points
        if num_joint_pts == 0:
            joint_pts_nodes = None

        # If there are some joint points
        else:
            # Get joint point nodes
            joint_pts_nodes = Graph.create_node_from_joint_pts(num_nodes_in_structure, joint_pts_info)

            # Maintain node information
            self.nodes_in_structure.extend(joint_pts_nodes)
            self.structure.set_joint_pt_nodes(joint_pts_nodes)

        """Get edge in structure"""
        bolts = Graph.detect_edges_of_structure(num_joint_pts, node1, node2, self.edges_in_structure,
                                                joint_pts_nodes,
                                                self.adding_timber)

        """Generate Bolt instance"""
        for ends_bolt in bolts:
            id = "bolt-" + str(len(self.bolts_in_structure))

            bolt = Bolt(id, ends_bolt[0], ends_bolt[1])
            self.bolts_in_structure.append(bolt)

            # draw bolt line in doc
            bolt.draw_line_guid("bolt")

        """Set timbers , nodes and edges to structure instance"""
        self.structure.set_timbers(self.timbers_in_structure)
        self.structure.set_nodes(self.nodes_in_structure)
        self.structure.set_edges(self.edges_in_structure, True)
        self.structure.set_bolts(self.bolts_in_structure)

        """Calculate redundancy of structure by using decision formula"""
        self.structure.calc_degree_of_redundancy()
        self.structure.draw_information(index)  # draw information of structure in doc and console

        """Color code timber"""
        # Todo ここは全ての部材を渡すのではなく、新たに生成されたオブジェクトのみを渡すように変更する
        self.structure.color_code_timbers()

        # 処理時間を表示
        # elapsed_time1 = t2 - t1
        # elapsed_time2 = t3 - t2
        # elapsed_time3 = t4 - t3
        # elapsed_time4 = t5 - t4
        # elapsed_time5 = t6 - t5

        # print("get_all_edges: {0}".format(elapsed_time1))
        # print("generate_bolt: {0}".format(elapsed_time2))
        # print("set_var: {0}".format(elapsed_time3))
        # print("calc_redundancy: {0}".format(elapsed_time4))
        # print("color_code: {0}".format(elapsed_time5))

    # 08. 変数をリセットする
    def reset(self):
        # Print the information of adding timber
        # for timber in self.timbers_in_structure:
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

    # 09. section listを作成し、csv形式で保存する→OpenSeesで使用するため
    def create_section_csv_list(self, section_list_path=None):

        self.edge_section_list = []  # init

        if section_list_path:
            pass
        else:
            section_list_path = "section_list\\section_list.csv"

        with open(section_list_path, "w") as f:
            # headerの設定
            fieldnames = ["No.", "S", "P1", "P2", "P3", "P4"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")  # 書き込みの空白を削除する
            writer.writeheader()

            # データの書き込み
            for edge in self.edges_in_structure:
                """master edge"""
                master_sec_id = len(self.edge_section_list)  # 0~n番と順番に書き込まないとGH側でエラーがでる

                # master edgeにsection idを設定
                edge.section_id = master_sec_id  # set section id
                self.edge_section_list.append(master_sec_id)

                # master edgeの属性ユーザーテキストを設定
                edge.set_user_text()  # joint, secを設定

                # 断面直径を計算する(master edgeは平均値を直径として割り当てる)
                edge.calc_average_diameter_of_section()

                # 断面情報をcsvに書き込む
                diameter = edge.diameter_of_section  # 断面直径(平均値)
                writer.writerow(
                    {"No.": edge.section_id, "S": "2", "P1": str(diameter), "P2": "0", "P3": "0", "P4": "0"})

                """split edge (child edge)"""
                for index, split_edge_guid in enumerate(edge.split_edges_guid):
                    sec_id = len(self.edge_section_list)  # 0~n番と順番に書き込まないとGH側でエラーがでる
                    self.edge_section_list.append(master_sec_id)

                    # split edge guid(timber center line)の属性ユーザーテキストを設定
                    rs.SetUserText(split_edge_guid, "joint", "3")  # joint
                    rs.SetUserText(split_edge_guid, "sec", str(sec_id))  # section id

                    # split edge guid(master edge)の属性ユーザーテキストを設定
                    rs.SetUserText(edge.split_edges_guid_master_edge[index], "joint", "3")  # joint
                    rs.SetUserText(edge.split_edges_guid_master_edge[index], "sec", str(sec_id))  # section id

                    # 断面情報をcsvに書き込む
                    diameter = edge.calc_diameter_of_section(index)
                    writer.writerow(
                        {"No.": str(sec_id), "S": "2", "P1": str(diameter), "P2": "0", "P3": "0", "P4": "0"})

    # 10. 構造解析で使用する荷重情報を取得する→OpenSeesで使用するため
    def get_nodal_load_info(self, split_num):
        # main sub structureを設定
        self.main_edges_in_structure = self.structure.main_edges
        self.sub_edges_in_structure = self.structure.sub_edges

        # About Nodal Loadを初期化
        self.mid_pt_coordinates = []  # 主構造のedgeの中心点座標群
        self.mid_pt_coordinates_on_split_edges = []  # 主構造のedgeを分割し、連結したsplit edges lineの中心点座標群
        self.free_end_coordinates = []  # 荷重をかける座標点群
        self.support_pt_coordinates = []  # サブ構造の支点座標群

        # main edgeの中央荷重点を取得
        for main_edge in self.main_edges_in_structure:
            # master edgeを2分割にし、その分割点(中央点)を取得する
            main_edge.divide_edge_two_edge(split_num)

            self.mid_pt_coordinates.append(main_edge.mid_pt)
            self.mid_pt_coordinates_on_split_edges.append(main_edge.mid_pt_on_split_edges_line)

            # main edgeが境界条件の1つになっている場合
            boundary_pt = main_edge.get_boundary_pt()
            if boundary_pt:
                self.boundary_pts.append(boundary_pt)

        # sub edgeの自由端荷重点を取得
        for sub_edges in self.sub_edges_in_structure:
            for sub_edge in sub_edges:
                nodal_pt, support_pt = sub_edge.get_free_end_coordinate()
                if nodal_pt:
                    self.free_end_coordinates.append(nodal_pt)
                if support_pt:
                    self.support_pt_coordinates.append(support_pt)

                # sub edgeが境界条件の1つになっている場合
                boundary_pt = sub_edge.get_boundary_pt()
                if boundary_pt:
                    self.boundary_pts.append(boundary_pt)

    # 10. 属性User textを設定する→OpenSeesで使用するため
    def set_user_text(self):
        # timber
        for timber in self.timbers_in_structure:
            timber.set_user_text()

        # bolt edge
        for bolt in self.bolts_in_structure:
            bolt.set_user_text()  # ばねモデルの剛性を設定

