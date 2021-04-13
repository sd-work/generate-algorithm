# coding: utf-8

import os
import sys
import time
import pickle
import importlib
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc

# Documentの位置を指定する
sc.doc = Rhino.RhinoDoc.ActiveDoc

# parameter
num_processes = 1
split_num = 10  # 1つのedgeを何分割のsegmented edgeにするか
optimization_result = False

if __name__ == "__main__":

    if flag:

        # 試行回数だけ処理を行う
        for i in range(num_processes):

            # 01. ターゲット曲線を生成する
            # ここはARによって入力する
            playground_instance.get_target_line_from_pts(target_line_guid)

            # 02. 新たに追加する木材を選定し、生成する
            playground_instance.select_adding_timber()

            # 03. 移動や回転を行い、木材を所定の位置に配置する
            playground_instance.transform_timber()

            # 04. 木材の表面の最適化を行う
            optimization_result = playground_instance.minimized_joint_area(connected_timber_ids)
            if optimization_result is False: break

            # 05. モデル化した構造体モデルから現状の構造体の状況を計算する
            playground_instance.analysis_structure(i)

            # 06. main, sub layerにedgeを振り分け、各edgeの色分けをする
            playground_instance.structure.set_edges_to_main_sub_layer(split_num)

            # reset
            playground_instance.reset()

            # Todo csvファイル(データベース)の木材情報を更新する

        # 07. Master timberのsurface, center line guidを非表示にする
        for timber in playground_instance.timbers_in_structure:
            rs.HideObject(timber.surface_guid)
            rs.HideObject(timber.center_line_guid)

        # 08. section listを作成し、csv形式で保存する→OpenSeesで使用するため
        #     edgeの属性ユーザーテキストを設定
        playground_instance.create_section_csv_list(section_list_path)

        # 09. 構造解析で使用する荷重情報を取得する→OpenSeesで使用するため
        playground_instance.get_nodal_load_info(split_num)

        # 10. 属性User textを設定する→OpenSeesで使用するため
        playground_instance.set_user_text()

        rs.EnableRedraw(True)

        # 11. Save Object instance
        if optimization_result is False:
            # これまでの処理を取り消す
            rs.Command("-_Undo")
        else:
            flag = rs.GetString("今回の生成データを保存しますか？ yes(y) or no(n)")
            if flag == "y" or flag == "yes":
                with open(binary_file_path, "wb") as web:
                    pickle.dump(playground_instance, web)
            else:
                # これまでの処理を取り消す
                rs.Command("-_Undo")

        # 次の処理に進むかのflag
        next_flag = True
