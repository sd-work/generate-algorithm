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


def remap_to_plane_space():
    origin = Point3d(0, 0, 0)
    pt1 = Point3d(100, 0, 0)
    pt2 = Point3d(50, 0, 50)
    print(pt1, pt2)

    vec1 = Vector3d(Point3d.Subtract(pt1, origin))
    vec2 = Vector3d(Point3d.Subtract(pt2, origin))

    cross_vec = Vector3d.CrossProduct(vec1, vec2)
    print(cross_vec)

    # plane
    plane = Plane(origin, pt1, pt2)

    remap_origin = plane.RemapToPlaneSpace(origin)
    remap_pt1 = plane.RemapToPlaneSpace(pt1)
    remap_pt2 = plane.RemapToPlaneSpace(pt2)
    print(remap_pt1[1], remap_pt2[1])

    vec1 = Vector3d(Point3d.Subtract(remap_pt1[1], remap_origin[1]))
    vec2 = Vector3d(Point3d.Subtract(remap_pt2[1], remap_origin[1]))

    cross_vec = Vector3d.CrossProduct(vec1, vec2)
    print(cross_vec)


remap_to_plane_space()

# get_rotate_direction()
