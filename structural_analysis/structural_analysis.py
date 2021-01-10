# coding: utf-8

import copy
import time
import Rhino
from Rhino.Geometry import *
import scriptcontext
import rhinoscriptsyntax as rs

from .component import LineTimber


# from component import LineTimber


class Structure:

    def __init__(self):
        # About element of structure
        self.timbers = []  # timber instances

        self.nodes = []  # 節点数(支点、自由端、接合部)
        self.edges = []  # 部材数(s)に相当
        self.main_edges = []  # 主構造を構成するエッジ
        self.sub_edges = []  # サブ構造を構成するエッジ
        self.bolts = []  # ボルト
        self.support_pt_nodes = []  # 支点ノード
        self.joint_pts_nodes = []  # 接合部ノード

        # About decision formula
        self.n = 0  # 支点反力数
        self.s = 0  # 部材数
        self.r = 0  # 剛接合部材数
        self.k = 0  # 節点数
        self.m = 0  # 不静定次数
        self.status = 0  # 構造体の状態  0: 不安定 1: 静定 2: 不静定

        # About Guid
        self.text_guid = None
        self.gl_line = None

    def set_main_sub_edges(self, main_structure_edges, sub_structure_edges):
        self.main_edges = []  # init
        self.sub_edges = []  # init

        self.main_edges = main_structure_edges
        self.sub_edges = sub_structure_edges

    def set_timbers(self, timbers):
        for timber in timbers:
            if timber in self.timbers:
                continue
            else:
                self.timbers.append(timber)

    def set_nodes(self, nodes, extend_list=False):
        if extend_list:
            self.nodes = []
            self.nodes.extend(nodes)

        else:
            for node in nodes:
                if node in self.nodes:
                    continue
                else:
                    self.nodes.append(node)

    def set_edges(self, edges, extend_list=False):
        if extend_list:
            self.edges = []
            self.edges.extend(edges)

        else:
            for edge in edges:
                if edge in self.edges:
                    continue
                else:
                    self.edges.append(edge)

    def set_bolts(self, bolts):
        for bolt in bolts:
            if bolt in self.bolts:
                continue
            else:
                self.bolts.append(bolt)

    def set_support_pt_nodes(self, support_pt_nodes):
        for support_pt_node in support_pt_nodes:
            if support_pt_node in self.support_pt_nodes:
                continue
            else:
                self.support_pt_nodes.append(support_pt_node)

    def set_joint_pt_nodes(self, joint_pts_nodes):
        for joint_pt_node in joint_pts_nodes:
            if joint_pt_node in self.joint_pts_nodes:
                continue
            else:
                self.joint_pts_nodes.append(joint_pt_node)

    def set_edges_to_main_sub_layer(self, split_num=10):

        # main structure
        for master_edge in self.main_edges:
            # master main edge
            master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "main")
            rs.ObjectLayer(master_edge.edge_line_guid, master_layer)  # set object layer
            rs.ObjectColor(master_edge.edge_line_guid, [0, 0, 255])  # Blue

            # 既に分割済みのmaster edgeは処理しない
            if master_edge.split_edges_guid:
                continue
            else:
                # 01. split edge(timber center line)
                master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "main_split")

                if master_edge.split_edges:
                    for split_edge in master_edge.split_edges:
                        split_edge_guid = scriptcontext.doc.Objects.AddLine(split_edge)
                        master_edge.split_edges_guid.append(split_edge_guid)

                    for split_edge in master_edge.split_edges_master_edge:
                        split_edge_guid = scriptcontext.doc.Objects.AddLine(split_edge)
                        master_edge.split_edges_guid_master_edge.append(split_edge_guid)

                else:
                    # master edgeを分割し、その分割線(split edge guid)を取得する
                    master_edge.split_master_edge_to_segmented_edges(split_num)

                # layerとcolorを割り当てる
                for i, split_edge_guid in enumerate(master_edge.split_edges_guid):
                    layer_name = master_edge.id + "-" + str(i)
                    layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_layer)
                    rs.ObjectLayer(split_edge_guid, layer)  # set object layer
                    rs.ObjectColor(split_edge_guid, [0, 0, 255])  # Blue

                # 02. split edge(master frame edge)
                master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "master_main_split")

                # layerとcolorを割り当てる
                for i, split_edge_guid in enumerate(master_edge.split_edges_guid_master_edge):
                    layer_name = "m-" + str(master_edge.id) + "-" + str(i)
                    layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_layer)
                    rs.ObjectLayer(split_edge_guid, layer)  # set object layer
                    rs.ObjectColor(split_edge_guid, [0, 0, 255])  # Blue

                # 03. divided edge(master frame edge)
                master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "split_main")

                for i, divided_edge_guid in enumerate(master_edge.divided_two_edges_guid):
                    layer_name = "s" + "-" + str(master_edge.id) + "-" + str(i)
                    layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_layer)

                    rs.ObjectLayer(divided_edge_guid, layer)  # set object layer
                    rs.ObjectColor(divided_edge_guid, [0, 0, 255])  # Blue

        # sub structure
        for edges in self.sub_edges:
            # 01. 片持ち群
            if len(edges) >= 2:
                for master_edge in edges:
                    master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "sub")
                    rs.ObjectLayer(master_edge.edge_line_guid, master_layer)  # set object layer
                    rs.ObjectColor(master_edge.edge_line_guid, [255, 140, 0])  # orange

                    # 既に分割済みのmaster edge(timber center line)は処理しない
                    if master_edge.split_edges_guid:
                        continue
                    else:
                        # 01. split edge(timber center line)
                        master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "sub_split")

                        if master_edge.split_edges:
                            for split_edge in master_edge.split_edges:
                                split_edge_guid = scriptcontext.doc.Objects.AddLine(split_edge)
                                master_edge.split_edges_guid.append(split_edge_guid)

                            for split_edge in master_edge.split_edges_master_edge:
                                split_edge_guid = scriptcontext.doc.Objects.AddLine(split_edge)
                                master_edge.split_edges_guid_master_edge.append(split_edge_guid)

                        else:
                            # master edgeを分割し、その分割線(split edge guid)を取得する
                            master_edge.split_master_edge_to_segmented_edges(split_num)

                        for i, split_edge_guid in enumerate(master_edge.split_edges_guid):
                            layer_name = master_edge.id + "-" + str(i)
                            layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_layer)
                            rs.ObjectLayer(split_edge_guid, layer)  # set object layer
                            rs.ObjectColor(split_edge_guid, [255, 140, 0])  # orange

                        # 02. split edge(master frame edge)
                        master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "master_sub_split")

                        # layerとcolorを割り当てる
                        for i, split_edge_guid in enumerate(master_edge.split_edges_guid_master_edge):
                            layer_name = "m-" + str(master_edge.id) + "-" + str(i)
                            layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_layer)
                            rs.ObjectLayer(split_edge_guid, layer)  # set object layer
                            rs.ObjectColor(split_edge_guid, [255, 140, 0])  # orange

            # 02. 片持ち
            else:
                for master_edge in edges:
                    master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "sub")
                    rs.ObjectLayer(master_edge.edge_line_guid, master_layer)  # set object layer
                    rs.ObjectColor(master_edge.edge_line_guid, [255, 255, 0])  # yellow

                    # 既に分割済みのmaster edge(timber center line)は処理しない
                    if master_edge.split_edges_guid:
                        continue
                    else:
                        # 01. split edge(timber center line)
                        master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "sub_split")

                        if master_edge.split_edges:
                            for split_edge in master_edge.split_edges:
                                split_edge_guid = scriptcontext.doc.Objects.AddLine(split_edge)
                                master_edge.split_edges_guid.append(split_edge_guid)

                            for split_edge in master_edge.split_edges_master_edge:
                                split_edge_guid = scriptcontext.doc.Objects.AddLine(split_edge)
                                master_edge.split_edges_guid_master_edge.append(split_edge_guid)

                        else:
                            # master edgeを分割し、その分割線(split edge guid)を取得する
                            master_edge.split_master_edge_to_segmented_edges(split_num)

                        for i, split_edge_guid in enumerate(master_edge.split_edges_guid):
                            layer_name = master_edge.id + "-" + str(i)
                            layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_layer)
                            rs.ObjectLayer(split_edge_guid, layer)  # set object layer
                            rs.ObjectColor(split_edge_guid, [255, 255, 0])  # yellow

                        # 02. split edge(master frame edge)
                        master_layer = rs.AddLayer(str(master_edge.id), [0, 0, 0], True, False, "master_sub_split")

                        # layerとcolorを割り当てる
                        for i, split_edge_guid in enumerate(master_edge.split_edges_guid_master_edge):
                            layer_name = "m-" + str(master_edge.id) + "-" + str(i)
                            layer = rs.AddLayer(layer_name, [0, 0, 0], True, False, master_layer)
                            rs.ObjectLayer(split_edge_guid, layer)  # set object layer
                            rs.ObjectColor(split_edge_guid, [255, 255, 0])  # yellow

        # Delete old layer
        # main layer内のempty layerを削除する
        parent = rs.LayerChildren("main")
        if parent:
            for child in parent:
                if rs.IsLayerEmpty(child):
                    rs.DeleteLayer(child)

        # sub layer内のempty layerを削除する
        parent = rs.LayerChildren("sub")
        if parent:
            for child in parent:
                if rs.IsLayerEmpty(child):
                    rs.DeleteLayer(child)

        # main split layer内のempty layerを削除する
        parent = rs.LayerChildren("main_split")
        if parent:
            for child in parent:
                if rs.IsLayerEmpty(child):
                    rs.DeleteLayer(child)

        # sub split layer内のempty layerを削除する
        parent = rs.LayerChildren("sub_split")
        if parent:
            for child in parent:
                if rs.IsLayerEmpty(child):
                    rs.DeleteLayer(child)

        # master_main_split layer内のempty layerを削除する
        parent = rs.LayerChildren("master_main_split")
        if parent:
            for child in parent:
                if rs.IsLayerEmpty(child):
                    rs.DeleteLayer(child)

        # master_sub_split layer内のempty layerを削除する
        parent = rs.LayerChildren("master_sub_split")
        if parent:
            for child in parent:
                if rs.IsLayerEmpty(child):
                    rs.DeleteLayer(child)

    def calc_degree_of_redundancy(self):
        num_joint_pts = len(self.joint_pts_nodes)  # 接合部数(ボルト接合してる箇所)
        self.s = 0  # 部材数は0で初期化
        self.k = 0  # 節点数は0で初期化

        # 支点反力数(n)
        self.n = len(self.support_pt_nodes) * 2  # 支点数 × 2(反力数が2なので)

        # 構造体が保持してる部材群(LineTimber Instance)から1つずつ部材を取り出し、部材数(s)と接点数(k)を計算する
        for master_timber in self.timbers:
            if master_timber.split_timbers:
                # master timberが保持するsplit timberの総数 = 部材数(s)としてカウント
                self.s += int(len(master_timber.split_timbers))
            else:
                self.s += 1

            # 自由端 + 支点を節点数(k)としてカウントする
            self.k += 2

        # 部材数(s)
        self.s += len(self.bolts)  # ボルトも部材数としてカウントする(接合部数 = ボルト数)

        # 剛接合部材数(r)
        self.r = num_joint_pts * 3  # 1つの接合部ではrの値を3として考える

        # 節点数(k)
        self.k += len(self.bolts) * 2  # 接合点 = ボルトの両端部(2点)を節点としてカウント

        # 不静定次数(m)
        self.m = (self.n + self.s + self.r) - (2 * self.k)

    def draw_information(self, i):
        # Print information in console
        # print("###{0}###".format(i + 1))
        # print("n: {0}".format(self.n))
        # print("s: {0}".format(self.s))
        # print("r: {0}".format(self.r))
        # print("k: {0}".format(self.k))
        # print("m: {0}".format(self.m))

        # 構造体の判定を行う
        # TODO 基本はmの値で判定を行うが、支点反力数の値が0~2の時はいくらmの値が大きくても不安定とみなす？
        if self.m < 0:
            # print("不安定")
            self.status = 0  # 不安定
        elif self.m == 0:
            # print("静定")
            self.status = 1  # 静定
        else:
            # print("不静定")
            self.status = 2  # 不静定

        # print("")

        # Draw text guid in doc
        if self.text_guid:
            rs.DeleteObject(self.text_guid)

        if self.status == 0:
            status = "不安定"
        elif self.status == 1:
            status = "静定"
        else:
            status = "不静定"

        text = "n={0}  s={1}  r={2}  k={3}".format(self.n, self.s, self.r, self.k) + "\n" + "m={0}".format(
            self.m) + "\n" + str(status)
        point = [850, -150, 0]
        height = 100
        font = "Arial"
        font_style = 0,
        justification = None

        self.text_guid = rs.AddText(text, point, height, font, font_style, justification)

    # ある部材(s)に着目し、その部材が冗長性を持っているかどうかを判定する
    def judge_redundancy_of_test_timber(self, structure_edges=None, edge_type=None):

        # 構造体を構成するedge群
        if structure_edges:
            test_edges = structure_edges
        else:
            test_edges = self.edges

        # 主構造
        if edge_type == "main":

            # すべてのEdgeに対して同じ判定処理を行う
            for test_edge in test_edges:

                # test edgeが取り除かれた時のTimber自体の安定度を判定する
                state = self.judge_stability_of_timber(test_edge)

                """test edge(split timber)が不安定 or キャンチである場合"""
                if state == 0:
                    # master timberが1つの接合点しか持たない + 地面に設置していない場合、その部材は赤色
                    if len(test_edge.timber.joint_pts_nodes) <= 1 and (not test_edge.timber.is_generated_from_GL):
                        # About master timber
                        rs.ObjectColor(test_edge.timber.surface_guid, [0, 0, 0])  # default color

                        # About split timber
                        rs.ObjectColor(test_edge.split_timber.surface_guid, [223, 51, 78])  # 赤色
                        test_edge.split_timber.status = 0  # 赤色
                        continue

                    else:
                        # test edgeは黄色
                        # About master timber
                        rs.ObjectColor(test_edge.timber.surface_guid, [0, 0, 0])  # default color

                        # About split timber
                        rs.ObjectColor(test_edge.split_timber.surface_guid, [225, 225, 0])  # 黄色
                        test_edge.split_timber.status = 1  # 黄色
                        continue

                """main structureの場合"""
                self.set_timber_color(test_edge, degree_of_stability=2)

        # サブ構造
        elif edge_type == "sub":

            for sub_edge in test_edges:
                """sub edge(split timber)が不安定である場合"""
                # master timberが1つの接合点しか持たない + 地面に設置していない場合、その部材は赤色
                if len(sub_edge.timber.joint_pts_nodes) <= 1 and (not sub_edge.timber.is_generated_from_GL):
                    # About master timber
                    rs.ObjectColor(sub_edge.timber.surface_guid, [0, 0, 0])  # default color

                    # About split timber
                    rs.ObjectColor(sub_edge.split_timber.surface_guid, [223, 51, 78])  # 赤色
                    sub_edge.split_timber.status = 0  # 赤色

                else:
                    # 片持ち群の場合はオレンジ、片持ちの場合は黄色
                    # About master timber
                    rs.ObjectColor(sub_edge.timber.surface_guid, [0, 0, 0])  # default color

                    # About split timber
                    # 片持ち群
                    if len(test_edges) >= 2:
                        rs.ObjectColor(sub_edge.split_timber.surface_guid, [255, 165, 0])  # オレンジ
                        sub_edge.split_timber.status = 4  # オレンジ

                    # 片持ち
                    else:
                        rs.ObjectColor(sub_edge.split_timber.surface_guid, [225, 225, 0])  # 黄色
                        sub_edge.split_timber.status = 1  # 黄色

            # """edgeのいずれの端部も自由端ではない場合、次の処理に進む"""
            # # 探索開始位置
            # search_start_nodes = [test_edge.start_node, test_edge.end_node]
            # search_start_nodes_id = [test_edge.start_node.id, test_edge.end_node.id]
            #
            # # 不静定次数を格納するリスト
            # m_list = []
            #
            # for i, search_start_node in enumerate(search_start_nodes):
            #     stack_list = [search_start_node]
            #     history_node_list = [search_start_node]  # history listに search start nodeを格納
            #     history_node_id_list = [search_start_node.id]  # node idを格納。判定に利用する
            #
            #     while stack_list:
            #         # print("stack list: {0}".format(len(stack_list)))
            #
            #         # stack listの最初のノードを取得する
            #         stack_node = stack_list.pop(0)
            #
            #         for connected_node in stack_node.connected_nodes:
            #             # 既にhistory listに存在するノード
            #             if connected_node.id in history_node_id_list:
            #                 continue
            #
            #             # 逆流禁止
            #             if connected_node.id == stack_node.id:
            #                 continue
            #
            #             # test edgeの両端である場合
            #             if stack_node.id in search_start_nodes_id and connected_node.id in search_start_nodes_id:
            #                 continue
            #
            #             # stack listにノードを追加
            #             stack_list.append(connected_node)
            #
            #             # history listにノードを追加
            #             history_node_list.append(connected_node)
            #             history_node_id_list.append(connected_node.id)
            #
            #     # print("history node: {0}".format(len(history_node_list)))
            #     # for node in history_node_list:
            #     #     print(node.id)
            #     #
            #     # print("")
            #
            #     # 構造判定式を用いてmの値を求める
            #     n = 0  # Todo test edgeの端点のいずれかが支点である場合はここも変わる？
            #
            #     count = 0
            #     # sの数はtest edgeの種類によって異なる
            #     for search_node_id in search_start_nodes_id:
            #         if search_node_id in history_node_id_list:
            #             count += 1
            #
            #     # test edgeを1つの部材としてカウントするため -> 以下のhaving edgeでカウントされる？
            #     if count == 2:
            #         s = 2
            #         k = 2  # test edgeの両端(2点)を自由端の節点としてカウントする
            #     elif count == 1:
            #         s = 1
            #         k = 1  # test edgeの一端(1点)を自由端の節点としてカウントする
            #     else:
            #         s = 0
            #         k = 0
            #
            #     r = 0
            #     num_bolts = 0
            #     edge_list = []
            #
            #     t2 = time.time()
            #
            #     # Todo ここに処理時間がかかっている
            #     # print(len(history_node_list))
            #
            #     for node in history_node_list:
            #         if node.structural_type == 0:  # 自由端
            #             k += 1  # 節点
            #
            #         elif node.structural_type == 1:  # 支点
            #             n += 2  # 支点は反力数2
            #             k += 1  # 節点
            #
            #         elif node.structural_type == 2:  # 接合点
            #             num_bolts += 1  # 1つの接合点には1つのボルトが存在。のちに部材数(s)、節点数(k)としてカウント
            #             r += 3  # 1つの接合点はrの値が3としてカウント
            #
            #             # 構造体のedge情報を取得
            #             for having_edge in node.having_edges:
            #                 if having_edge in edge_list:
            #                     continue
            #                 else:
            #                     # having edgeの始点、終点のいずれもがtest edgeの両端と同一な場合
            #                     if having_edge.start_node.id in search_start_nodes_id and having_edge.end_node.id in search_start_nodes_id:
            #                         continue
            #                     else:
            #                         edge_list.append(having_edge)
            #
            #     t3 = time.time()
            #     # print(t3 - t2)
            #
            #     # 部材数(s)
            #     s += len(edge_list) + num_bolts  # ボルトも部材数としてカウント
            #
            #     # 節点(k)
            #     k += num_bolts * 2  # 接合点 = ボルトの両端部(2点)を節点としてカウント
            #
            #     # 不静定次数(m)
            #     m = (n + s + r) - (2 * k)
            #
            #     # 基本はmの値で判定を行うが、支点反力数の値が0~2の時はいくらmの値が大きくても不安定とみなす
            #     if n <= 2:
            #         m = -1
            #
            #     # 不静定次数を格納する
            #     m_list.append(m)
            #
            #     # print("n: {0}".format(n))
            #     # print("s: {0}".format(s))
            #     # print("r: {0}".format(r))
            #     # print("k: {0}".format(k))
            #     # print("m: {0}".format(m))
            #
            # # m listからtest edgeの色を判定する
            # degree_of_stability = 0
            #
            # for m in m_list:
            #     if m < 0:  # 不安定
            #         # degree_of_instability += 1
            #         pass
            #     elif m == 0:  # 静定
            #         degree_of_stability += 1
            #         pass
            #     else:  # 不静定
            #         degree_of_stability += 1
            #         pass
            #
            # print("degree_of_stability: {0}".format(degree_of_stability))
            #
            # """Color code edge split timber"""
            # self.set_timber_color(test_edge, degree_of_stability)

    def set_timber_color(self, test_edge, degree_of_stability):

        # split structure1 or split structure2のいずれかが不安定である場合
        # test edgeが破壊されると、不安定な構造体が生成されてしまうので、冗長性はないと判定する
        if degree_of_stability == 0 or degree_of_stability == 1:
            # master structureが不安定である場合
            if self.status == 0:
                # test.edge.split timberは赤色
                # About master timber
                rs.ObjectColor(test_edge.timber.surface_guid, [0, 0, 0])  # default color

                # About split timber
                rs.ObjectColor(test_edge.split_timber.surface_guid, [223, 51, 78])  # 赤色
                test_edge.split_timber.status = 0  # 赤色

            # master structureが静定である場合
            elif self.status == 1:
                # test.edge.split timberは黄色
                # About master timber
                rs.ObjectColor(test_edge.timber.surface_guid, [0, 0, 0])  # default color

                # About split timber
                rs.ObjectColor(test_edge.split_timber.surface_guid, [225, 225, 0])  # 黄色
                test_edge.split_timber.status = 1  # 黄色

            # master structureが不静定である場合
            elif self.status == 2:
                # test.edge.split timberは黄色
                # About master timber
                rs.ObjectColor(test_edge.timber.surface_guid, [0, 0, 0])  # default color

                # About split timber
                # test edgeのいずれの端点が支点である場合は青色に設定
                if test_edge.start_node.structural_type == 1 or test_edge.end_node.structural_type == 1:
                    rs.ObjectColor(test_edge.split_timber.surface_guid, [157, 204, 255])  # 青色
                    test_edge.split_timber.status = 2  # 青色
                    print("On GL")

                else:
                    rs.ObjectColor(test_edge.split_timber.surface_guid, [0, 255, 0])  # 緑
                    # rs.ObjectColor(test_edge.split_timber.surface_guid, [225, 225, 0])  # 黄色
                    test_edge.split_timber.status = 1  # 黄色
                    print("Green")

        # split structure1 or split structure2のいずれも静定もしくは不静定である場合
        # test edgeが破壊されても、不安定な構造体が生成されないので、冗長性があると判定する
        elif degree_of_stability == 2:
            # master structureが不安定である場合
            if self.status == 0:
                # About master timber
                rs.ObjectColor(test_edge.timber.surface_guid, [0, 0, 0])  # default color

                # About split timber
                rs.ObjectColor(test_edge.split_timber.surface_guid, [223, 51, 78])  # 赤色
                test_edge.split_timber.status = 0  # 赤色

            # master structureが安定構造である場合
            elif self.status == 1 or self.status == 2:
                # Todo test edgeが保持するmaster timberの構造状態を確認する
                # 01. この時、split structure1, 2がいずれも安定構造ではあるが、部材単体を見ると不安定である場合
                # test.edge.split timberは赤色 or 黄色になる

                # pattern1 -> test edge上のある点でsplitすることで生成されるsplit timberが1つの接合点しか持たない場合
                # # Calculate uv parameter about timber surface
                # rc, u_parameter, v_parameter = Surface.ClosestPoint(timber_srf, test_point)

                # Split timber surface
                # split_srf_list = timber_srf.Split(0, u_parameter)
                #
                # 02. 部材単体も安定である場合
                # test.edge.split timberは青色 -> 冗長性があるedgeとしてみなす
                # About master timber

                # About split timber
                rs.ObjectColor(test_edge.split_timber.surface_guid, [157, 204, 255])  # 青色
                test_edge.split_timber.status = 2  # 青色

    # 部材の色分けを行う(全体の判定)
    def color_code_timbers(self):

        # edgeを主構造体とサブ構造体に振り分ける
        main_structure_edges, sub_structure_edges = self.regard_test_edge_as_main_structure_or_sub_structure()

        # main, sub edgesをインスタンス変数として保存しておく
        self.set_main_sub_edges(main_structure_edges, sub_structure_edges)

        # 主構造体を構成するedgeの冗長性を判定し、色分けを行う
        self.judge_redundancy_of_test_timber(main_structure_edges, "main")

        # サブ構造体を構成するedgeの冗長性を判定し、色分けを行う
        for sub_edges in sub_structure_edges:
            self.judge_redundancy_of_test_timber(sub_edges, "sub")

        # Todo ここでOpenSeasの構造解析を行う？
        # command = "-_Grasshopper _E _S _D _O \"{0}\" _Enter"
        # location = "G:\\マイドライブ\\2020\\04_Master\\2006_Generation-algorithm\\StructualAnalysis\\201208\\5timbers\\timbers.gh"
        # everything = command.format(location)
        # rs.Command(everything)

    def split_master_edge(self, layer=None):

        for main_edge in self.main_edges:
            split_edges = main_edge.divide_edge_two_edge()
            for split_edge in split_edges:
                edge_guid = scriptcontext.doc.Objects.AddCurve(split_edge)

                # set layer
                rs.ObjectLayer(edge_guid, layer)

                # user textの設定を行う
                rs.SetUserText(edge_guid, "joint", "3")  # joint
                rs.SetUserText(edge_guid, "sec", str(main_edge.section_id))  # section id

    # 主構造体とサブ構造体に分割する
    def regard_test_edge_as_main_structure_or_sub_structure(self):

        main_structure_edges = []
        sub_structure_edges = []

        # 削除等を行うため、edge群を複製しておく
        test_edges = copy.copy(self.edges)

        for test_edge in test_edges:

            # edgeのいずれかの端部が自由端である場合->サブ構造体とみなす
            if test_edge.start_node.structural_type == 0 or test_edge.end_node.structural_type == 0:
                sub_structure_edges.append([test_edge])
                continue

            # master structureを分割した構造体1と構造体2の構造判定(main or sub)を格納する
            count_main_structure = 0

            # 探索開始位置
            search_start_nodes = [test_edge.start_node, test_edge.end_node]
            search_start_nodes_id = [test_edge.start_node.id, test_edge.end_node.id]

            for i, search_start_node in enumerate(search_start_nodes):
                stack_list = [search_start_node]  # 探索をしにいくノードを格納しておく
                history_node_list = [search_start_node]  # 訪問済みのノードを格納
                history_node_id_list = [search_start_node.id]  # 訪問済みのノードidを格納

                while stack_list:

                    # stack listの最初のノードを取得する
                    stack_node = stack_list.pop(0)

                    # stack nodeの隣接ノードを調べに行く
                    for connected_node in stack_node.connected_nodes:
                        # 既にhistory listに存在するノード
                        if connected_node.id in history_node_id_list:
                            continue

                        # 逆流禁止
                        if connected_node.id == stack_node.id:
                            continue

                        # test edgeの両端である場合
                        if stack_node.id in search_start_nodes_id and connected_node.id in search_start_nodes_id:
                            continue

                        # stack listにノードを追加
                        stack_list.append(connected_node)

                        # history listにノードを追加
                        history_node_list.append(connected_node)
                        history_node_id_list.append(connected_node.id)

                # 構造体1、構造体2が主構造かサブ構造かどうかを支点の数で判定する
                is_main_structure = False
                edge_list = []

                for node in history_node_list:
                    if node.structural_type == 1:  # 支点
                        is_main_structure = True
                        break

                if is_main_structure:
                    count_main_structure += 1
                else:
                    for node in history_node_list:
                        if node.structural_type == 2:  # 接合点
                            # edge情報を取得
                            for having_edge in node.having_edges:
                                if having_edge in edge_list:
                                    continue
                                else:
                                    # having edgeの始点、終点のいずれもがtest edgeの両端と同一な場合
                                    if having_edge.start_node.id in search_start_nodes_id and having_edge.end_node.id in search_start_nodes_id:
                                        continue

                                    # 上記に該当しない場合、edge listにhaving edgeを格納
                                    edge_list.append(having_edge)

                    # 取得したedgeはtest_edgesから削除する
                    for edge in edge_list:
                        # test edges
                        if edge in test_edges:
                            test_edges.remove(edge)

                        # main structure edges
                        if edge in main_structure_edges:
                            main_structure_edges.remove(edge)

                        # sub structure edges
                        for index, sub_edges in enumerate(sub_structure_edges):
                            if edge in sub_edges:
                                del sub_structure_edges[index]

                    # サブ構造体としてedge list情報を保持する
                    edge_list.append(test_edge)  # test edgeはサブ構造体に含まれる
                    sub_structure_edges.append(edge_list)

            # count main structureからtest edgeが主構造、サブ構造どちらに属するのかを判定する
            if count_main_structure == 2:
                main_structure_edges.append(test_edge)

        return main_structure_edges, sub_structure_edges

    # 部材単体の構造安定度を判定する
    @staticmethod
    def judge_stability_of_timber(test_edge):
        """
        :param test_edge:
        :return: stability of timber -> -1: exception  0: instability 1: stability
        """

        end_nodes = []
        end_nodes_id = []

        # p1. test edge両端のノードが接合部の場合、次の処理に進む
        # p2. test edgeの一端が接合点、もう一端が支点の場合、次の処理に進む
        flag = False
        if test_edge.start_node.structural_type == 2 or test_edge.start_node.structural_type == 1:
            end_nodes.append(test_edge.start_node)
            end_nodes_id.append(test_edge.start_node.id)

            if test_edge.end_node.structural_type == 2 or test_edge.start_node.structural_type == 1:
                end_nodes.append(test_edge.end_node)
                end_nodes_id.append(test_edge.end_node.id)
                flag = True

        if not flag:  # test edgeは黄色の部材？
            return 0
        else:
            return 1

        # self_timber = test_edge.timber  # test edgeが所属するTimber instance
        #
        # # 1つずつtest edgeの端部ノードを取り出す
        # for end_node in end_nodes:
        #     count_joint_pts = 0
        #
        #     # end node is joint pt, so count as a joint point
        #     count_joint_pts += 1
        #
        #     # Todo 切断点を塑性ヒンジとして考える -> これがある時点で全て安定とみなされる
        #     count_joint_pts += 1
        #
        #     # 端部ノード(接合点)が接続する隣接ノードを調べる
        #     for connected_node in end_node.connected_nodes:
        #
        #         # 隣接点がtest edgeのいずれかである場合
        #         if connected_node.id in end_nodes_id:
        #             continue
        #
        #         for joint_pt_node in self_timber.joint_pts_nodes:
        #             # 接合点である場合
        #             if connected_node.id == joint_pt_node.id:
        #                 count_joint_pts += 1
        #
        #         # 支点である場合
        #         if connected_node.structural_type == 1:
        #             count_joint_pts += 1
        #
        #     # もしある部材が接合点を1つ以下しか持っていない場合、不安定とみなす
        #     if count_joint_pts <= 1:
        #         return 0
        #
        # # 上記の判定に合致しない場合は安定とみなす
        # return 1
