# coding: utf-8

import time
from playground import *

if __name__ == "__main__":
    start = time.time()

    playground = Playground()

    # init
    # playground.generate_timber(20)
    # playground.export_csv_file()

    # csvファイルを読み込み、木材情報を取り出す
    playground.open_csv_file()

    for _ in range(20):
        # 01. 新たに追加する木材を選定し、生成する
        target_length = random.randint(900, 1800)
        playground.select_adding_timber(target_length)

        # 02. 移動・回転などを行う
        playground.transform_timber()

        # TODO 00. csvファイル(データベース)の木材情報を更新する

    print(time.time() - start)
