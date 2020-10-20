# coding: utf-8

import copy
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
        # Print information
        print("###{0}###".format(i + 1))
        print("n: {0}".format(self.n))
        print("s: {0}".format(self.s))
        print("r: {0}".format(self.r))
        print("k: {0}".format(self.k))
        print("m: {0}".format(self.m))

        # 構造体の判定を行う
        # TODO 基本はmの値で判定を行うが、支点反力数の値が0~2の時はいくらmの値が大きくても不安定とみなす？
        if self.m < 0:
            print("不安定")
            self.status = 0  # 不安定
        elif self.m == 0:
            print("静定")
            self.status = 1  # 静定
        else:
            print("不静定")
            self.status = 2  # 不静定

        print("")

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
    def judge_redundancy_of_test_timber(self):

        # すべてのEdgeに対して同じ判定処理を行う  Todo 部材数が多くなるにつれ、処理時間が長くなるのでアルゴリズムは要検討
        for edge in self.edges:

            # 判定を行うEdge
            test_edge = edge
            print("###edge {0}###".format(test_edge.id))

            # 探索開始位置
            search_start_nodes = [test_edge.start_node, test_edge.end_node]
            search_start_nodes_id = [test_edge.start_node.id, test_edge.end_node.id]

            # 不静定次数を格納するリスト
            m_list = []

            for i, search_start_node in enumerate(search_start_nodes):
                stack_list = [search_start_node]
                history_node_list = [search_start_node]  # history listに search start nodeを格納
                history_node_is_list = [search_start_node.id]  # node idを格納。判定に利用する

                while stack_list:
                    # print("stack list: {0}".format(len(stack_list)))

                    # stack listの最初のノードを取得する
                    stack_node = stack_list.pop(0)

                    for connected_node in stack_node.connected_nodes:
                        # 既にhistory listに存在するノード
                        if connected_node.id in history_node_is_list:
                            continue

                        # 逆流禁止
                        if connected_node.id == stack_node.id:
                            continue

                        #
                        if stack_node.id in search_start_nodes_id and connected_node.id in search_start_nodes_id:
                            continue

                        # # test edgeの両端である場合
                        # if connected_node.id == search_start_nodes[0].id or connected_node.id == search_start_nodes[1].id:
                        #     continue

                        # stack listにノードを追加
                        stack_list.append(connected_node)

                        # history listにノードを追加
                        history_node_list.append(connected_node)
                        history_node_is_list.append(connected_node.id)

                # print("history node: {0}".format(len(history_node_list)))
                # for node in history_node_list:
                #     print(node.id)
                #
                # print("")

                # 構造判定式を用いてmの値を求める
                n = 0  # Todo test edgeの端点のいずれかが支点である場合はここも変わる？

                count = 0
                # sの数はtest edgeの種類によって異なる
                for search_node_id in search_start_nodes_id:
                    if search_node_id in history_node_is_list:
                        count += 1

                # test edgeを1つの部材としてカウントするため -> 以下のhaving edgeでカウントされる？
                if count == 2:
                    s = 2
                    k = 2  # test edgeの両端(2点)を自由端の節点としてカウントする
                elif count == 1:
                    s = 1
                    k = 1  # test edgeの一端(1点)を自由端の節点としてカウントする
                else:
                    s = 0
                    k = 0

                r = 0
                num_bolts = 0
                edge_list = []

                for node in history_node_list:
                    if node.structural_type == 0:  # 自由端
                        k += 1  # 節点

                    elif node.structural_type == 1:  # 支点
                        n += 2  # 支点は反力数2
                        k += 1  # 節点

                    elif node.structural_type == 2:  # 接合点
                        num_bolts += 1  # 1つの接合点には1つのボルトが存在。のちに部材数(s)、節点数(k)としてカウント
                        r += 3  # 1つの接合点はrの値が3としてカウント

                        # 構造体のedge情報を取得
                        for having_edge in node.having_edges:
                            if having_edge in edge_list:
                                continue
                            else:
                                # having edgeの始点、終点のいずれもがtest edgeの両端と同一な場合
                                if having_edge.start_node.id in search_start_nodes_id and having_edge.end_node.id in search_start_nodes_id:
                                    continue
                                else:
                                    edge_list.append(having_edge)

                                # if i == 0:
                                #     check_node = search_start_nodes[1]
                                # else:
                                #     check_node = search_start_nodes[0]
                                #
                                # if having_edge.start_node.id == check_node.id or having_edge.end_node.id == check_node.id:
                                #     continue
                                # else:
                                #     edge_list.append(having_edge)

                # 部材数(s)
                s += len(edge_list) + num_bolts  # ボルトも部材数としてカウント

                # 節点(k)
                k += num_bolts * 2  # 接合点 = ボルトの両端部(2点)を節点としてカウント

                # 不静定次数(m)
                m = (n + s + r) - (2 * k)

                # TODO 基本はmの値で判定を行うが、支点反力数の値が0~2の時はいくらmの値が大きくても不安定とみなす？
                if n <= 2:
                    m = -1
                
                m_list.append(m)

                print("n: {0}".format(n))
                print("s: {0}".format(s))
                print("r: {0}".format(r))
                print("k: {0}".format(k))
                print("m: {0}".format(m))

            # m listからtest edgeの色を判定する
            degree_of_stability = 0
            # degree_of_instability = 0

            for m in m_list:
                if m < 0:  # 不安定
                    # degree_of_instability += 1
                    pass
                elif m == 0:  # 静定
                    degree_of_stability += 1
                    pass
                else:  # 不静定
                    degree_of_stability += 1
                    pass

            print("degree_of_stability: {0}".format(degree_of_stability))

            """Color code edge split timber"""
            # master timberが1つの接合点しか持たない + 地面に設置していない場合、その部材は赤色
            if len(test_edge.timber.joint_pts_nodes) <= 1 and (not test_edge.timber.is_generated_from_GL):
                # test.edge.split timberは赤色
                # About master timber

                # About split timber
                rs.ObjectColor(test_edge.split_timber.surface_guid, [223, 51, 78])  # 赤色
                test_edge.split_timber.status = 0  # 赤色
                continue

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
                    rs.ObjectColor(test_edge.split_timber.surface_guid, [225, 225, 0])  # 黄色
                    test_edge.split_timber.status = 1  # 黄色

            # split structure1 or split structure2のいずれも静定もしくは不静定である場合
            # test edgeが破壊されても、不安定な構造体が生成されないので、冗長性があると判定する
            elif degree_of_stability == 2:
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

        rs.EnableRedraw(False)

        self.judge_redundancy_of_test_timber()

        rs.EnableRedraw(True)
