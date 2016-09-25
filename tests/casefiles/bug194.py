#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade e243dfc50cf6+ on Tue Aug 23 19:11:38 2016
#

import wx

# begin wxGlade: dependencies
import gettext
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class Frame194(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: Frame194.__init__
        wx.Frame.__init__(self, *args, **kwds)
        self.list_box_single = wx.ListBox(self, wx.ID_ANY, choices=[_("Listbox wxLB_SINGLE")])
        self.list_box_multiple = wx.ListBox(self, wx.ID_ANY, choices=[_("Listbox wxLB_MULTIPLE")], style=wx.LB_MULTIPLE)
        self.list_box_extended = wx.ListBox(self, wx.ID_ANY, choices=[_("Listbox wxLB_EXTENDED")], style=wx.LB_EXTENDED)
        self.check_list_box_single = wx.CheckListBox(self, wx.ID_ANY, choices=[_("CheckListBox wxLB_SINGLE")], style=wx.LB_SINGLE)
        self.check_list_box_multiple = wx.CheckListBox(self, wx.ID_ANY, choices=[_("CheckListBox wxLB_MULTIPLE")], style=wx.LB_MULTIPLE)
        self.check_list_box_extended = wx.CheckListBox(self, wx.ID_ANY, choices=[_("CheckListBox wxLB_EXTENDED")], style=wx.LB_EXTENDED)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: Frame194.__set_properties
        self.SetTitle(_("frame_1"))
        self.SetSize((800, 600))
        self.list_box_single.SetSelection(0)
        self.list_box_multiple.SetSelection(0)
        self.list_box_extended.SetSelection(0)
        self.check_list_box_single.SetSelection(0)
        self.check_list_box_multiple.SetSelection(0)
        self.check_list_box_extended.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: Frame194.__do_layout
        sizer_1 = wx.GridSizer(2, 3, 0, 0)
        sizer_1.Add(self.list_box_single, 1, wx.ALL | wx.EXPAND, 5)
        sizer_1.Add(self.list_box_multiple, 1, wx.ALL | wx.EXPAND, 5)
        sizer_1.Add(self.list_box_extended, 1, wx.ALL | wx.EXPAND, 5)
        sizer_1.Add(self.check_list_box_single, 1, wx.ALL | wx.EXPAND, 5)
        sizer_1.Add(self.check_list_box_multiple, 1, wx.ALL | wx.EXPAND, 5)
        sizer_1.Add(self.check_list_box_extended, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

# end of class Frame194
class MyApp(wx.App):
    def OnInit(self):
        Bug194_Frame = Frame194(None, wx.ID_ANY, "")
        self.SetTopWindow(Bug194_Frame)
        Bug194_Frame.Show()
        return True

# end of class MyApp

if __name__ == "__main__":
    gettext.install("app") # replace with the appropriate catalog name

    app = MyApp(0)
    app.MainLoop()