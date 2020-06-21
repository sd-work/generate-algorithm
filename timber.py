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


class Timber:

    def __init__(self, id, length=None, path_to_csv=None):
        self.id = id
        self.center_line = None
        self.center_line_guid = None
        self.length = length
        self.surface = None
        self.surface_guid = None
        self.path_to_csv = path_to_csv
        self.is_used = False

        # temp parameter
        self.section_curves_info = []
        self.center_points = []
        self.section_curves = []  # 断面曲線のリスト

        # temp method
        self.generate_timber_info(random.randint(900, 1800))

    # 断面曲面から仮想の木材データを生成する
    def generate_timber_info(self, timber_length):
        # 中心線を構成する中心点群を生成
        split_num = 50
        unit_center_point_z = abs(timber_length / split_num)

        for i in range(split_num):
            section_curves_info = [random.randint(-5, 5), random.randint(-5, 5), i * unit_center_point_z]  # 中心点
            radius_section_crv = random.randint(50, 60)  # 半径
            section_curves_info.append(radius_section_crv)
            self.section_curves_info.append(section_curves_info)

        # 点群から中心線を生成
        start = Rhino.Geometry.Point3d(self.section_curves_info[0][0], self.section_curves_info[0][1],
                                       self.section_curves_info[0][2])
        end = Rhino.Geometry.Point3d(self.section_curves_info[-1][0], self.section_curves_info[-1][1],
                                     self.section_curves_info[-1][2])
        self.length = start.DistanceTo(end)

    def generate_timber(self):
        # csvファイルから木材の情報を取得し、変数に代入する
        with open(self.path_to_csv, "r") as csv_file:
            reader = csv.reader(csv_file)
            self.section_curves_info = [section_crv_info for section_crv_info in reader]

        # 断面曲線情報から木材のsrfモデルを生成
        for crv_info in self.section_curves_info:
            point = Rhino.Geometry.Point3d(float(crv_info[0]), float(crv_info[1]), float(crv_info[2]))
            section_curve = NurbsCurve.CreateFromCircle(Rhino.Geometry.Circle(point, float(crv_info[3])))
            self.center_points.append(point)
            self.section_curves.append(section_curve)

        self.center_line = Rhino.Geometry.Polyline(self.center_points)
        self.surface = Rhino.Geometry.Brep.CreateFromLoft(self.section_curves, Point3d.Unset, Point3d.Unset,
                                                          LoftType.Loose,
                                                          False)

        # draw model -> ライノ空間上に描画させる
        self.center_line_guid = scriptcontext.doc.Objects.AddPolyline(self.center_line)
        for srf in self.surface:
            self.surface_guid = scriptcontext.doc.Objects.AddBrep(srf)

        # 木材を使用済みにする
        self.is_used = True

    # timberを移動させる
    def transform_timber(self, origin_p, transform_p):
        xf = Rhino.Geometry.Transform.Translation(transform_p - origin_p)
        scriptcontext.doc.Objects.Transform(self.center_line_guid, xf, True)  # 中心線
        scriptcontext.doc.Objects.Transform(self.surface_guid, xf, True)  # 表面サーフェス

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

        # TODO pandasやnumpyはironpythonの環境では使用できない！
        # index = ["point" + str(i) for i in range(len(self.section_curves_info))]
        # columns = ["x", "y", "z"]
        #
        # df = pd.DataFrame(data=self.section_curves_info, index=index, columns=columns)
        #
        # df.to_csv(path)
