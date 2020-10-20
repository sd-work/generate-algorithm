# coding: utf-8

import Rhino
from Rhino.Geometry import *
import scriptcontext
import rhinoscriptsyntax as rs


class LineTimber:

    def __init__(self, obj_guid, master_line_timber_instance=None):
        self.line_guid = obj_guid
        self.line = rs.coerceline(self.line_guid)
        self.start_pt = self.line.From
        self.end_pt = self.line.To
        self.child_line_timber_list = []  # これが部材数を数える時に使える

        # Specific to child instance
        self.master_line_timber = master_line_timber_instance

    def draw_end_point(self):
        if self.start_pt:
            scriptcontext.doc.Objects.AddPoint(self.start_pt)

        if self.end_pt:
            scriptcontext.doc.Objects.AddPoint(self.end_pt)

