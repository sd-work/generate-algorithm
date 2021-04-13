# coding: utf-8

import os
import sys
import time
import pickle
import importlib
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import playground

reload(playground)  # モジュールを更新する
from playground import Playground

# Documentの位置を指定する
sc.doc = Rhino.RhinoDoc.ActiveDoc


if reload_flag:

    # 前回のデータを引き継ぐかどうかを判定する
    flag = "yes"
    # flag = rs.GetString("前回までのデータを使用しますか？ yes(y) or no(n)")

    # データを引き継ぐ場合
    if flag == "y" or flag == "yes":

        # Open Object information
        with open(binary_file_path, "rb") as web:
            rs.EnableRedraw(False)

            # Load Playground instance
            playground_instance = pickle.load(web)

            # Playground instanceから前回の構造体を描画するかどうかを判定する
            # flag = rs.GetString("前回までのデータを描画しますか？ yes(y) or no(n)")

            # 既に描画済みなので、新たにDoc空間に描画しない
            if rs.IsLayer("playground"):
                pass

            # 初回なので、描画する
            else:
                # レイヤーを生成
                playground_instance.create_playground_layer()

                # データを復元する
                playground_instance.restore_playground_instance()

                # Master timberのsurface, center line guidを非表示にする
                for timber in playground_instance.timbers_in_structure:
                    rs.HideObject(timber.surface_guid)
                    rs.HideObject(timber.center_line_guid)

            rs.EnableRedraw(True)

    else:
        # playgroundインスタンスを新しく生成
        playground_instance = Playground()

        # init
        # playground.generate_timber_info(200)
        # playground.export_csv_file()

        # レイヤーを生成
        playground_instance.create_playground_layer()

        # csvファイルを読み込み、木材情報を取り出す
        playground_instance.open_csv_file()

    # 次の処理に進むかどうかのflag
    next_flag = True
