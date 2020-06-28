# coding: utf-8

from Rhino.Geometry import *
import rhinoscriptsyntax as rs
import math
import random
import sys
import codecs
from timber import *

class TargetLine:

    def __init__(self, guid):
        self.guid = guid
        self.line = rs.coercecurve(self.guid)
        self.length = self.calc_length()
        self.start_p = self.line.PointAtStart
        self.mid_p = self.line.PointAtNormalizedLength(0.5)
        self.end_p = self.line.PointAtEnd
        self.vector = Rhino.Geometry.Vector3d(self.end_p - self.start_p)

    def calc_length(self):
        return self.line.GetLength()

    def transform_line(self, origin_p, transform_p):
        xf = Rhino.Geometry.Transform.Translation(transform_p - origin_p)
        scriptcontext.doc.Objects.Transform(self.guid, xf, True)
