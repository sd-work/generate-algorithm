# coding : utf-8

import math
import Rhino
from Rhino.Geometry import *


def get_rotate_direction():
    print("---cross product---")
    vec1 = Vector3d(10, 10, 10)
    vec2 = Vector3d(20, 5, 0)

    cross_vec1 = Vector3d.CrossProduct(vec1, vec2)
    cross_vec2 = Vector3d.CrossProduct(vec2, vec1)
    print(cross_vec1)
    print(cross_vec2)

def sub_point():
    pt1 = Point3d(100, 100, 0)
    pt2 = Point3d(50, 30, 0)

    new_pt = Point3d.Subtract(pt1, pt2)

    print(new_pt)

# get_rotate_direction()

sub_point()