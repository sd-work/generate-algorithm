# coding: utf-8

import copy


class Search:

    pos_in_cycle = -1  # サイクル中に含まれるノード
    history = []  # 訪問履歴
    history_list = []
    pre_order = []  # 行きがけ
    post_order = []  # 帰りがけ

    node_index_dict = {}  # [Node id, index]

    @staticmethod
    def detect_cycles_in_graph(graph):
        Search.pre_order = [False for _ in range(len(graph.contiguous_list))]
        Search.post_order = [False for _ in range(len(graph.contiguous_list))]

        ###
        for i, v_node in enumerate(graph.nodes):
            Search.node_index_dict[str(v_node.id)] = i
        print(Search.node_index_dict)
        ###

        graph_contiguous_list = graph.contiguous_list

        start_node = graph.nodes[0]
        start_node_id = start_node.id

        # DFS
        Search.dfs_detect_cycles_in_graph(graph_contiguous_list, start_node_id, -1)

        if Search.history_list:
            cycles = []
            
            for history in Search.history_list:
                cycle = []

                print(history)

                while history:
                    node = history[-1]  # リストの最後の要素を取得
                    cycle.append(node)
                    history.pop()  # 末尾の要素を削除

                    if node == history[0]:
                        # # サイクルが三角形である場合
                        # if len(cycle) == 3:
                        #     cycles.append(cycle)
                        cycles.append(cycle)

                        break
        else:
            cycles = []

        Search.reset()

        return cycles

    @staticmethod
    def dfs_detect_cycles_in_graph(graph, node_id, previous_node_id=-1):
        """
        
        :param graph: 
        :param node_id: index
        :param previous_node_id: id
        :return: 
        """

        # 指定されたノードを訪問済みにする
        list_index = Search.node_index_dict[str(node_id)]
        Search.pre_order[list_index] = True
        # print("Visiting {0}".format(node_id))

        # 訪問済みのノードを履歴として保持する
        Search.history.append(node_id)

        # 指定されたノード(親)の子ノードを取得 -> next_node is Node instance -> node.id (int or str)
        for next_node in graph[list_index]:
            # print("-- next node:{0} previous_node_id:{1} --".format(next_node.id, previous_node_id.id))

            select_node_id = next_node.id
            select_index = Search.node_index_dict[str(select_node_id)]

            # 逆流を禁止する
            if select_node_id == previous_node_id:
                continue

            # 完全終了したノードはスルーする
            if Search.post_order[select_index]:
                continue

            # サイクルを検出
            if (Search.pre_order[select_index]) and (not Search.post_order[select_index]):
                pos_in_cycle = select_node_id

                temp_history = copy.deepcopy(Search.history)
                temp_history.insert(0, pos_in_cycle)

                Search.history_list.append(temp_history)

                # reset
                Search.history = []

            if Search.pre_order[select_index]:  # 訪問済み
                continue

            # 再帰的に探索
            Search.dfs_detect_cycles_in_graph(graph, select_node_id, node_id)

        if not Search.history:
            pass
        else:
            Search.history.pop()
        Search.post_order[list_index] = True  # 帰りがけ順

    @staticmethod
    def reset():
        Search.history = []  # 訪問履歴
        Search.history_list = []
        Search.pre_order = []
        Search.post_order = []
        Search.node_index_dict = {}