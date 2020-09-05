# coding: utf-8

import rhinoscriptsyntax as rs
import rhinoscript.utility
import random
import csv
import os
import scriptcontext
import rhinoscript.utility
import Rhino
from Rhino.Geometry import *
from target_line import *


def utilize_vector(vector):
    unit_vector = Vector3d(vector.X / vector.Length, vector.Y / vector.Length, vector.Z / vector.Length)
    return unit_vector


class Optimization:
    def __init__(self):
        pass

    @staticmethod
    def edit_adding_timber_range(target_line, num_of_joint_pt):

        # 部材の端点のいずれかがGLから生成される場合
        if target_line.start_p.Z == 0 or target_line.end_p.Z == 0:
            if target_line.start_p.Z == 0:
                pass
            else:
                temp_p = target_line.start_p
                target_line.start_p = target_line.end_p
                target_line.end_p = temp_p
                target_line.vector = Rhino.Geometry.Vector3d(target_line.end_p - target_line.start_p)

            target_length = target_line.length + random.randint(300, 400)  # 木材の参照長さ

            return target_length, target_line

        # 部材の端点のいずれもGLから生成されない場合
        else:
            if num_of_joint_pt == "1":
                vec1 = Vector3d(target_line.start_p - target_line.mid_p)
                vec2 = Vector3d(target_line.end_p - target_line.start_p)

                unit_vec1 = Vector3d(vec1.X / vec1.Length, vec1.Y / vec1.Length, vec1.Z / vec1.Length)
                unit_vec2 = Vector3d(vec2.X / vec2.Length, vec2.Y / vec2.Length, vec2.Z / vec2.Length)

                vec_length1 = vec1.Length + random.randint(400, 800)
                vec_length2 = vec2.Length + random.randint(0, 300)
            else:
                vec1 = Vector3d(target_line.start_p - target_line.mid_p)
                vec2 = Vector3d(target_line.end_p - target_line.mid_p)

                unit_vec1 = Vector3d(vec1.X / vec1.Length, vec1.Y / vec1.Length, vec1.Z / vec1.Length)
                unit_vec2 = Vector3d(vec2.X / vec2.Length, vec2.Y / vec2.Length, vec2.Z / vec2.Length)

                vec_length1 = vec1.Length + random.randint(300, 700)
                vec_length2 = vec2.Length + random.randint(300, 700)

            new_vec1 = Vector3d(unit_vec1.X * vec_length1, unit_vec1.Y * vec_length1, unit_vec1.Z * vec_length1)
            new_vec2 = Vector3d(unit_vec2.X * vec_length2, unit_vec2.Y * vec_length2, unit_vec2.Z * vec_length2)

            new_vec1 = Vector3d.Add(new_vec1, Vector3d(target_line.mid_p))
            new_vec2 = Vector3d.Add(new_vec2, Vector3d(target_line.mid_p))

            new_target_line = PolylineCurve([Point3d(new_vec1.X, new_vec1.Y, new_vec1.Z),
                                             Point3d(new_vec2.X, new_vec2.Y, new_vec2.Z)])

            target_length = new_target_line.GetLength()  # 木材の参照長さ

            return target_length, TargetLine(None, new_target_line)

    @staticmethod
    def get_best_timber_in_database(timber_list_in_database, target_line):
        target_length = target_line.length
        select_timber = None
        min_diff_length = 10000
        for i, timber in enumerate(timber_list_in_database):
            # TODO ここの処理はいずれはサーバーとのやりとりの中で行う
            if timber.is_used:
                continue

            # ターゲット曲線と木材の長さの差異を計算する
            diff_length = abs(timber.length - target_length)

            if diff_length < min_diff_length:
                select_timber = timber
                min_diff_length = diff_length

        return select_timber

    @staticmethod
    def old_get_order_joint_optimization(num_joint_pts, adding_timbers, joint_pts_info_to_generated):
        """
        :param joint_pts_info_to_generated:
        :param num_joint_pts:
        :param adding_timbers: 追加する木材群
        :return: 各接合点における情報(２次元配列)
                 [joint point, cross_vector, self timber, other timber]
        """

        joint_points_info = []  # 各接合点についての情報を格納しておくリスト

        # なめらかな２個の曲線から構成されるターゲット曲線(折れ曲がった点が1つ)
        if len(adding_timbers) == 2:

            # 接合点の数だけ、最適化の処理を行う
            for i in range(num_joint_pts):

                # 既に生成されている部材に接合する接合点の場合
                if joint_pts_info_to_generated:
                    index = i

                    # 既に生成されている部材に接合する場合
                    for joint_info in joint_pts_info_to_generated:
                        self_timber = joint_info[0]
                        other_timber = joint_info[1]
                        events = Intersect.Intersection.CurveCurve(self_timber.target_line.Line,
                                                                   other_timber.target_line.Line,
                                                                   tolerance=0.001, overlapTolerance=0.0)
                        if events:
                            for event in events:
                                # 部材の接合点を最適化する際に使用する移動ベクトルを取得
                                move_vec = Vector3d(Vector3d.CrossProduct(self_timber.target_line.vector,
                                                                          other_timber.target_line.vector))

                                joint_points_info.append([Point3d(event.PointA), move_vec, self_timber, other_timber])

                        # update index
                        index += 1

                    # adding timbers同士で接合する接合点の場合
                    if index == num_joint_pts - 1:
                        if index == 0:
                            self_timber = adding_timbers[index]
                            other_timber = adding_timbers[index + 1]
                        else:
                            self_timber = adding_timbers[index]
                            other_timber = adding_timbers[0]
                    else:
                        self_timber = adding_timbers[index]
                        other_timber = adding_timbers[index + 1]

                    events = Intersect.Intersection.CurveCurve(self_timber.target_line.Line,
                                                               other_timber.target_line.Line,
                                                               tolerance=0.001, overlapTolerance=0.0)
                    if events:
                        for event in events:
                            # 部材の接合点を最適化する際に使用する移動ベクトルを取得
                            move_vec = Vector3d.CrossProduct(self_timber.target_line.vector,
                                                             other_timber.target_line.vector)

                            joint_points_info.append([Point3d(event.PointA), move_vec, self_timber, other_timber])

                    return joint_points_info

                # 既に生成されている部材に接合しない場合
                else:

                    if i > num_joint_pts - 1:
                        return

                    if i == num_joint_pts - 1:
                        if i == 0:
                            self_timber = adding_timbers[i]
                            other_timber = adding_timbers[i + 1]
                        else:
                            self_timber = adding_timbers[i]
                            other_timber = adding_timbers[0]
                    else:
                        self_timber = adding_timbers[i]
                        other_timber = adding_timbers[i + 1]

                    events = Intersect.Intersection.CurveCurve(self_timber.target_line.Line,
                                                               other_timber.target_line.Line,
                                                               tolerance=0.001, overlapTolerance=0.0)

                    if events:
                        for event in events:
                            # 部材の接合点を最適化する際に使用する移動ベクトルを取得
                            move_vec = Vector3d.CrossProduct(self_timber.target_line.vector,
                                                             other_timber.target_line.vector)

                            joint_points_info.append([Point3d(event.PointA), move_vec, self_timber, other_timber])

                return joint_points_info



        # なめらかな3個の曲線から構成されるターゲット曲線(折れ曲がった点が2つ)
        elif len(adding_timbers) == 3:

            # 接合点を計算し、取得する
            for i in range(len(adding_timbers)):
                if i == len(adding_timbers) - 1:
                    events = Intersect.Intersection.CurveCurve(adding_timbers[i].target_line.Line,
                                                               adding_timbers[0].target_line.Line,
                                                               tolerance=0.001,
                                                               overlapTolerance=0.0)
                else:
                    events = Intersect.Intersection.CurveCurve(adding_timbers[i].target_line.Line,
                                                               adding_timbers[i + 1].target_line.Line,
                                                               tolerance=0.001,
                                                               overlapTolerance=0.0)

                # 交点がある場合は交点を取得し、リストに格納する
                if events:
                    for event in events:
                        if i == len(adding_timbers) - 1:
                            joint_point_info = [Point3d(event.PointA), adding_timbers[i], adding_timbers[0]]
                        else:
                            joint_point_info = [Point3d(event.PointA), adding_timbers[i], adding_timbers[i + 1]]

                        # 接合点における情報をリストに格納
                        joint_points_info.append(joint_point_info)

            # 部材の接合点を最適化する際に使用する移動ベクトルを取得
            for joint_point_info in joint_points_info:
                # 外積計算よりベクトルを計算
                move_vec = Vector3d(Vector3d.CrossProduct(joint_point_info[1].target_line.vector,
                                                          joint_point_info[2].target_line.vector))

                # 接合部情報のリストにベクトル情報を格納
                joint_point_info.insert(1, move_vec)

            return joint_points_info

    @staticmethod
    def get_proper_move_vector(unit_vec, intersection_crv_length, origin_pt):

        # オフセットする大きさ(Vector Length)を更新する
        if intersection_crv_length is None:
            vec_length = random.random()  # TODO 値調整
        elif intersection_crv_length <= 42:
            vec_length = random.uniform(0.1, 0.3)
        elif intersection_crv_length <= 50:
            vec_length = random.random()
        elif intersection_crv_length <= 60:
            vec_length = random.uniform(1, 2)
        elif intersection_crv_length <= 80:
            vec_length = random.uniform(2, 3)
        elif intersection_crv_length <= 100:
            vec_length = random.uniform(3, 4)
        elif intersection_crv_length <= 120:
            vec_length = random.uniform(4, 5)
        elif intersection_crv_length <= 200:
            vec_length = random.uniform(8, 10)
        elif intersection_crv_length <= 300:
            vec_length = random.uniform(10, 20)
        else:
            vec_length = random.uniform(20, 40)

        # translate vector
        new_move_vec = Vector3d(unit_vec.X * vec_length, unit_vec.Y * vec_length, unit_vec.Z * vec_length)
        new_move_vec = Vector3d.Add(new_move_vec, Vector3d(origin_pt))

        return new_move_vec

    @staticmethod
    def get_proper_rotate_angle(intersection_crv_length):

        # 交差曲線の長さに応じた回転角度を取得する
        if intersection_crv_length is None:
            angle = random.uniform(0.1, 0.2)  # TODO 値調整
        elif intersection_crv_length <= 50:
            angle = random.uniform(0.005, 0.01)
        elif intersection_crv_length <= 60:
            angle = random.uniform(0.01, 0.03)
        elif intersection_crv_length <= 80:
            angle = random.uniform(0.03, 0.06)
        elif intersection_crv_length <= 100:
            angle = random.uniform(0.06, 0.09)
        elif intersection_crv_length <= 200:
            angle = random.uniform(0.1, 0.3)
        elif intersection_crv_length <= 300:
            angle = random.uniform(0.5, 1)
        else:
            angle = random.uniform(1, 3)

        radian = (angle * math.pi) / 180

        return radian

    @staticmethod
    def get_rotate_direction(index, joint_pts_info, curve_length_list, intersect_info_list):

        if index == 0:
            joint_pt_info = joint_pts_info[1]
            joint_pt = joint_pt_info[1]
            self_timber = joint_pt_info[3]
            other_timber = joint_pt_info[4]
            radian = Optimization.get_first_rotate_angle(joint_pts_info, 1, curve_length_list[1])

        else:
            joint_pt_info = joint_pts_info[0]
            joint_pt = joint_pt_info[1]
            self_timber = joint_pt_info[3]
            other_timber = joint_pt_info[4]
            radian = Optimization.get_first_rotate_angle(joint_pts_info, 0, curve_length_list[0])

        # rotate angle
        temp_radian_list = [radian, -radian]

        # axis of rotation and rotation center
        rotation_center = Optimization.get_mid_pt_in_closed_crv(intersect_info_list[index][1][0])
        axis = Vector3d(rotation_center - joint_pt)

        temp_intersection_list = []
        for i in range(2):
            # rotate timber
            self_timber.rotate_timber_in_program(temp_radian_list[i], axis, rotation_center)

            # get the length of the intersection curve
            intersect_info = Intersect.Intersection.BrepBrep(self_timber.surface_breps[0],
                                                             other_timber.surface_breps[0], 0.01)

            sum_crv_length = 0
            if intersect_info[1]:
                for intersection_curve in intersect_info[1]:
                    sum_crv_length += intersection_curve.GetLength()
            else:
                sum_crv_length = 0

            # append curve length information to list
            temp_intersection_list.append(sum_crv_length)

            # reset the rotation process
            self_timber.rotate_timber_in_program(-temp_radian_list[i], axis, rotation_center)

        # print("temp curve length: {0}".format(temp_intersection_list))

        if index == 0:
            length_current_intersection_crv = curve_length_list[1]
        else:
            length_current_intersection_crv = curve_length_list[0]

        # calculate difference length of two curves
        diff_length_crv = []
        if length_current_intersection_crv is None:
            length_current_intersection_crv = 0

            for i in range(2):
                diff = length_current_intersection_crv - temp_intersection_list[i]
                diff_length_crv.append(diff)
        else:
            for i in range(2):
                diff = temp_intersection_list[i] - length_current_intersection_crv
                diff_length_crv.append(diff)

        # define rotation direction by difference length
        if diff_length_crv[0] < diff_length_crv[1]:
            return 1, radian
        else:
            return -1, radian

    @staticmethod
    def get_joint_pts_info(adding_timbers, timber_list_in_playground):
        """
        :param adding_timbers: 追加する木材群
        :param timber_list_in_playground: 遊び場に既に生成されている木材群
        :return: 各接合点における情報(２次元配列)
                 [[joint_id, joint point, cross_vector, self timber, other timber]]
        """

        # Parameter
        joint_pts_info = []

        # 既に生成されている部材に接合するかどうかを決定する
        flag = rs.GetString("既に生成されている部材に接合しますか？ yes(y) or no(n)")

        if flag == "yes" or flag == "y":
            generated_timbers = []
            get_timber_ids = rs.GetString("既に生成されている部材のidを入力してください")
            get_timber_ids = get_timber_ids.split(',')

            for get_timber_id in get_timber_ids:
                for timber in timber_list_in_playground:
                    if timber.id == get_timber_id:
                        generated_timbers.append(timber)
        else:
            generated_timbers = []

        # 各木材の生成状況を読み、生成順番を決定する
        other_timbers = list(adding_timbers)  # 部材群
        if generated_timbers:
            for generated_timber in generated_timbers:
                other_timbers.append(generated_timber)

        # 各部材の接合点を計算し、取得する
        for self_timber in adding_timbers:
            temp_joint_pts = []

            for other_timber in other_timbers:
                if self_timber == other_timber:
                    continue
                else:

                    events = Intersect.Intersection.CurveCurve(self_timber.target_line.Line,
                                                               other_timber.center_line.ToPolylineCurve(),
                                                               0.001, 0.0)

                    if not events:
                        continue
                    else:
                        for event in events:
                            # timberクラスインスタンスに接合点情報を格納
                            joint_pt_id = self_timber.id + "-" + other_timber.id
                            self_timber.joint_pts_info.append([joint_pt_id, event.PointA, other_timber])

                            # debug
                            temp_joint_pts.append([joint_pt_id, event.PointA, self_timber, other_timber])

                            # TODO ここの設定
                            if joint_pts_info:
                                is_processed = False
                                for joint_pt_info in joint_pts_info:
                                    if self_timber.id in joint_pt_info[0] and other_timber.id in joint_pt_info[0]:
                                        is_processed = True
                                        break
                                if not is_processed:
                                    # 部材の接合点を最適化する際に使用する移動ベクトルを取得 TODO ここのベクトルの向き
                                    move_vec = Vector3d.CrossProduct(self_timber.target_line.vector,
                                                                     other_timber.target_line.vector)

                                    unit_move_vec = utilize_vector(move_vec)

                                    # reverse_move_vec = move_vec
                                    # reverse_move_vec.Reverse()

                                    joint_pts_info.append(
                                        [joint_pt_id, event.PointA, unit_move_vec, self_timber, other_timber])
                            else:
                                # 部材の接合点を最適化する際に使用する移動ベクトルを取得 TODO ここのベクトルの向き
                                move_vec = Vector3d.CrossProduct(self_timber.target_line.vector,
                                                                 other_timber.target_line.vector)

                                unit_move_vec = utilize_vector(move_vec)

                                # reverse_move_vec = move_vec
                                # reverse_move_vec.Reverse()

                                joint_pts_info.append(
                                    [joint_pt_id, event.PointA, unit_move_vec, self_timber, other_timber])

        # 木材の接合部最適化を行う順番を決定する
        joint_pts_info = Optimization.get_order_joint_optimization(joint_pts_info, generated_timbers)

        return joint_pts_info

    @staticmethod
    def get_order_joint_optimization(joint_pts_info, generated_timbers):
        optimization_order_list = []

        # 並び替え
        for joint_pt_info in joint_pts_info:
            rating = 0
            self_timber = joint_pt_info[3]

            # 選択した木材の端部のいずれかが既に生成されている部材に接合する場合
            if generated_timbers:
                for generated_timber in generated_timbers:
                    if generated_timber.id in joint_pt_info[0]:
                        rating += 2

            # 選択した木材がGLから生成されている場合
            if self_timber.target_line.start_p.Z == 0 or self_timber.target_line.end_p.Z == 0:
                rating += 1

            # 部材の評価点を元に、部材をdictに格納する
            optimization_order_list.append([rating, joint_pt_info])

        # sorted()かけるとdict->list型に変換される
        sorted_optimization_order_list = sorted(optimization_order_list, key=lambda x: x[0], reverse=True)

        # 順序を入れ替えた新しいjoint_pt_infoを生成
        joint_pts_info = [joint_pt_info[1] for joint_pt_info in sorted_optimization_order_list]

        return joint_pts_info

    @staticmethod
    def get_move_vector(base_pt, self_timber_srf, other_timber_srf):

        origin_pt = Brep.ClosestPoint(self_timber_srf, base_pt)
        transform_pt = Brep.ClosestPoint(other_timber_srf, base_pt)

        # move_vec = Vector3d(transform_pt.X - origin_pt.X, transform_pt.Y - origin_pt.Y, transform_pt.Z - origin_pt.Z)
        # print(move_vec.Length)

        return origin_pt, transform_pt

    @staticmethod
    def get_mid_pt_in_closed_crv(target_crv):
        divide_num = 12

        crv_domain = target_crv.Domain
        crv_domain_unit_range = (crv_domain[1] - crv_domain[0]) / divide_num

        pt1 = target_crv.PointAt(crv_domain_unit_range * 0)
        pt2 = target_crv.PointAt(crv_domain_unit_range * (divide_num / 2))

        mid_pt = Line(pt1, pt2).PointAt(0.5)

        return mid_pt

    @staticmethod
    def get_pattern_of_processing_method(intersect_info_list):

        intersect_crv_length_list = []
        curve_length_list = [0, 0]

        for intersect_info in intersect_info_list:
            sum_crv_length = 0
            if intersect_info[1]:
                for crv in intersect_info[1]:
                    sum_crv_length += crv.GetLength()
                intersect_crv_length_list.append(sum_crv_length)
            else:
                intersect_crv_length_list.append(None)

        # 場合わけを行う
        rating_list = [0, 0]
        tolerance = 40

        for i, intersect_crv_length in enumerate(intersect_crv_length_list):

            if intersect_crv_length is None:
                rating_list[i] = 0
                curve_length_list[i] = None
                continue

            if 0 < intersect_crv_length <= tolerance:
                rating_list[i] = 3
                curve_length_list[i] = intersect_crv_length
                continue

            if intersect_crv_length > tolerance:
                rating_list[i] = 2
                curve_length_list[i] = intersect_crv_length
                continue

        # print("rating: {0}".format(rating_list))

        # 変形形式を決定し、戻り値として返す
        type_transform = None  # type_transform -> 0: move / 1: rotation / 2: Optimization is success
        select_index = None

        if sum(rating_list) == 6:
            return [2], curve_length_list

        elif sum(rating_list) == 5:
            type_transform = 1
            for i, rating in enumerate(rating_list):
                if rating == 3:
                    select_index = i
                elif rating == 2:
                    pass

        elif sum(rating_list) == 4:
            type_transform = 0
            if intersect_crv_length_list[0] > intersect_crv_length_list[1]:
                select_index = 1
            else:
                select_index = 0

        elif sum(rating_list) == 3:
            type_transform = 1
            for i, rating in enumerate(rating_list):
                if rating == 3:
                    select_index = i

        elif sum(rating_list) == 2:
            type_transform = 0
            for i, rating in enumerate(rating_list):
                if rating == 2:
                    select_index = i

        elif sum(rating_list) == 0:
            type_transform = 0
            select_index = 0

        return [type_transform, select_index], curve_length_list

    @staticmethod
    def old_get_rotate_direction(joint_pts_info, rotate_direction_list):

        for index in range(len(joint_pts_info)):

            base_pt_start = joint_pts_info[index][1]

            if index == 0:
                base_pt_end = joint_pts_info[1][1]
                trans_pt = joint_pts_info[1][5]
            else:
                base_pt_end = joint_pts_info[0][1]
                trans_pt = joint_pts_info[0][5]

            ### debug ###
            # line1 = Line(base_pt_start, base_pt_end)
            # line2 = Line(base_pt_start, trans_pt)
            #
            # scriptcontext.doc.Objects.AddLine(line1)
            # scriptcontext.doc.Objects.AddLine(line2)
            ### ----- ###

            # define plane and remap coordinate to plane space TODO 毎回平面を設定すると全部 + or - の値になってしまう
            temp_plane = Plane(base_pt_start, base_pt_end, trans_pt)

            remap_base_pt_start = temp_plane.RemapToPlaneSpace(base_pt_start)
            remap_base_pt_end = temp_plane.RemapToPlaneSpace(base_pt_end)
            remap_trans_pt = temp_plane.RemapToPlaneSpace(trans_pt)

            vec1 = Vector3d(Point3d.Subtract(remap_trans_pt[1], remap_base_pt_start[1]))
            vec2 = Vector3d(Point3d.Subtract(remap_base_pt_end[1], remap_base_pt_start[1]))

            cross_vec = Vector3d.CrossProduct(vec1, vec2)

            # TODO
            if cross_vec.Z > 0:
                rotate_direction_list[index] = 1  # + rotate
            else:
                rotate_direction_list[index] = -1  # - rotate

        return rotate_direction_list

    @staticmethod
    def get_first_rotate_angle(joint_pts_info, index, curve_length):

        base_pt_start = joint_pts_info[index][1]

        if index == 0:
            base_pt_end = joint_pts_info[1][1]
            trans_pt = joint_pts_info[1][5]
        else:
            base_pt_end = joint_pts_info[0][1]
            trans_pt = joint_pts_info[0][5]

        # TODO 半径分の角度を考慮しないといけない --> 現状は1.3倍することで値を調整している
        vec1 = Vector3d(base_pt_end - base_pt_start)
        vec2 = Vector3d(trans_pt - base_pt_start)

        vec_radian = Vector3d.VectorAngle(vec1, vec2)
        vec_radian = vec_radian * 1.3

        # 回転方向を決定する --> 交差曲線の長さから考察
        if curve_length is None:
            # print("curve length is none")

            # 回転方向を決定する --> +方向、-方向に回転させた時の交差曲線の長さから考察
            pass


        elif curve_length < 200:
            # print("Do not Change")
            vec_radian = Optimization.get_proper_rotate_angle(curve_length)

        return vec_radian
