#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# generated by wxGlade 853e6e5689f4+ on Tue Oct  7 06:34:48 2014
#

import wx

# begin wxGlade: dependencies
import gettext
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class MessageDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MessageDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, *args, **kwds)
        self.msg_image = wx.StaticBitmap(self, wx.ID_ANY, (wx.ArtProvider_GetBitmap(wx.ART_TIP, wx.ART_MESSAGE_BOX, (48, 48))))
        self.msg_list = wx.ListCtrl(self, wx.ID_ANY, style=wx.BORDER_SUNKEN | wx.LC_NO_HEADER | wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.OK = wx.Button(self, wx.ID_OK, "")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MessageDialog.__set_properties
        self.SetTitle(_("wxGlade Message"))
        self.SetSize(wx.DLG_SZE(self, (250, 112)))
        self.msg_image.SetMinSize((48, 48))
        self.OK.SetFocus()
        self.OK.SetDefault()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MessageDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        msg_title = wx.StaticText(self, wx.ID_ANY, _("wxGlade Message"))
        msg_title.SetFont(wx.Font(-1, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_1.Add(msg_title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        sizer_2.Add(self.msg_image, 0, 0, 0)
        sizer_2.Add(self.msg_list, 1, wx.EXPAND | wx.LEFT, 10)
        sizer_1.Add(sizer_2, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        sizer_1.Add(self.OK, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizer(sizer_1)
        self.Layout()
        self.Centre()
        # end wxGlade

# end of class MessageDialog
if __name__ == "__main__":
    gettext.install("app") # replace with the appropriate catalog name

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    msgdialog = MessageDialog(None, wx.ID_ANY, "")
    app.SetTopWindow(msgdialog)
    msgdialog.Show()
    app.MainLoop()