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


class Playground:

    def __init__(self):
        self.timber_list_in_database = []  # データベース上にある部材
        self.timber_list_in_playground = []  # 遊び場を構成している部材
        self.target_line_in_playground = []  # 遊び場を構成しているターゲット曲線
        self.adding_timber = None
        self.adding_timbers = []
        self.adding_target_line = None

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
                self.timber_list_in_database.append(Timber(info[0], info[1], info[2]))

    def select_adding_timber(self, target_line):

        # 取得したターゲット曲線情報から、木材を追加するための新たなターゲット曲線情報を取得
        target_length, self.adding_target_line = Optimization.edit_adding_timber_range(target_line)

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
        vector_timber = Rhino.Geometry.Vector3d(self.adding_timber.center_line.Last - self.adding_timber.center_line.First)
        angle = Vector3d.VectorAngle(vector_timber, self.adding_target_line.vector)
        axis = Vector3d.CrossProduct(vector_timber, self.adding_target_line.vector)
        rotation_center = self.adding_timber.center_line.First
        self.adding_timber.rotate_timber(angle, axis, rotation_center)

    def minimized_joint_area(self):

        # ターゲット曲線の情報から接合点、ベクトルを計算し、取得する
        joint_pts_info = Optimization.get_joint_pts_info(self.adding_timbers, self.timber_list_in_playground)

        # 接する面積の最小化を行う TODO ここは汎用的(どんな追加状況でも生成可能)なアルゴリズムに変更する
        optimized_timbers = []
        optimized_unit_move_vec = []

        # print("num_joint_pt: {0}".format(len(joint_pts_info)))

        for i in range(len(joint_pts_info)):
            joint_pt = joint_pts_info[i][1]
            unit_move_vec = joint_pts_info[i][2]
            self_timber = joint_pts_info[i][3]
            other_timber = joint_pts_info[i][4]

            # TODO 汎用的なアルゴリズムに変更する
            if self_timber in optimized_timbers:
                # TODO switchした際にself timberはgenerated_timberではだめ！
                if other_timber in self.timber_list_in_playground:
                    # print("other timber is already used in playground")

                    # test
                    self_timber.bridge_joint_area(joint_pts_info)
                    return

                else:
                    self_timber = other_timber
                    other_timber = joint_pts_info[i][3]

            # vector TODO 汎用的なアルゴリズムに変更する
            if optimized_unit_move_vec:
                angle = Vector3d.VectorAngle(optimized_unit_move_vec[0], unit_move_vec)
                if angle == 0:
                    pass

                else:
                    unit_move_vec.Reverse()

            print("timber_{0}".format(self_timber.id))
            print("timber_{0}".format(other_timber.id))

            # optimization
            self_timber.minimized_joint_area(other_timber, joint_pt, unit_move_vec)

            # append list
            optimized_timbers.append(self_timber)
            optimized_timbers.append(other_timber)

            optimized_unit_move_vec.append(unit_move_vec)

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
