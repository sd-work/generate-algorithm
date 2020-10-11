# coding: utf-8

import rhinoscriptsyntax as rs
import random
import csv
import os
import clr
import sys

# sys.path.append(r'C:\Program Files\IronPython 2.7')
# sys.path.append(r'C:\Program Files\IronPython 2.7\DLLs')
# sys.path.append(r'C:\Program Files\IronPython 2.7\Lib')
# sys.path.append(r'C:\Program Files\IronPython 2.7\Lib\site-packages')

# clr.AddReference('System')

import scriptcontext
import rhinoscript.utility
import Rhino
from Rhino.Geometry import *
from Rhino.DocObjects import *
from optiimization import *


class Timber:

    def __init__(self, id, length=None, path_to_csv=None, parent_layer=None):
        self.id = id  # Timber id
        self.master_timber = None
        if length is None:
            self.length = None
        else:
            self.length = float(length)
        self.path_to_csv = path_to_csv  # Timber情報が格納されたディレクトリまでのパス
        self.generate_pattern = None  # ???
        self.is_used = False  # 生成済みかどうかの判定フラグ
        self.joint_pts_info = []  # 接合点情報

        # Object(RhinoCommon)
        self.center_line = None  # 中心線
        self.surface_breps = None  # TimberのB-rep  # TODO これがないとIntersectionコマンドが使えない->Surfaceに統一したい
        self.surface = None  # Timberのサーフェス
        self.split_timbers = []  # Timber Surfaceを分割したsplit timber instance群

        # Guid(In doc)
        self.text_dot_id = None
        self.center_line_guid = None
        self.surface_guid = None

        # Layer
        self.parent_layer = parent_layer
        self.timber_layer = None
        self.surface_layer = None
        self.text_id_layer = None
        self.center_line_layer = None
        self.split_timbers_layer = None

        # Graph
        self.nodes = []  # Timberが保持するノード情報
        self.edges = []  # Timberが保持するエッジ情報
        self.joint_pts_nodes = []  # Timberが保持する接合点におけるノード情報を格納
        self.is_generated_from_GL = False  # TimberがGLから生成されているかを判定するフラグ
        self.rigid_joints = []  # Timberが保持する仮想剛接合点(三角形=virtual node)情報
        self.connected_timbers = []  # Timberが接続している木材情報
        self.status = -1  # -1/ init 0/red 1/yellow 2/blue

        # temp parameter
        self.section_curves_info = []
        self.center_points = []
        self.section_curves = []  # 断面曲線のリスト
        self.intersection_curve = None  # 他の部材と接合する位置
        self.target_line = None

    # 断面曲面から仮想の木材データを生成する
    def generate_timber_info(self, timber_length):
        # 中心線を構成する中心点群を生成
        split_num = 50
        unit_center_point_z = abs(timber_length / split_num)

        for i in range(split_num):
            section_curves_info = [random.randint(-5, 5), random.randint(-5, 5), i * unit_center_point_z]  # 中心点
            radius_section_crv = random.randint(30, 40)  # 半径
            section_curves_info.append(radius_section_crv)
            self.section_curves_info.append(section_curves_info)

        # 点群から中心線を生成
        start = Rhino.Geometry.Point3d(self.section_curves_info[0][0], self.section_curves_info[0][1],
                                       self.section_curves_info[0][2])
        end = Rhino.Geometry.Point3d(self.section_curves_info[-1][0], self.section_curves_info[-1][1],
                                     self.section_curves_info[-1][2])
        self.length = start.DistanceTo(end)

    # モデル空間上にあるオブジェクトを3dmファイルに書き出す TODO 指定したオブジェクトのみを書き出すようにする
    @staticmethod
    def save_as_rhino_file(name="Default.3dm"):
        filename = name
        master_folder = 'G:\\マイドライブ\\2020\\04_Master\\2006_Generation-algorithm\\RhinoModel\\timbers\\'
        path = os.path.abspath(master_folder + filename + ".3dm")
        cmd = "_-SaveAs " + chr(34) + path + chr(34)
        rs.Command(cmd, True)

    def export_csv_file(self, name):
        master_folder = 'G:\\マイドライブ\\2020\\04_Master\\2006_Generation-algorithm\\RhinoModel\\timbers\\'
        timber_folder = os.path.join(master_folder, name)

        if os.path.exists(timber_folder):
            pass
        else:
            os.mkdir(timber_folder)  # 各木材のディレクトリを作成

        self.path_to_csv = os.path.join(timber_folder, (name + ".csv"))

        with open(self.path_to_csv, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(self.section_curves_info)  # center points

    def create_timber_layer(self):
        self.timber_layer = rs.AddLayer(self.id, [0, 0, 0], True, False, self.parent_layer)

        self.center_line_layer = rs.AddLayer("center line", [0, 0, 0], True, False, self.timber_layer)
        self.surface_layer = rs.AddLayer("surface", [0, 0, 0], True, False, self.timber_layer)
        self.text_id_layer = rs.AddLayer("text id", [0, 0, 0], True, False, self.timber_layer)

        self.split_timbers_layer = rs.AddLayer("split timber", [0, 0, 0], True, False, self.timber_layer)

    def generate_timber(self):
        # layerを作成
        self.create_timber_layer()

        # csvファイルから木材の情報を取得し、変数に代入する
        with open(self.path_to_csv, "r") as csv_file:
            reader = csv.reader(csv_file)
            self.section_curves_info = [section_crv_info for section_crv_info in reader]

        # 断面曲線情報から木材のRhinoモデルを生成
        for crv_info in self.section_curves_info:
            point = Rhino.Geometry.Point3d(float(crv_info[0]), float(crv_info[1]), float(crv_info[2]))
            section_curve = NurbsCurve.CreateFromCircle(Rhino.Geometry.Circle(point, float(crv_info[3])))
            self.center_points.append(point)
            self.section_curves.append(section_curve)

        self.center_line = Rhino.Geometry.Polyline(self.center_points)

        self.surface_breps = Rhino.Geometry.Brep.CreateFromLoft(self.section_curves, Point3d.Unset, Point3d.Unset,
                                                                LoftType.Loose,
                                                                False)
        surfaces = self.surface_breps[0].Surfaces
        self.surface = surfaces[0]

        # Rhinoモデル空間に更新内容を反映させる→TODO ここは最終的には最後に描画するようにする
        # 中心線
        self.center_line_guid = scriptcontext.doc.Objects.AddPolyline(self.center_points)
        rs.ObjectLayer(self.center_line_guid, self.center_line_layer)

        # サーフェス
        srf_guid = scriptcontext.doc.Objects.AddSurface(self.surface)
        rs.ObjectLayer(srf_guid, self.surface_layer)
        self.surface_guid = srf_guid

        # dot text
        self.text_dot_id = scriptcontext.doc.Objects.AddTextDot(self.id, self.center_line.PointAt(0))
        rs.ObjectLayer(self.text_dot_id, self.text_id_layer)

        # 木材を使用済みにする
        self.is_used = True

    # timberを移動させる
    def translate_timber(self, origin_p, transform_p):
        xf = Rhino.Geometry.Transform.Translation(transform_p - origin_p)  # 変位

        '''プログラム上の変数をここで更新。ここ重要'''
        self.center_line.Transform(xf)
        self.surface.Transform(xf)
        for srf in self.surface_breps:
            srf.Transform(xf)

        # モデル空間に更新内容を反映させる→TODO ここは最終的には最後に描画するようにする
        scriptcontext.doc.Objects.Transform(self.center_line_guid, xf, True)  # 中心線
        scriptcontext.doc.Objects.Transform(self.surface_guid, xf, True)  # 表面サーフェス

        if self.text_dot_id:
            scriptcontext.doc.Objects.Transform(self.text_dot_id, xf, True)  # dot text

    # timberを回転させる
    def rotate_timber(self, angle, axis, rotation_center):
        xf = Transform.Rotation(angle, axis, rotation_center)  # 変位

        ''' 01. プログラム(Rhino common)上の変数をここで更新。ここ重要'''
        self.center_line.Transform(xf)  # 中心線

        self.surface.Transform(xf)
        for srf in self.surface_breps:  # 表面サーフェス
            srf.Transform(xf)

        # 02. モデル空間に更新内容を反映させる→TODO ここは最終的には最後に描画するようにする
        scriptcontext.doc.Objects.Transform(self.center_line_guid, xf, True)  # 中心線
        scriptcontext.doc.Objects.Transform(self.surface_guid, xf, True)  # 表面サーフェス
        if self.text_dot_id:
            scriptcontext.doc.Objects.Transform(self.text_dot_id, xf, True)  # dot text

    # Rhinoモデル空間上にあるオブジェクトを回転させる
    def rotate_timber_in_program(self, angle, axis, rotation_center):

        xf = Transform.Rotation(angle, axis, rotation_center)  # 変位

        '''プログラム上の変数をここで更新'''
        self.center_line.Transform(xf)  # 中心線

        self.surface.Transform(xf)
        for srf in self.surface_breps:  # 表面サーフェス
            srf.Transform(xf)

    # 接する面積を最小化する(1つの接合点を処理する)
    def minimized_joint_area(self, other_timber, joint_point, unit_move_vec):

        # optimization parameter
        tolerance = 40
        previous_curve_length_list = 1000
        is_vec_reverse = False

        for i in range(200):
            intersect_info = Intersect.Intersection.BrepBrep(self.surface_breps[0], other_timber.surface_breps[0], 0.01)

            ### 木材間で接触がなかった場合 ###
            if len(intersect_info[1]) == 0:
                if i == 0:
                    origin_pt, transform_pt = Optimization.get_move_vector(joint_point, self.surface_breps[0],
                                                                           other_timber.surface_breps[0])

                    self.translate_timber(origin_pt, transform_pt)
                    continue

                intersection_crv_length = None

                if not is_vec_reverse:
                    unit_move_vec.Reverse()
                    is_vec_reverse = True

            #### 木材間で接触があった場合 ###
            else:
                intersection_curve = intersect_info[1][0]
                intersection_crv_length = intersection_curve.GetLength()

                # reverse move vector
                if previous_curve_length_list < intersection_crv_length:
                    is_vec_reverse = True

                if is_vec_reverse:
                    unit_move_vec.Reverse()
                    is_vec_reverse = False

            # update parameter
            previous_curve_length_list = intersection_crv_length

            # 交差曲線の長さが許容値(tolerance)より短い場合
            if 0 < intersection_crv_length < tolerance:
                # print("Final intersection curve length: {0}".format(intersection_crv_length))

                joint_pt = Optimization.get_mid_pt_in_closed_crv(intersect_info[1][0])

                ### debug ###
                # if intersect_info[1]:
                #     scriptcontext.doc.Objects.AddCurve(intersect_info[1][0])

                return intersection_crv_length, joint_pt
            else:
                new_move_vec = Optimization.get_proper_move_vector(unit_move_vec, intersection_crv_length, joint_point)
                transform_p = Point3d(new_move_vec.X, new_move_vec.Y, new_move_vec.Z)
                self.translate_timber(joint_point, transform_p)

            if i == 199:
                print("Optimization has failed")
                return False

    # 接する面積を最小化する(2つの接合点を同時に処理する)
    def bridge_joint_area(self, joint_pts_info):
        """
        :param joint_pts_info:  [[joint_id, joint point, cross_vector, self timber, other timber, +rotation center]]
        :return:
        """

        # rotation center
        for i, joint_pt_info in enumerate(joint_pts_info):
            vec_length = 1000
            unit_vec = joint_pt_info[2]
            trans_vec = Vector3d(unit_vec.X * vec_length, unit_vec.Y * vec_length, unit_vec.Z * vec_length)
            trans_vec = Vector3d.Add(Vector3d(joint_pt_info[1]), trans_vec)
            line = LineCurve(joint_pt_info[1], Point3d(trans_vec.X, trans_vec.Y, trans_vec.Z))
            intersect_info = Intersect.Intersection.CurveBrep(line, joint_pts_info[i][4].surface_breps[0], 0.001)
            joint_pts_info[i].append(intersect_info[2][0])

        # optimization parameter
        previous_curve_length_move_list = [1000, 1000]
        previous_curve_length_rotate_list = [1000, 1000]
        is_first_rotate = True

        # TODO 無くても良い？ 200728
        rotation_direction_list = [1, -1]

        # main process
        for i in range(200):
            intersect_info_list = []

            # 接合部1,2の交差曲線を取得
            for joint_pt_info in joint_pts_info:
                other_timber = joint_pt_info[4]
                intersect_info = Intersect.Intersection.BrepBrep(self.surface_breps[0], other_timber.surface_breps[0],
                                                                 0.01)
                intersect_info_list.append(intersect_info)

            # 部材同士の関係性(交差曲線)から、処理方法を選択する
            pattern_info, curve_length_list = Optimization.get_pattern_of_processing_method(intersect_info_list)

            if pattern_info[0] == 2:
                print("Optimization has been successful")

                joint_pt1 = Optimization.get_mid_pt_in_closed_crv(intersect_info_list[0][1][0])
                joint_pt2 = Optimization.get_mid_pt_in_closed_crv(intersect_info_list[1][1][0])

                return [joint_pt1, joint_pt2]

            # 選択した木材の情報
            index = pattern_info[1]

            #### debug ####
            # if pattern_info[0] == 0:
            #     print("previous_move: {0}".format(previous_curve_length_move_list))
            # else:
            #     print("previous_rotate: {0}".format(previous_curve_length_rotate_list))
            # print("now: {0}".format(curve_length_list))
            #### ----- ####

            ### move timber ###
            if pattern_info[0] == 0:
                joint_pt_info = joint_pts_info[index]
                joint_pt = joint_pt_info[1]

                # 交差曲線とjoint ptとのベクトルに変更でも良いかも？
                unit_move_vec = joint_pt_info[2]

                other_timber = joint_pt_info[4]

                crv_length = self.minimized_joint_area(other_timber, joint_pt, unit_move_vec)

                previous_curve_length_move_list[index] = crv_length[0]

            #### rotate timber ###
            elif pattern_info[0] == 1:

                tolerance_diff = 10

                # if condition is satisfied, change rotate direction
                if index == 0:
                    if previous_curve_length_rotate_list[1] and curve_length_list[1] is None:
                        if rotation_direction_list[index] == -1:
                            rotation_direction_list[index] = 1
                        else:
                            rotation_direction_list[index] = -1

                    elif previous_curve_length_rotate_list[1] is None and curve_length_list[1]:
                        if rotation_direction_list[index] == -1:
                            rotation_direction_list[index] = 1
                        else:
                            rotation_direction_list[index] = -1

                    elif previous_curve_length_rotate_list[1] is None and curve_length_list[1] is None:
                        pass

                    elif previous_curve_length_rotate_list[1] < curve_length_list[1] - tolerance_diff:
                        if rotation_direction_list[index] == -1:
                            rotation_direction_list[index] = 1
                        else:
                            rotation_direction_list[index] = -1

                    # update parameter
                    previous_curve_length_rotate_list[1] = curve_length_list[1]

                elif index == 1:
                    if previous_curve_length_rotate_list[0] and curve_length_list[0] is None:
                        if rotation_direction_list[index] == -1:
                            rotation_direction_list[index] = 1
                        else:
                            rotation_direction_list[index] = -1

                    elif previous_curve_length_rotate_list[0] is None and curve_length_list[0]:
                        if rotation_direction_list[index] == -1:
                            rotation_direction_list[index] = 1
                        else:
                            rotation_direction_list[index] = -1

                    elif previous_curve_length_rotate_list[0] is None and curve_length_list[0] is None:
                        pass

                    elif previous_curve_length_rotate_list[0] < curve_length_list[0] - tolerance_diff:
                        if rotation_direction_list[index] == -1:
                            rotation_direction_list[index] = 1
                        else:
                            rotation_direction_list[index] = -1

                    # update parameter
                    previous_curve_length_rotate_list[0] = curve_length_list[0]

                # rotate angle
                if is_first_rotate:
                    rotation_direction_list[index], radian = Optimization.get_rotate_direction(index,
                                                                                               joint_pts_info,
                                                                                               curve_length_list,
                                                                                               intersect_info_list)
                    is_first_rotate = False

                else:
                    if index == 0:
                        radian = Optimization.get_proper_rotate_angle(curve_length_list[1])
                    else:
                        radian = Optimization.get_proper_rotate_angle(curve_length_list[0])

                radian = radian * rotation_direction_list[index]
                # print(radian)

                rotation_center = Optimization.get_mid_pt_in_closed_crv(intersect_info_list[index][1][0])
                axis = Vector3d(rotation_center - joint_pts_info[index][1])

                self.rotate_timber(radian, axis, rotation_center)

            ### debug ###
            # if intersect_info_list[0][1]:
            #     scriptcontext.doc.Objects.AddCurve(intersect_info_list[0][1][0])
            # if intersect_info_list[1][1]:
            #     scriptcontext.doc.Objects.AddCurve(intersect_info_list[1][1][0])
            ### debug ###

            if i == 199:
                print("Optimization has failed")
                return False

            # print("")

    def move_timber(self, other_timber, joint_point, move_vec):

        # minimized_joint_area --> optimization
        unit_move_vec = Vector3d(move_vec.X / move_vec.Length, move_vec.Y / move_vec.Length,
                                 move_vec.Z / move_vec.Length)

        tolerance = 40
        previous_curve_length_list = 1000
        is_vec_reverse = False
        for i in range(100):
            # Intersects a timber surface with other timber surface
            intersect_info = Intersect.Intersection.BrepBrep(self.surface_breps[0], other_timber.surface_breps[0], 0.01)

            # 木材間で接触がなかった場合
            if len(intersect_info[1]) == 0:
                # TODO バグの原因->動かす方向の設定
                if i == 0:
                    origin_pt, transform_pt = Optimization.get_move_vector(joint_point, self.surface_breps[0],
                                                                           other_timber.surface_breps[0])

                    self.translate_timber(origin_pt, transform_pt)
                    continue

                intersection_crv_length = 50

                if not is_vec_reverse:
                    unit_move_vec.Reverse()
                    is_vec_reverse = True

            # 木材間で接触があった場合
            else:
                intersection_curve = intersect_info[1][0]
                intersection_crv_length = intersection_curve.GetLength()

                # reverse move vector TODO 改良の余地あり
                if previous_curve_length_list < intersection_crv_length:
                    is_vec_reverse = True

                previous_curve_length_list = intersection_crv_length

                if is_vec_reverse:
                    unit_move_vec.Reverse()
                    is_vec_reverse = False

            # 交差曲線の長さが許容値(tolerance)より短い場合
            if intersection_crv_length < tolerance:
                print("final length: {0}".format(intersection_crv_length))
                return
            else:
                new_move_vec = Optimization.get_proper_move_vector(unit_move_vec, intersection_crv_length, joint_point)
                transform_p = Point3d(new_move_vec.X, new_move_vec.Y, new_move_vec.Z)
                self.translate_timber(joint_point, transform_p)

            if i == 99:
                print("Can not be optimization")

    def judge_timber_pattern(self, target_line, generated_timbers):
        """
        始点と終点情報から木材の生成パターンを判定する
        それぞれの点が取れるパターンは①GL②空中③既存のいずれか。パターンの合計は５つに分類される。
        rating:2 -> GL-Gl(pattern 0)
        rating:3 -> GL-空中(pattern 1)
        rating:4 -> GL-既存(pattern 2)
        rating:5 -> 空中-既存(pattern 3)
        rating:6 -> 既存-既存(pattern 4)
        :return:
        """

        rating = 0

        # 始点、終点のパターンを検索し、配点による分類を行う
        temp_pts = [target_line.start_p, target_line.end_p]

        for test_point in temp_pts:
            is_there_joint_pt = False

            # GL判定--> +1
            if test_point.Z == 0:
                rating += 1
                self.is_generated_from_GL = True
                continue

            # 既存の部材に接合しているかの判定--> +3
            for generated_timber in generated_timbers:

                temp_target_curve = generated_timber.center_line.ToPolylineCurve()
                events = Intersect.Intersection.CurveCurve(temp_target_curve, self.target_line.Line, 0.001, 0.0)

                if events:
                    for ccx_event in events:
                        if ccx_event.PointA == test_point:
                            rating += 3
                            is_there_joint_pt = True
                            continue

            # 空中判定--> +2
            if not is_there_joint_pt:
                rating += 2

        # 配点から、部材の生成パターンを判定する
        if rating == 2:
            self.generate_pattern = 0
        elif rating == 3:
            self.generate_pattern = 1
        elif rating == 4:
            self.generate_pattern = 2
        elif rating == 5:
            self.generate_pattern = 3
        elif rating == 6:
            self.generate_pattern = 4
        else:
            print("It's a pattern that can't be classified. ")

    def set_having_edge(self, edges):
        for edge in edges:
            if edge in self.edges:
                continue
            else:
                self.edges.append(edge)
                # edge.timber = self  # TODO これでOK？

    def set_nodes(self, nodes):
        for node in nodes:
            if node in self.nodes:
                continue
            else:
                self.nodes.append(node)

    def set_joint_pt_nodes(self, joint_pt_nodes):
        for joint_pt in joint_pt_nodes:
            if joint_pt in self.joint_pts_nodes:
                continue
            else:
                self.joint_pts_nodes.append(joint_pt)

    def split_timber_surface(self, test_point, timber_instance=None):
        split_timber_instances = []

        # Get closest point on timber surface from test point which is joint point node
        if timber_instance is None:
            timber_srf = self.surface
        else:
            timber_srf = timber_instance.surface

        # Calculate uv parameter about timber surface
        rc, u_parameter, v_parameter = Surface.ClosestPoint(timber_srf, test_point)

        # Split timber surface
        split_srf_list = timber_srf.Split(0, u_parameter)

        # Delete old split timber
        if timber_instance.master_timber:
            # Delete split timber guid from doc
            timber_instance.delete_timber_guid()

            # Remove split timber from instance variable which already generated timber has
            timber_instance.master_timber.split_timbers.remove(timber_instance)

        # Split timber instance
        for split_srf in split_srf_list:
            # 引数に渡されたTimber instanceがMaster Timberである場合
            if timber_instance.master_timber is None:
                split_timber = Timber(timber_instance.id + "-" + str(len(timber_instance.split_timbers)))

                # split timberにmaster timber instance情報を紐づける
                split_timber.master_timber = timber_instance

            # 引数に渡されたTimber instanceがSplit Timberである場合
            else:
                id = timber_instance.master_timber.id + "-" + str(len(timber_instance.master_timber.split_timbers))
                split_timber = Timber(id)

                # split timberにmaster timber instance情報を紐づける
                split_timber.master_timber = self

            # timber surface情報を紐づける
            split_timber.surface = split_srf

            # 色分けのステータスを引き継ぐ
            split_timber.status = timber_instance.status

            # Draw split surface in doc
            split_timber.surface_guid = scriptcontext.doc.Objects.AddSurface(split_srf)  # timber surface guid

            # 生成されるsplit timberが青色の場合はここで色分けを行う
            if split_timber.status == 2:
                rs.ObjectColor(split_timber.surface_guid, [157, 204, 255])  # 青色
            elif split_timber.status == 1:
                rs.ObjectColor(split_timber.surface_guid, [225, 225, 0])  # 黄色

            # レイヤー分け
            temp_layer = rs.AddLayer(split_timber.id, [0, 0, 0], True, False, self.split_timbers_layer)
            rs.ObjectLayer(split_timber.surface_guid, temp_layer)

            # 戻り値として格納する
            split_timber_instances.append(split_timber)

            # Maintain split surface information to instance variable
            # 引数に渡されたTimber instanceがMaster Timberである場合
            if timber_instance.master_timber is None:
                timber_instance.split_timbers.append(split_timber)

            # 引数に渡されたTimber instanceがSplit Timberである場合
            else:
                timber_instance.master_timber.split_timbers.append(split_timber)

        return split_timber_instances

    def old_split_timber_surface(self):
        for joint_pt_node in self.joint_pts_nodes:
            if -50 < joint_pt_node.point.Z < 50:
                continue

            # Get closest point on timber surface from test point which is joint point node
            timber_srf = self.surface
            test_point = joint_pt_node.point

            rc, u_parameter, v_parameter = Surface.ClosestPoint(timber_srf, test_point)

            # Split timber surface
            split_srf_list = timber_srf.Split(0, u_parameter)

            for split_srf in split_srf_list:
                # Draw split surface in doc  TODO Timber instanceに紐づける？
                split_srf_guid = scriptcontext.doc.Objects.AddSurface(split_srf)
                # self.split_timbers_srf_guid.append(split_srf_guid)

                # Maintain split surface information to instance variable
                self.split_timbers.append(split_srf)

                # # split Timber instance -> parent timber id - child(split) timber id
                # split_timber = Timber(self.id + "-" + str(len(self.split_timbers)))
                #
                # split_timber.surface = split_srf  # surface of split timber
                # split_timber.surface_guids += scriptcontext.doc.Objects.AddSurface(split_srf)  # guid of surface

            # --- old version ---
            # # Get closest point on timber surface from test point which is joint point node
            # timber_srf = self.surface  # This is about Timber surface
            # test_point = node.point  # This is about Node point
            #
            # domain_u = timber_srf.Domain(0)  # 高さ方向
            # domain_v = timber_srf.Domain(1)  # 断面方向
            #
            # split_num = 10
            # if domain_v[0] < 0:
            #     unit_domain_v = ((domain_v[1] - domain_v[0]) / split_num) * -1
            # else:
            #     unit_domain_v = (domain_v[1] - domain_v[0]) / split_num
            #
            # rc, u_parameter, v_parameter = Surface.ClosestPoint(timber_srf, test_point)
            # closest_pt_on_timber_srf = timber_srf.PointAt(u_parameter, v_parameter)
            #
            # # Get closest point on center line from test point which is on timber surface
            # closest_pt_on_center_line = Polyline.ClosestPoint(self.center_line, closest_pt_on_timber_srf)
            #
            # # Generate cutter surface
            # pt1 = timber_srf.PointAt(u_parameter, unit_domain_v * 0)
            # pt2 = timber_srf.PointAt(u_parameter, unit_domain_v * 2)
            #
            # vec1 = Vector3d(pt1 - closest_pt_on_center_line)
            # vec2 = Vector3d(pt2 - closest_pt_on_center_line)
            #
            # cross_vec = Vector3d.CrossProduct(vec1, vec2)
            #
            # # define plane by center point and normal vector
            # plane = Plane(closest_pt_on_center_line, cross_vec)
            #
            # # cutter circle surface
            # circle = Rhino.Geometry.Circle(plane, 100)
            # circle = circle.ToNurbsCurve()
            #
            # tolerance = scriptcontext.doc.ModelAbsoluteTolerance
            # cutter_circle_srf = Rhino.Geometry.Brep.CreatePlanarBreps(circle, tolerance)
            #
            # # Split timber surface by cutter surface
            # split_list = timber_srf.Split(0, u_parameter)
            # print(split_list)
            #
            # scriptcontext.doc.Objects.AddSurface(split_list[0])
            #
            # # debug
            # # rc = [scriptcontext.doc.Objects.AddBrep(brep) for brep in cutter_circle_srf]

    def delete_timber_guid(self):
        if self.text_dot_id:
            rs.DeleteObject(self.text_dot_id)

        if self.center_line_guid:
            rs.DeleteObject(self.center_line_guid)

        if self.surface_guid:
            rs.DeleteObject(self.surface_guid)

        self.text_dot_id = None
        self.center_line_guid = None
        self.surface_guid = None

    # 部材の構造的な状態を判定し、色分けをする
    def color_code_timber(self):
        # debug
        # for edge in self.edges:
        #     print(edge.id)
        # print("")
        # for node in self.nodes:
        #     print(node.id)
        # print("")
        # for joint_pt_node in self.joint_pts_nodes:
        #     print(joint_pt_node.id)
        # print("")

        # 1. TimberがGLから生成されている場合
        if self.is_generated_from_GL:

            # 1-1. Timberが剛接点を持たない場合 -> 赤色
            if len(self.rigid_joints) == 0:
                # Master timber
                rs.ObjectColor(self.surface_guid, [223, 51, 78])  # 赤色
                self.status = 0  # 赤色

                # split timber
                for split_timber in self.split_timbers:
                    rs.ObjectColor(split_timber.surface_guid, [223, 51, 78])  # 赤色
                    split_timber.status = 0  # 赤色

            # 1-2. Timberが1つ以上の剛接点を持つ場合
            else:
                # 剛接合点は持つ + それがGLに接地している場合
                for rigid_joint in self.rigid_joints:
                    if rigid_joint.is_on_GL:
                        # Master timber
                        rs.ObjectColor(self.surface_guid, [225, 225, 0])  # 黄色
                        self.status = 1  # 黄色

                        # split timber
                        for split_timber in self.split_timbers:
                            rs.ObjectColor(split_timber.surface_guid, [225, 225, 0])  # 黄色
                            split_timber.status = 1  # 黄色

                        return

                # 1-3. 剛接点は持つが、それらのいずれもGLに接地していない場合
                # Master timber
                rs.ObjectColor(self.surface_guid, [223, 51, 78])  # 赤色
                self.status = 0  # 赤色

                # split timber
                for split_timber in self.split_timbers:
                    rs.ObjectColor(split_timber.surface_guid, [223, 51, 78])  # 赤色
                    split_timber.status = 0  # 赤色

        # 02. TimberがGLから生成されていない場合
        else:
            # 2-1. Timberが1つ以上の剛接点を持つ場合 -> 黄色
            if len(self.rigid_joints) >= 1:
                # Master timber
                rs.ObjectColor(self.surface_guid, [225, 225, 0])  # 黄色
                self.status = 1  # 黄色

                # split timber
                for split_timber in self.split_timbers:
                    rs.ObjectColor(split_timber.surface_guid, [225, 225, 0])  # 黄色
                    split_timber.status = 1  # 黄色

            # 2-2. Timberが剛接点を持たない場合 -> 赤色 or 黄色
            else:
                # TODO Timberが剛接点を持たないが、接合点が２つ以上ある場合に黄色になるパターンが存在する？
                # Timberが保持する接合点が2個以上の場合 -> 黄色
                if len(self.joint_pts_nodes) >= 2:
                    # Master timber
                    rs.ObjectColor(self.surface_guid, [225, 225, 0])  # 黄色
                    self.status = 1  # 黄色

                    # split timber
                    for split_timber in self.split_timbers:
                        rs.ObjectColor(split_timber.surface_guid, [225, 225, 0])  # 黄色
                        split_timber.status = 1  # 黄色

                # Timberが保持する接合点が0個か1個の場合 -> 赤色
                elif len(self.joint_pts_nodes) <= 1:
                    # Master timber
                    rs.ObjectColor(self.surface_guid, [223, 51, 78])  # 赤色
                    self.status = 0  # 赤色

                    # split timber
                    for split_timber in self.split_timbers:
                        rs.ObjectColor(split_timber.surface_guid, [223, 51, 78])  # 赤色
                        split_timber.status = 0  # 赤色
