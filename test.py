import rhinoscriptsyntax as rs
import os
import pickle


with open(path, "rb") as web:
    print("Load is success!")

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
