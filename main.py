# coding: utf-8

import time
import rhinoscriptsyntax as rs
from playground import *

if __name__ == "__main__":

    # parameter
    num_processes = 5

    # playgroundインスタンスを生成
    playground = Playground()

    # init
    # playground.generate_timber_info(100)
    # playground.export_csv_file()

    # レイヤーを生成
    playground.create_playground_layer()

    # csvファイルを読み込み、木材情報を取り出す
    playground.open_csv_file()

    for i in range(num_processes):
        # 01. ターゲット曲線を生成する
        playground.get_target_line()

        # 02. 新たに追加する木材を選定し、生成する
        playground.select_adding_timber()

        # 03. 移動や回転を行い、木材を所定の位置に配置する
        playground.transform_timber()

        # 04. 木材の表面の最適化を行う
        flag = playground.minimized_joint_area()
        if not flag: break

        # 05. グラフ表記から現状の構造体の状況を取得する
        playground.analysis_structure(i)
        # playground.determine_status_of_structure()

        # reset
        playground.reset()

        # TODO 00. csvファイル(データベース)の木材情報を更新する

    # Master timberのsurface, center line guidを非表示にする
    for timber in playground.timbers_in_structure:
        rs.HideObject(timber.surface_guid)
        rs.HideObject(timber.center_line_guid)
