# coding: utf-8

import time
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
        # 00. ターゲット曲線を設定する
        # rs.Command("_Line")
        target_line = TargetLine(rs.GetObject("Pick up a target line", rs.filter.curve))

        # 01. 新たに追加する木材を選定し、生成する
        playground.select_adding_timber(target_line)

        # 02. 移動や回転などを行い、木材を所定の位置に配置する
        playground.transform_timber(target_line)

        # TODO 00. csvファイル(データベース)の木材情報を更新する

    # print("Done: {0}".format(time.time() - start))
