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

    def set_user_text(self):
        # ばねモデルの剛性を設定する -> 今回はM12ボルトを使用する
        rs.SetUserText(self.line_guid, "kxt", "204658")  # 要素x軸正方向のばね剛性 ※引張剛性
        rs.SetUserText(self.line_guid, "kxc", "0")  # 要素x軸負方向のばね剛性 ※圧縮剛性
        rs.SetUserText(self.line_guid, "kyt", "169640")  # 要素y軸正方向のばね剛性 ※せん断剛性
        rs.SetUserText(self.line_guid, "kyc", "169640")  # 要素y軸負方向のばね剛性 ※せん断剛性
        rs.SetUserText(self.line_guid, "kzt", "1")  # 要素z軸正方向のばね剛性 ※せん断剛性
        rs.SetUserText(self.line_guid, "kzc", "1")  # 要素z軸負方向のばね剛性 ※せん断剛性
        rs.SetUserText(self.line_guid, "mx", "999999")  # 要素x軸周りの回転剛性 ※ねじり剛性
        rs.SetUserText(self.line_guid, "my", "0")  # 要素y軸周りの回転剛性 ※曲げ剛性
        rs.SetUserText(self.line_guid, "mz", "2022")  # 要素z軸周りの回転剛性 ※曲げ剛性

        # ばね要素の短期許容耐力を設定する -> 今回はM12ボルトを使用する
        # rs.SetUserText(self.line_guid, "Mya", "0")  # 短期許容曲げモーメント y軸周り
        # rs.SetUserText(self.line_guid, "Mza", "0")  # 短期許容曲げモーメント z軸周り
