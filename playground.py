# coding: utf-8

from Rhino.Geometry import *
import rhinoscriptsyntax as rs
import math
import random
import sys
import codecs
from timber import *


class Playground:

    def __init__(self):
        self.timber_list = []  # 遊び場を構成している部材の数
        self.adding_timber = None

    # 部材データを生成する TODO ここはスキャンした3Dデータに切り替える
    def generate_timber(self, num_timber):
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

    def select_adding_timber(self, target_length):
        candidate_timbers = []

        # 条件に合致する木材を取得
        for timber in self.timber_list:
            # TODO ここの処理はいずれはサーバーとのやりとりの中で行う
            if timber.is_used:
                continue

            if target_length <= timber.length + 300 <= target_length + 600:
                candidate_timbers.append(timber)

        # ランダムに1つの木材を選択 TODO ここもいずれは調整したい。ランダム性を。
        if not candidate_timbers:
            print("There is not timber in candidate timbers list.")
            return

        self.adding_timber = random.choice(candidate_timbers)
        self.adding_timber.generate_timber()

    def transform_timber(self):
        origin_p = Point3d(0, 0, 0)
        transform_p = Point3d(random.randint(-500, 500), random.randint(-500, 500), 0)
        self.adding_timber.transform_timber(origin_p, transform_p)
