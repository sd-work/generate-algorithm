# coding: utf-8

import os
import sys
import time
import pickle
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
from playground import *

# Documentの位置を指定する
sc.doc = Rhino.RhinoDoc.ActiveDoc

# parameter
num_processes = 2

# 前回のデータを引き継ぐかどうかを判定する
flag = rs.GetString("前回までのデータを使用しますか？ yes(y) or no(n)")

# データを引き継ぐ場合
if flag == "y" or flag == "yes":
    # Open Object information
    with open("test.binaryfile", "rb") as web:
        rs.EnableRedraw(False)

        # Load Playground instance
        playground = pickle.load(web)

        # Playground instanceから前回の構造体を描画するかどうかを判定する
        flag = rs.GetString("前回までのデータを描画しますか？ yes(y) or no(n)")

        if flag == "y" or flag == "yes":
            # レイヤーを生成
            playground.create_playground_layer()

            # データを復元する
            playground.restore_playground_instance()

            # Master timberのsurface, center line guidを非表示にする
            for timber in playground.timbers_in_structure:
                rs.HideObject(timber.surface_guid)
                rs.HideObject(timber.center_line_guid)

        rs.EnableRedraw(True)

else:
    # playgroundインスタンスを新しく生成
    playground = Playground()

    # init
    # playground.generate_timber_info(100)
    # playground.export_csv_file()

    # レイヤーを生成
    playground.create_playground_layer()

    # csvファイルを読み込み、木材情報を取り出す
    playground.open_csv_file()

if __name__ == "__main__":

    # 試行回数だけ処理を行う
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

        # reset
        playground.reset()

        # TODO 00. csvファイル(データベース)の木材情報を更新する

    # Master timberのsurface, center line guidを非表示にする
    for timber in playground.timbers_in_structure:
        rs.HideObject(timber.surface_guid)
        rs.HideObject(timber.center_line_guid)

    # 属性User textを設定する→OpenSeesで使用するため
    playground.set_user_text()

    # 荷重点を読み込む
    nodal_load_pts = playground.free_end_coordinates

    # Save Object
    flag = rs.GetString("今回の生成データを保存しますか？ yes(y) or no(n)")

    if flag == "y" or flag == "yes":
        with open("test.binaryfile", "wb") as web:
            pickle.dump(playground, web)

    # Next process flag
    toggle = True