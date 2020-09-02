# coding: utf-8

import copy
import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs

from .node import Node
from .edge import Edge
from .cycle import Cycle


class Graph:

    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        self.contiguous_list = []
        self.cycles = []
        self.cycles_instance = []

        # Variables specific to virtual graph

    def set_graph(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def create_graph(self):
        self.contiguous_list = []

        for node in self.nodes:
            node.sort_connected_nodes()
            self.contiguous_list.append(node.connected_nodes)

        # debug
        temp_contiguous_list = []
        for node in self.contiguous_list:
            temp = []
            for connected_node in node:
                temp.append(connected_node.id)
            temp_contiguous_list.append(temp)
        print(temp_contiguous_list)

    @staticmethod
    def create_node_from_joint_pts(num_nodes_in_playground, joint_pts_info):
        # Get joint point nodes
        joint_pts_nodes = []

        for i, joint_pt_info in enumerate(joint_pts_info):
            joint_pt = joint_pt_info[1]
            joint_pt_node = Node(num_nodes_in_playground + 2 + i, joint_pt)
            joint_pts_nodes.append(joint_pt_node)

            # Draw node in doc
            joint_pt_node.generate_node_point("r-node")

        return joint_pts_nodes

    def get_closest_edge_from_test_point(self, test_pt):
        edge_to_get = None
        min_distance = 10000

        for edge in self.edges:
            distance = edge.edge_line.DistanceTo(test_pt, True)

            if distance < min_distance:
                min_distance = distance
                edge_to_get = edge
            else:
                continue

        return edge_to_get

    def detect_edge_of_real_graph(self, num_joint_pts, node1, node2, edges_in_playground, nodes_in_playground,
                                  joint_pts_nodes=None, timber=None):

        if num_joint_pts == 0:
            id = str(node1.id) + "-" + str(node2.id)
            edge = Edge(id, node1, node2, timber)

            # Record the nodes to which each node is connected
            node1.connected_nodes.append(node2)
            node2.connected_nodes.append(node1)
            node1.sort_connected_nodes()
            node2.sort_connected_nodes()

            # Draw edge line in doc
            edge.generate_edge_line("r-edge")

            # Maintain node information
            edges_in_playground.append(edge)

            return [edge]

        else:
            edges = []
            delete_old_edges = []

            for i in range(num_joint_pts):
                joint_pt_node = joint_pts_nodes[i]
                edge_to_get = self.get_closest_edge_from_test_point(joint_pt_node.point)
                print("edge to get: {0}".format(edge_to_get.id))

                """ Get edge(adding timber node and joint point node) """
                if num_joint_pts == 1:
                    id = str(node1.id) + "-" + str(joint_pt_node.id)
                    edge1 = Edge(id, node1, joint_pt_node, timber)

                    id = str(node2.id) + "-" + str(joint_pt_node.id)
                    edge2 = Edge(id, node2, joint_pt_node, timber)

                    # Record the nodes to which each node is connected
                    node1.set_connected_nodes(joint_pt_node)
                    node2.set_connected_nodes(joint_pt_node)
                    node1.sort_connected_nodes()
                    node2.sort_connected_nodes()

                    # Draw edge line in doc
                    edge1.generate_edge_line("r-edge")
                    edge2.generate_edge_line("r-edge")

                    # Record the nodes to which joint point is connected
                    joint_pt_node.set_connected_nodes([node1, node2, edge_to_get.start_node, edge_to_get.end_node])
                    joint_pt_node.sort_connected_nodes()

                    # Maintain node information
                    edges_in_playground += edge1, edge2
                    edges = [edge1, edge2]

                elif num_joint_pts == 2:
                    node_to_get = Graph.get_closest_node_from_test_point(joint_pt_node.point, [node1, node2])

                    id = str(node_to_get.id) + "-" + str(joint_pt_node.id)
                    edge1 = Edge(id, node_to_get, joint_pt_node, timber)

                    if i == 0:
                        joint_pt_node2 = joint_pts_nodes[1]
                    else:
                        joint_pt_node2 = joint_pts_nodes[0]

                    id = str(joint_pt_node.id) + "-" + str(joint_pt_node2.id)
                    edge2 = Edge(id, joint_pt_node, joint_pt_node2, timber)

                    # Record the nodes to which each node is connected
                    node_to_get.set_connected_nodes(joint_pt_node)
                    joint_pt_node.set_connected_nodes(joint_pt_node2)
                    node_to_get.sort_connected_nodes()
                    joint_pt_node.sort_connected_nodes()

                    # Draw edge line in doc
                    if i == 0:
                        edge1.generate_edge_line("r-edge")
                    else:
                        edge1.generate_edge_line("r-edge")
                        edge2.generate_edge_line("r-edge")

                    # Record the nodes to which joint point is connected
                    joint_pt_node.set_connected_nodes(
                        [node_to_get, joint_pt_node2, edge_to_get.start_node, edge_to_get.end_node])
                    joint_pt_node.sort_connected_nodes()

                    # Maintain node information
                    if i == 0:
                        edges_in_playground.append(edge1)
                        edges.append(edge1)
                    else:
                        edges_in_playground += edge1, edge2
                        edges += edge1, edge2

                """ Get edge(Already generated timber node and joint point node) """
                already_generated_timber = edge_to_get.timber

                id = str(edge_to_get.start_node.id) + "-" + str(joint_pt_node.id)
                edge1 = Edge(id, edge_to_get.start_node, joint_pt_node, already_generated_timber)

                id = str(edge_to_get.end_node.id) + "-" + str(joint_pt_node.id)
                edge2 = Edge(id, edge_to_get.end_node, joint_pt_node, already_generated_timber)

                # Maintain node information
                edges_in_playground += edge1, edge2

                # Linking Node and Edge information to already generated timber
                already_generated_timber.nodes.append(joint_pt_node)

                already_generated_timber.edges.remove(edge_to_get)  # remove edge to get id from edges list
                already_generated_timber.edges += edge1, edge2

                # Draw edge line in doc
                edge1.generate_edge_line("r-edge")
                edge2.generate_edge_line("r-edge")

                # Record the nodes to which each node is connected
                # Start node that an edge has
                temp_connected_nodes = []
                if len(edge_to_get.start_node.connected_nodes) == 4:
                    for connected_node in edge_to_get.start_node.connected_nodes:
                        if connected_node == edge_to_get.end_node:  # edge_to_get.end_node.id TODO
                            continue
                        else:
                            temp_connected_nodes.append(connected_node)

                    temp_connected_nodes.append(joint_pt_node)

                    # Set connected nodes information to an edge
                    edge_to_get.start_node.set_connected_nodes(temp_connected_nodes)
                    edge_to_get.start_node.sort_connected_nodes()

                else:
                    # Set connected nodes information to an edge
                    edge_to_get.start_node.set_connected_nodes(joint_pt_node)
                    edge_to_get.start_node.sort_connected_nodes()

                # End node that an edge has
                temp_connected_nodes = []
                if len(edge_to_get.end_node.connected_nodes) == 4:
                    for connected_node in edge_to_get.end_node.connected_nodes:
                        if connected_node == edge_to_get.start_node:  # edge_to_get.start_node.id
                            continue
                        else:
                            temp_connected_nodes.append(connected_node)

                    temp_connected_nodes.append(joint_pt_node)

                    # Set connected nodes information to an edge
                    edge_to_get.end_node.set_connected_nodes(temp_connected_nodes)
                    edge_to_get.end_node.sort_connected_nodes()

                else:
                    # Set connected nodes information to an edge
                    edge_to_get.end_node.set_connected_nodes(joint_pt_node)
                    edge_to_get.end_node.sort_connected_nodes()

                # Judge whether joint point nodes have two GL node
                gl_nodes = joint_pt_node.judge_node_on_ground(nodes_in_playground)

                if gl_nodes:
                    id = str(gl_nodes[0].id) + "-" + str(gl_nodes[1].id)
                    edge = Edge(id, gl_nodes[0], gl_nodes[1], None)

                    # Maintain node information
                    edges_in_playground.append(edge)

                    # Draw edge line in doc
                    edge.generate_edge_line("r-edge")

                # delete old edge
                if num_joint_pts == 1:
                    edge_to_get.delete_guid()
                    edges_in_playground.remove(edge_to_get)
                elif num_joint_pts == 2:
                    if i == 0:
                        delete_old_edges.append(edge_to_get)
                    else:
                        delete_old_edges.append(edge_to_get)

                        for old_edge in delete_old_edges:
                            old_edge.delete_guid()
                            edges_in_playground.remove(old_edge)

            return edges

    def detect_edge_of_virtual_graph(self, virtual_node, edges_in_playground, edges_in_virtual):
        adding_virtual_nodes = []
        missing_edges = []

        for real_node in virtual_node.nodes_of_real_graph:
            for connected_node in real_node.connected_nodes:

                # If the selected node is the node that is shaping the cycle
                if connected_node in virtual_node.nodes_of_real_graph:

                    # Get Missing edge
                    edge_id = [real_node.id, connected_node.id]
                    edge_id.sort()

                    if edge_id in missing_edges:
                        continue
                    else:
                        missing_edges.append(edge_id)

                else:
                    new_connected_node = None

                    # if connected node is a part of real graph node of generated virtual node
                    flag = False
                    for v_node in self.nodes:
                        if not v_node.nodes_of_real_graph:
                            continue
                        if connected_node in v_node.nodes_of_real_graph:
                            new_connected_node = v_node
                            flag = True
                            break

                    if not flag:
                        new_connected_node = Node(connected_node.id, connected_node.point)  # 新たなinstanceとして生成

                        # Draw node in doc
                        new_connected_node.generate_node_point("v-node")

                    # get timber id which edge has
                    if real_node.id < connected_node.id:
                        check_edge_id = str(real_node.id) + "-" + str(connected_node.id)
                    else:
                        check_edge_id = str(connected_node.id) + "-" + str(real_node.id)

                    timber = None
                    real_edge = None
                    for edge in edges_in_playground:
                        if check_edge_id == edge.id:
                            real_edge = edge
                            timber = real_edge.timber
                            break

                    id = str(virtual_node.id) + "-" + str(new_connected_node.id)
                    v_edge = Edge(id, virtual_node, new_connected_node, timber)  # virtual node to new connected node

                    # connecting real edge information to virtual edge
                    v_edge.real_edge = real_edge
                    virtual_node.having_edges.append(v_edge)

                    # Record the nodes to which each node is connected
                    virtual_node.connected_nodes.append(new_connected_node)
                    new_connected_node.connected_nodes.append(virtual_node)
                    virtual_node.sort_connected_nodes()
                    new_connected_node.sort_connected_nodes()

                    adding_virtual_nodes.append(new_connected_node)
                    # self.nodes.append(new_connected_node)

                    # Draw edge line in doc
                    v_edge.generate_edge_line("v-edge")

                    # Maintain edge information
                    edges_in_virtual.append(v_edge)

                    # Delete old edge
                    if flag:  # new connected node is virtual node
                        for having_edge in new_connected_node.having_edges:
                            for r_node in virtual_node.nodes_of_real_graph:
                                for r_connected_node in r_node.connected_nodes:
                                    if str(r_connected_node.id) in str(having_edge.id):
                                        # delete old edge and connected node information
                                        for i, v_connected_node in enumerate(new_connected_node.connected_nodes):
                                            if v_connected_node.id == r_connected_node.id:
                                                new_connected_node.connected_nodes.pop(i)  # del node

                                                having_edge.delete_guid()  # del edge from  doc
                                                new_connected_node.having_edges.remove(having_edge)
                                                edges_in_virtual.remove(having_edge)  # del edge instance from edge list
                                                break
                                        else:
                                            continue
                                        break
                                else:
                                    continue
                                break
                            else:
                                continue
                            break

        # Calculate missing edges
        for missing_edge in missing_edges:
            missing_edge_id = str(missing_edge[0]) + "-" + str(missing_edge[1])

            for edge in edges_in_playground:
                if missing_edge_id == edge.id:
                    virtual_node.missing_edges.append(edge)
                    break
            else:
                continue
            break

        # debug
        # for edge in virtual_node.missing_edges:
        #     print(edge.id)

        return adding_virtual_nodes

    @staticmethod
    def get_closest_node_from_test_point(test_pt, reference_pts):
        node_to_get = None
        min_distance = 10000

        for reference_pt in reference_pts:
            distance = Point3d.DistanceTo(test_pt, reference_pt.point)

            if distance < min_distance:
                min_distance = distance
                node_to_get = reference_pt
            else:
                continue

        return node_to_get

    def generate_cycle(self, cycles, nodes_in_playground, layer_name):

        for cycle in cycles:
            if cycle in self.cycles:
                continue

            # Maintain cycle information
            self.cycles.append(cycle)

            num_node_on_gl = 0
            cycle_nodes_instance = []
            for node_id in cycle:
                if layer_name == "r-cycle":

                    node_instance = nodes_in_playground[node_id]
                    cycle_nodes_instance.append(nodes_in_playground[node_id])

                    # judge node on the GL
                    if -40 < node_instance.z < 40:
                        num_node_on_gl += 1

                elif layer_name == "v-cycle":
                    for node_in_playground in nodes_in_playground:
                        if node_in_playground.id == node_id:
                            node_instance = node_in_playground
                            cycle_nodes_instance.append(node_in_playground)

                            # judge node on the GL
                            if -40 < node_instance.z < 40:
                                num_node_on_gl += 1

            if num_node_on_gl == 2:
                is_on_gl = True
            else:
                is_on_gl = False

            cycle = Cycle("v-" + str(len(self.cycles)), cycle_nodes_instance, is_on_gl)  # instance
            cycle.generate_cycle_mesh(layer_name)  # Add cycle mesh
            self.cycles_instance.append(cycle)

            return cycle

        return None
