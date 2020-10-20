# coding: utf-8

import copy
import scriptcontext
from Rhino.Geometry import *
import rhinoscriptsyntax as rs


class Bolt:

    def __init__(self, id, start_pt, end_pt):
        self.id = id
        self.start_pt = start_pt
        self.end_pt = end_pt
        self.line = LineCurve(self.start_pt, self.end_pt)

        # About Guid
        self.line_guid = None

    def draw_line_guid(self, layer_name):
        layer = rs.AddLayer(str(self.id), [0, 0, 0], True, False, layer_name)

        self.line_guid = scriptcontext.doc.Objects.AddCurve(self.line)
        rs.ObjectLayer(self.line_guid, layer)

    def delete_line_guid(self):
        if self.line_guid:
            rs.DeleteObject(self.line_guid)