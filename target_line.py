# coding: utf-8

import scriptcontext
import Rhino
from Rhino.Geometry import *
import rhinoscriptsyntax as rs
import math
import random
import sys
import codecs
from timber import *


class TargetLine:

    def __init__(self, guid=None, rhino_obj=None):
        if guid:
            self.guid = guid
            self.Line = rs.coercecurve(self.guid)
        elif guid is None:
            self.guid = None
            self.Line = rhino_obj

        self.length = self.calc_length()
        self.start_p = self.Line.PointAtStart
        self.mid_p = self.Line.PointAtNormalizedLength(0.5)
        self.end_p = self.Line.PointAtEnd
        self.vector = Rhino.Geometry.Vector3d(self.end_p - self.start_p)

    def calc_length(self):
        return self.Line.GetLength()

    def calc_vector(self):
        self.vector = Rhino.Geometry.Vector3d(self.end_p - self.start_p)

    def transform_line(self, origin_p, transform_p):
        xf = Rhino.Geometry.Transform.Translation(transform_p - origin_p)
        scriptcontext.doc.Objects.Transform(self.guid, xf, True)

    def delete_line_guid(self):
        rs.DeleteObject(self.guid)

        self.guid = None

    @staticmethod
    def get_target_line():
        # ターゲット曲線の元になる基準線を生成する
        rs.Command("_Line")

        picked_based_line = rs.GetObjects("Pick up based lines", rs.filter.curve)
        based_target_line, divide_pts = TargetLine.generate_based_target_line(picked_based_line)

        # ターゲット曲線を生成する
        rs.Command("_Line")
        rs.DeleteObject(based_target_line)  # delete based target line
        rs.DeleteObjects(divide_pts)  # delete divided points
        picked_target_line = rs.GetObjects("Pick up target lines", rs.filter.curve)

        # Target line instanceを生成する
        target_line = TargetLine(picked_target_line)

        return target_line

    @staticmethod
    def generate_based_target_line(base_line_guid):
        divide_pts_guid = []
        base_line = rs.coercecurve(base_line_guid)

        if base_line.PointAtStart.Z == 0 or base_line.PointAtEnd.Z == 0:
            divide_segments = 20

            if base_line.PointAtStart.Z == 0:
                gl_point = base_line.PointAtStart
                to_point = base_line.PointAtEnd
            else:
                gl_point = base_line.PointAtEnd
                to_point = base_line.PointAtStart

            vector = Vector3d(to_point - gl_point)
            vector.Unitize()

            vector = Vector3d.Multiply(vector, 2000)
            vector = Vector3d.Add(vector, Vector3d(gl_point))

            desired_target_line = Line(Point3d(gl_point), Point3d(vector))

        else:
            divide_segments = 30

            # TODO ここでのターゲット曲線の生成方法にバグあり
            vec1 = Vector3d(base_line.PointAtStart - base_line.PointAt(0.5))
            vec2 = Vector3d(base_line.PointAtEnd - base_line.PointAt(0.5))

            vec1.Unitize()
            vec2.Unitize()

            new_vec1 = Vector3d.Multiply(vec1, 1500)
            new_vec2 = Vector3d.Multiply(vec2, 1500)
            new_vec1 = Vector3d.Add(new_vec1, Vector3d(base_line.PointAt(0.5)))
            new_vec2 = Vector3d.Add(new_vec2, Vector3d(base_line.PointAt(0.5)))

            desired_target_line = Line(Point3d(new_vec1), Point3d(new_vec2))

        # draw line in doc
        desired_target_line = scriptcontext.doc.Objects.AddLine(desired_target_line)

        # draw divide point in doc
        divide_pts = rs.DivideCurve(desired_target_line, divide_segments, False, True)
        for pt in divide_pts:
            pt_guid = rs.AddPoint(pt)
            divide_pts_guid.append(pt_guid)

        # Delete guid
        rs.DeleteObject(base_line_guid)

        return desired_target_line, divide_pts_guid
