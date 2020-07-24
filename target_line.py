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
