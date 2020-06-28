# coding: utf-8

from Rhino.Geometry import *
import rhinoscriptsyntax as rs
import math
import random
import sys
import codecs
from timber import *
from target_line import *


class Playground:

    def __init__(self):
        self.timber_list = []  # 遊び場を構成している部材の数
        self.adding_timber = None

    # 部材データを生成する TODO ここはスキャンした3Dデータに切り替える
    def generate_timber_info(self, num_timber):
        for id in range(num_timber):
            timber = Timber(id)
            self.timber_list.append(timber)

            # 木材の情報をcsvファイルとして書き出す
            timber.export_csv_file("timber_" + str(id + 1))

    def export_csv_file(self):
        path = r"G:\マイドライブ\2020\04_Master\2006_Generation-algorithm\RhinoPython\csv\timber_info.csv"

        with open(path, "w") as csv_file:
            writer = csv.writer(csv_file)

            for timber in self.timber_list:
                # TODO サーバーとやりとりをするので、データベース上に使用した材かどうかの記述をするように変更する
                writing_info = [timber.id, timber.length, timber.path_to_csv.encode("utf-8")]

                writer.writerow(writing_info)

    def open_csv_file(self):
        path = r"G:\マイドライブ\2020\04_Master\2006_Generation-algorithm\RhinoPython\csv\timber_info.csv"

        with codecs.open(path, "r", "utf-8") as csv_file:
            reader = csv.reader(csv_file)
            for info in reader:
                if not info:
                    continue

                self.timber_list.append(Timber(info[0], info[1], info[2]))

    def select_adding_timber(self, target_line):

        # 木材の長さ
        # target_length = 0

        # 部材の端点のいずれかがGLから生成される場合
        if target_line.start_p.Z == 0 or target_line.end_p.Z == 0:
            if target_line.start_p.Z == 0:
                pass
            else:
                temp_p = target_line.start_p
                target_line.start_p = target_line.end_p
                target_line.end_p = temp_p
                target_line.vector = Rhino.Geometry.Vector3d(target_line.end_p - target_line.start_p)

            target_length = target_line.length + random.randint(300, 400)

        else:
            vec1 = Vector3d(target_line.start_p - target_line.mid_p)
            vec2 = Vector3d(target_line.end_p - target_line.mid_p)

            unit_vec1 = Vector3d(vec1.X / vec1.Length, vec1.Y / vec1.Length, vec1.Z / vec1.Length)
            unit_vec2 = Vector3d(vec2.X / vec2.Length, vec2.Y / vec2.Length, vec2.Z / vec2.Length)

            vec_length1 = vec1.Length + random.randint(300, 600)
            vec_length2 = vec2.Length + random.randint(300, 600)

            new_vec1 = Vector3d(unit_vec1.X * vec_length1, unit_vec1.Y * vec_length1, unit_vec1.Z * vec_length1)
            new_vec2 = Vector3d(unit_vec2.X * vec_length2, unit_vec2.Y * vec_length2, unit_vec2.Z * vec_length2)

            new_vec1 = Vector3d.Add(new_vec1, Vector3d(target_line.mid_p))
            new_vec2 = Vector3d.Add(new_vec2, Vector3d(target_line.mid_p))

            new_target_line = Line(Point3d(new_vec1.X, new_vec1.Y, new_vec1.Z),
                                   Point3d(new_vec2.X, new_vec2.Y, new_vec2.Z))

            target_length = new_target_line.Length

        print("target_length: {0}".format(target_length))

        # 条件に合致する木材を取得
        candidate_timbers = []

        select_timber = None
        min_diff_length = 10000
        for i, timber in enumerate(self.timber_list):
            # TODO ここの処理はいずれはサーバーとのやりとりの中で行う
            if timber.is_used:
                continue

            # ターゲット曲線と木材の長さの差異を計算する
            diff_length = abs(timber.length - target_length)

            if diff_length < min_diff_length:
                select_timber = timber
                min_diff_length = diff_length
                print(min_diff_length)

            # # TODO 長さがMaxのモノが選定されるとバグがでる。要改善
            # if target_length - 200 <= timber.length <= target_length + 200:
            #     diff_length = abs(timber.length - target_length)
            #     candidate_timbers.append(timber)

        # # ランダムに1つの木材を選択 TODO ここもいずれは調整したい。ランダム性を。
        # if not candidate_timbers:
        #     print("There is not timber in candidate timbers list.")
        #     return

        # self.adding_timber = random.choice(candidate_timbers)
        self.adding_timber = select_timber

        self.adding_timber.generate_timber()

    def transform_timber(self, target_line):
        # 01. translate
        origin_p = self.adding_timber.center_line.First  # timberの端点
        transform_p = target_line.start_p  # ターゲット曲線の端点
        self.adding_timber.translate_timber(origin_p, transform_p)

        # 02. rotation
        self.adding_timber.rotation_timber(target_line.vector)
