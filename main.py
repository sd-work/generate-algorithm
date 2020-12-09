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
num_processes = 1

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

    global t1, t2, t3, t4, t5, t6

    # 試行回数だけ処理を行う
    for i in range(num_processes):
        # t1 = time.time()

        # 01. ターゲット曲線を生成する
        playground.get_target_line()

        t2 = time.time()

        rs.EnableRedraw(False)

        # 02. 新たに追加する木材を選定し、生成する
        playground.select_adding_timber()

        t3 = time.time()

        # 03. 移動や回転を行い、木材を所定の位置に配置する
        playground.transform_timber()

        t4 = time.time()

        # 04. 木材の表面の最適化を行う
        flag = playground.minimized_joint_area()
        if not flag: break

        t5 = time.time()

        # 05. グラフ表記から現状の構造体の状況を取得する
        playground.analysis_structure(i)

        t6 = time.time()

        # reset
        playground.reset()

        # TODO 00. csvファイル(データベース)の木材情報を更新する

    # main, sub layerにedgeを振り分ける
    playground.structure.set_edges_to_main_sub_layer()

    # 属性User textを設定する→OpenSeesで使用するため
    playground.set_user_text()

    # 荷重点を読み込む
    nodal_load_pts = playground.free_end_coordinates

    rs.EnableRedraw(True)

    # Save Object instance
    flag = rs.GetString("今回の生成データを保存しますか？ yes(y) or no(n)")

    if flag == "y" or flag == "yes":
        with open("test.binaryfile", "wb") as web:
            pickle.dump(playground, web)

        # with open("Backup-BinaryFile\\test.binaryfile") as web:
        #     pickle.dump(playground, web)

    # Master timberのsurface, center line guidを非表示にする
    for timber in playground.timbers_in_structure:
        rs.HideObject(timber.surface_guid)
        rs.HideObject(timber.center_line_guid)

    # Next process flag
    toggle = True

    # 処理時間を表示
    # elapsed_time1 = t2 - t1
    elapsed_time2 = t3 - t2
    elapsed_time3 = t4 - t3
    elapsed_time4 = t5 - t4
    elapsed_time5 = t6 - t5

    # print("elapsed time1: {0}".format(elapsed_time1))
    print("select timber: {0}".format(elapsed_time2))
    print("transform: {0}".format(elapsed_time3))
    print("optimization: {0}".format(elapsed_time4))
    print("color code: {0}".format(elapsed_time5))













