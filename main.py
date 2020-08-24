# coding: utf-8

import time
import rhinoscriptsyntax as rs

from playground import *
from target_line import *

if __name__ == "__main__":

    # parameter
    num_processes = 7

    # playgroundインスタンスを生成
    playground = Playground()

    # init
    # playground.generate_timber_info(50)
    # playground.export_csv_file()

    # レイヤーを生成
    playground.create_playground_layer()

    # csvファイルを読み込み、木材情報を取り出す
    playground.open_csv_file()

    for _ in range(num_processes):
        # ターゲット曲線を生成する
        rs.Command("_Line")

        poly_target_line = rs.GetObjects("Pick up target lines", rs.filter.curve)
        explode_target_lines = rs.ExplodeCurves(poly_target_line, True)
        if not explode_target_lines:
            explode_target_lines = poly_target_line

        # TODO 一次的な操作
        temp_num_of_joint_pt = rs.GetString("Input number of joint point")

        # main process
        for target_line in explode_target_lines:
            # 00. ターゲット曲線を設定する
            target_line = TargetLine(target_line)

            # 01. 新たに追加する木材を選定し、生成する
            playground.select_adding_timber(target_line, temp_num_of_joint_pt)

            # 02. 移動や回転などを行い、木材を所定の位置に配置する
            playground.transform_timber()

        # 03. 木材の表面の最適化を行う
        flag = playground.minimized_joint_area()
        if not flag:
            break

        # 04. グラフ表記から現状の構造体の状況を取得する
        playground.determine_status_of_structure()

        # reset
        playground.reset(explode_target_lines)

        # TODO 00. csvファイル(データベース)の木材情報を更新する
