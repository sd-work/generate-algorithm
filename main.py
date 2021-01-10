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
split_num = 10  # 1つのedgeを何分割のsegmented edgeにするか

# 前回のデータを引き継ぐかどうかを判定する
flag = rs.GetString("前回までのデータを使用しますか？ yes(y) or no(n)")

# データを引き継ぐ場合
if flag == "y" or flag == "yes":

    # Open Object information
    with open("binary_file\\playground.binaryfile", "rb") as web:
        rs.EnableRedraw(False)

        # Load Playground instance
        playground = pickle.load(web)

        # Playground instanceから前回の構造体を描画するかどうかを判定する
        flag = rs.GetString("前回までのデータを描画しますか？ yes(y) or no(n)")

        if flag == "y" or flag == "yes":
            # レイヤーを生成
            playground.create_playground_layer()

            # Todo データを復元する
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
    # playground.generate_timber_info(200)
    # playground.export_csv_file()

    # レイヤーを生成
    playground.create_playground_layer()

    # csvファイルを読み込み、木材情報を取り出す
    playground.open_csv_file()

if __name__ == "__main__":

    # 試行回数だけ処理を行う
    for i in range(num_processes):
        rs.EnableRedraw(True)

        # 01. ターゲット曲線を生成する
        playground.get_target_line()

        rs.EnableRedraw(False)

        # 02. 新たに追加する木材を選定し、生成する
        playground.select_adding_timber()

        # 03. 移動や回転を行い、木材を所定の位置に配置する
        playground.transform_timber()

        # 04. 木材の表面の最適化を行う
        flag = playground.minimized_joint_area()
        if not flag: break

        # 05. グラフ表記から現状の構造体の状況を取得する
        playground.analysis_structure(i)

        # 06. main, sub layerにedgeを振り分け、色分けをする
        playground.structure.set_edges_to_main_sub_layer(split_num)

        # reset
        playground.reset()

        # Todo csvファイル(データベース)の木材情報を更新する

    # 07. Master timberのsurface, center line guidを非表示にする
    for timber in playground.timbers_in_structure:
        rs.HideObject(timber.surface_guid)
        rs.HideObject(timber.center_line_guid)

    # 08. section listを作成し、csv形式で保存する→OpenSeesで使用するため
    playground.create_section_csv_list()

    # 09. 構造解析で使用する荷重情報を取得する→OpenSeesで使用するため
    playground.get_nodal_load_info(split_num)

    # 10. 属性User textを設定する→OpenSeesで使用するため
    playground.set_user_text()

    rs.EnableRedraw(True)

    # 11. Save Object instance
    flag = rs.GetString("今回の生成データを保存しますか？ yes(y) or no(n)")
    if flag == "y" or flag == "yes":
        with open("binary_file\\playground.binaryfile", "wb") as web:
            pickle.dump(playground, web)

