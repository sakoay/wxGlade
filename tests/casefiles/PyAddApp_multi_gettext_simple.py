#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade "faked test version"
#

# This is an automatically generated file.
# Manual changes will be overwritten without warning!

import wx
import gettext
from MyAppFrame import MyAppFrame

if __name__ == "__main__":
    gettext.install("myapp") # replace with the appropriate catalog name

    myapp = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    appframe = MyAppFrame(None, wx.ID_ANY, "")
    myapp.SetTopWindow(appframe)
    appframe.Show()
    myapp.MainLoop()
