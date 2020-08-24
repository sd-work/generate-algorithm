# coding: utf-8

import copy


class Search:

    pos_in_cycle = -1  # サイクル中に含まれるノード
    history = []  # 訪問履歴
    history_list = []
    is_visited = []
    finished = []

    @staticmethod
    def detect_cycles_in_graph(graph):
        Search.is_visited = [False for _ in range(len(graph))]
        Search.finished = [False for _ in range(len(graph))]

        # DFS
        Search.dfs_detect_cycles_in_graph(graph, 0, -1)

        if Search.history_list:
            # サイクルを復元
            cycles = []
            for cycle_list in Search.history_list:
                cycle = []

                while cycle_list:
                    t = cycle_list[-1]  # リストの最後の要素を取得
                    cycle.append(t)
                    cycle_list.pop()  # 末尾の要素を削除

                    if t == cycle_list[0]:
                        cycles.append(cycle)
                        break
        else:
            cycles = []

        Search.reset()

        return cycles

    @staticmethod
    def dfs_detect_cycles_in_graph(graph, node_pos, previous_node=-1):

        # 指定されたノードを訪問済みにする
        Search.is_visited[node_pos] = True
        # print("Visiting {0}".format(node_pos))

        # 訪問済みのノードを履歴として保持する
        Search.history.append(node_pos)

        # 指定されたノード(親)の子ノードを取得
        for next_node in graph[node_pos]:
            # print("-- next node:{0} previous_node:{1} --".format(next_node, previous_node))

            # 逆流を禁止する
            if next_node == previous_node:
                continue

            # 完全終了したノードはスルーする
            if Search.finished[next_node]:
                continue

            # サイクルを検出
            if (Search.is_visited[next_node]) and (not Search.finished[next_node]):
                pos_in_cycle = next_node

                temp_history = copy.deepcopy(Search.history)
                temp_history.insert(0, pos_in_cycle)

                Search.history_list.append(temp_history)

                # reset
                Search.history = []

            if Search.is_visited[next_node]:  # 訪問済み
                continue

            # 再帰的に探索
            Search.dfs_detect_cycles_in_graph(graph, next_node, node_pos)

            # # サイクルを検出したならば、まっすぐに抜けていく
            # if Search.pos_in_cycle != -1:
            #     return

        if not Search.history:
            pass
        else:
            Search.history.pop()
        Search.finished[node_pos] = True  # 帰りがけ順？

    @staticmethod
    def reset():
        Search.history = []  # 訪問履歴
        Search.history_list = []
        Search.is_visited = []
        Search.finished = []