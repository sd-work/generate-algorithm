# coding: utf-8

import math
import scriptcontext
import rhinoscript.utility
import Rhino


def calc_length(x, y, z):
    vec_length = math.sqrt(x * x + y * y * z * z)
    return vec_length


class PointVector:

    def __init__(self, _x=0, _y=0, _z=0):
        self.x = _x
        self.y = _y
        self.z = _z
        self.length = calc_length(self.x, self.y, self.z)

    def set_x(self, _x):
        self.x = _x

    def set_y(self, _y):
        self.y = _y

    def set_z(self, _z):
        self.z = _z

    def set_xyz(self, _x, _y, _z):
        self.x = _x
        self.y = _y
        self.z = _z

    def set_polar_xyz(self, length, phi, theta):
        """
        極座標→直角座標への変換
        :param length: 原点からの距離(長さ) 0 <= length <= ∞
        :param phi: x軸からのなす角(方位角) 0 <= phi <= 360(2pi)
        :param theta: z軸からのなす角(極角) 0 <= theta <= 180(pi)
        :return:
        """

        self.x = length * math.sin(math.pi/180*theta) * math.cos(math.pi/180*phi)
        self.y = length * math.sin(math.pi/180*theta) * math.sin(math.pi/180*phi)
        self.z = length * math.cos(math.pi/180*theta)

    def add(self, vec):
        self.x += vec.x
        self.y += vec.y
        self.z += vec.z

    def subtract(self, vec):
        self.x -= vec.x
        self.y -= vec.y
        self.z -= vec.z

    def multiply(self, d):
        self.x *= d
        self.y *= d
        self.z *= d

    def divide(self, d):
        self.x /= d
        self.y /= d
        self.z /= d

    def calc_distance(self, vec):
        dx = self.x - vec.x
        dy = self.y - vec.y
        dz = self.z - vec.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def dot(self, vec):
        return self.x * vec.x + self.y * vec.y + self.z * vec.z

    def cross(self, vec):
        pass
















