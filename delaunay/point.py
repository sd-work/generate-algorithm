# coding: utf-8
import rhinoscriptsyntax as rs
from Rhino.Geometry import *

class Point:
    def __init__(self, point_coordinate, virtual_node=None):
        self.virtual_node = virtual_node
        self.coordinate = point_coordinate
        self.x = point_coordinate[0]
        self.y = point_coordinate[1]
        self.z = point_coordinate[2]
        self.point = Point3d(self.x, self.y, self.z)
        self.connected_points = []

