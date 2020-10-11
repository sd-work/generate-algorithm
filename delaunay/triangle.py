# coding: utf-8
import math
from Rhino.Geometry import *
import scriptcontext
import rhinoscriptsyntax as rs


class Triangle:

    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.vertex = [p1, p2, p3]
        self.polyline_curve = self.generate_polyline_curve()
        self.radius = None
        self.center_p = None
        self.line1_guid = None
        self.line2_guid = None
        self.line3_guid = None
        self.polyline_guid = None
        self.circle_guid = None

    def generate_polyline_curve(self):
        point_list = [Point3d(pt.x, pt.y, pt.z) for pt in self.vertex]
        return PolylineCurve(point_list)

    # 任意の3点の外接円の中心と半径を取得
    def cul_center_coordinate_and_radius(self):

        # 外接円の中心点を計算
        c = 2 * ((self.p2.x - self.p1.x) * (self.p3.y - self.p1.y) - (self.p2.y - self.p1.y) * (self.p3.x - self.p1.x))

        x = ((self.p3.y - self.p1.y) * (pow(self.p2.x, 2) - pow(self.p1.x, 2) + pow(self.p2.y, 2) - pow(self.p1.y, 2)) +
             (self.p1.y - self.p2.y) * (
                     pow(self.p3.x, 2) - pow(self.p1.x, 2) + pow(self.p3.y, 2) - pow(self.p1.y, 2))) / c

        y = ((self.p1.x - self.p3.x) * (pow(self.p2.x, 2) - pow(self.p1.x, 2) + pow(self.p2.y, 2) - pow(self.p1.y, 2)) +
             (self.p2.x - self.p1.x) * (
                     pow(self.p3.x, 2) - pow(self.p1.x, 2) + pow(self.p3.y, 2) - pow(self.p1.y, 2))) / c

        self.center_p = [x, y, 0]

        # 外接円の半径を計算
        self.radius = math.sqrt(pow((self.p1.x - self.center_p[0]), 2) + pow((self.p1.y - self.center_p[1]), 2))

        # debug
        # pt = Point3d(self.center_p[0], self.center_p[1], self.center_p[2])
        # circle = Circle(pt, self.radius)
        # self.circle_guid = scriptcontext.doc.Objects.AddCircle(circle)

    def delete_circle_guid(self):
        if self.circle_guid:
            rs.DeleteObject(self.circle_guid)

    def delete_triangle_guid(self):
        if self.polyline_guid:
            rs.DeleteObject(self.polyline_guid)

    # 分割三角形をRhinoに描画するためのメソッド
    def draw_divide_triangle(self):
        points = [self.p1.point, self.p2.point, self.p3.point, self.p1.point]
        self.polyline_guid = scriptcontext.doc.Objects.AddPolyline(points)

        # line1 = Rhino.Geometry.Line(self.p1.x, self.p1.y, self.p1.z, self.p2.x, self.p2.y, self.p2.z)
        # line2 = Rhino.Geometry.Line(self.p1.x, self.p1.y, self.p1.z, self.p3.x, self.p3.y, self.p3.z)
        # line3 = Rhino.Geometry.Line(self.p2.x, self.p2.y, self.p2.z, self.p3.x, self.p3.y, self.p3.z)
        # self.line1_guid = scriptcontext.doc.Objects.AddLine(line1)
        # self.line2_guid = scriptcontext.doc.Objects.AddLine(line2)
        # self.line3_guid = scriptcontext.doc.Objects.AddLine(line3)

    # 外接円に任意の点が内包されているかどうか判定"""
    def judge_test_point_in_circumscribed_circle(self, test_pt):
        distance = math.sqrt(pow((test_pt.x - self.center_p[0]), 2) + pow((test_pt.y - self.center_p[1]), 2))

        if distance < self.radius:
            return True
        else:
            return False

    def judge_test_point_in_triangle(self, test_pt):

        vec1 = Vector3d(self.p1.point - test_pt.point)
        vec2 = Vector3d(self.p2.point - test_pt.point)
        vec3 = Vector3d(self.p3.point - test_pt.point)

        angle1 = Vector3d.VectorAngle(vec1, vec2)
        angle2 = Vector3d.VectorAngle(vec2, vec3)
        angle3 = Vector3d.VectorAngle(vec1, vec3)

        sum_angle = math.degrees(angle1) + math.degrees(angle2) + math.degrees(angle3)
        print(math.degrees(angle1), math.degrees(angle2), math.degrees(angle3))
        print(sum_angle)

        if int(sum_angle) == 360:
            return True
        else:
            return False

        # cross1 = calc_cross(vec1, vec2)
        # cross2 = calc_cross(vec2, vec3)
        # cross3 = calc_cross(vec1, vec3)
        # cross1 = Vector3d.CrossProduct(vec1, vec2)
        # cross2 = Vector3d.CrossProduct(vec2, vec3)
        # cross3 = Vector3d.CrossProduct(vec1, vec3)

        # print(cross1, cross2, cross3)
        #
        # if cross1 < 0 and cross2 < 0 and cross3 < 0:
        #     return True
        #
        # elif cross1 > 0 and cross2 > 0 and cross3 > 0:
        #     return True
        #
        # else:
        #     return False

        # if cross1.Length < 0 and cross2.Length < 0 and cross3.Length < 0:
        #     return True
        #
        # elif cross1.Length > 0 and cross2.Length > 0 and cross3.Length > 0:
        #     return True
        #
        # else:
        #     return False


def calc_cross(vec1, vec2):
    vec1_length = vec1.Length
    vec2_length = vec2.Length
    angle = Vector3d.VectorAngle(vec1, vec2)
    print(angle)

    return vec1_length * vec2_length * math.sin(math.radians(angle))




















