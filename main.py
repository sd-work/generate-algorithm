# coding: utf-8

import time
import rhinoscriptsyntax as rs
from playground import *
from target_line import *

if __name__ == "__main__":
    # start = time.time()

    # parameter
    num_processes = 3

    # playgroundインスタンスを生成
    playground = Playground()

    # init
    # playground.generate_timber_info(50)
    # playground.export_csv_file()

    # csvファイルを読み込み、木材情報を取り出す
    playground.open_csv_file()

    for _ in range(num_processes):
        # ターゲット曲線を取得する
        rs.Command("_Line")
        # rs.Command("_PolyLine")
        poly_target_line = rs.GetObjects("Pick up target lines", rs.filter.curve)
        explode_target_lines = rs.ExplodeCurves(poly_target_line, True)

        if not explode_target_lines:
            explode_target_lines = poly_target_line

        for target_line in explode_target_lines:
            # 00. ターゲット曲線を設定する
            target_line = TargetLine(target_line)

            # 01. 新たに追加する木材を選定し、生成する
            playground.select_adding_timber(target_line)

            # 02. 移動や回転などを行い、木材を所定の位置に配置する
            playground.transform_timber()

        # 03. 木材の表面の最適化を行う
        playground.minimized_joint_area()

        # reset
        playground.reset(explode_target_lines)

        # TODO 00. csvファイル(データベース)の木材情報を更新する

    # print("Done: {0}".format(time.time() - start))
