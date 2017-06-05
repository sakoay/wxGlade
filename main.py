"""\
Main wxGlade module: defines wxGladeFrame which contains the buttons to add
widgets and initializes all the stuff (tree, frame_property, etc.)

@copyright: 2002-2007 Alberto Griggio
@copyright: 2011-2016 Carsten Grohmann
@copyright: 2016 Dietmar Schwertberger
@license: MIT (see LICENSE.txt) - THIS PROGRAM COMES WITH NO WARRANTY
"""

# import general python modules
import logging, os, os.path, sys, math, time
import wx
from xml.sax import SAXParseException

# import project modules
import application
import common, config, compat, misc, clipboard
import preferencesdialog, msgdialog, bugdialog, about
import log
import template
from tree import WidgetTree
from xml_parse import XmlWidgetBuilder, ProgressXmlWidgetBuilder, XmlParsingError



class wxGladePropertyPanel(wx.Frame):
    "Panel used to display the Properties of the various widgets"
    def __init__(self, parent, frame_style):
        wx.Frame.__init__( self, parent, -1, _('Properties - <%s>' % _('app')), style=frame_style, name='PropertyFrame' )

        self.current_widget = None        # instance currently being edited
        self.next_widget = None           # the next one, will only be edited after a small delay

        self.pagenames = None

        self.notebook = wx.Notebook(self, -1)
        self.Bind(wx.EVT_CLOSE, self.hide_frame)

    def hide_frame(self, event):
        #menu_bar.Check(PROPS_ID, False)
        self.Hide()

    def is_visible(self):
        return self.IsShown()

    ####################################################################################################################
    # new editor interface
    def set_widget(self, widget, force=False):
        if widget is self.current_widget and not force:
            # just update
            return
        self.next_widget = widget
        if self.current_widget:
            for editor in self.current_widget.properties.values():
                editor.destroy_editor()
            self.current_widget = None   # delete the reference
        wx.CallLater( 150, self.edit_properties, widget )

    def edit_properties(self, edit_widget):
        # this will be called with a delay
        if edit_widget is not self.next_widget:
            # wait for another call...
            return

        self.current_widget = None
        self.create_editor(edit_widget)
        self.current_widget = edit_widget
        if self:
            self.SetTitle(_('Properties - %s - <%s>') % (edit_widget.klass, edit_widget.name) )

    def create_editor(self, edit_widget):
        # fill the frame with a notebook of property editors
        if not self.notebook: return  # already deleted
        self.current_widget_class = edit_widget.__class__

        self.notebook.Hide()

        # remember the notebook page to be selected
        selection = self.notebook.GetSelection()
        select_page = self.pagenames[selection]  if selection!=-1  else None

        # clear notebook pages
        if self.notebook.PageCount:
            #self.notebook.DeleteAllPages()  # deletes also the windows on the pages
            while self.notebook.PageCount:
                self.notebook.DeletePage(self.notebook.PageCount-1)

        self.editors = editors = {}

        self.pagenames = pagenames = []
        self.sizers = []
        current_page = current_sizer = current_pagename = None
        property_instance = None
        for prop in edit_widget.PROPERTIES:
            if prop[0].isupper():
                # end previous page
                if current_page is not None:
                    if property_instance and not property_instance.GROW:
                        current_sizer.AddStretchSpacer(prop=5)
                    self.end_page(current_page, current_sizer, current_pagename)
                    current_page = None

                # start new page
                current_pagename = prop
                if prop=="Layout" and not edit_widget._has_layout:continue
                if prop=="Events" and edit_widget.events is None: continue

                current_page = self.start_page(prop)
                current_sizer = wx.BoxSizer(wx.VERTICAL)
                self.sizers.append(current_sizer)

                self.pagenames.append(prop)

                continue

            if current_pagename=="Layout" and not edit_widget._has_layout: continue

            # a property or None
            property_instance_ = edit_widget.properties.get(prop)
            if property_instance_ is not None:
                property_instance = property_instance_
                property_instance.create_editor(current_page, current_sizer)

        if current_page is not None:
            self.end_page(current_page, current_sizer, current_pagename)

        if select_page and select_page in pagenames:
            index = pagenames.index(select_page)
            self.notebook.SetSelection(index)
        else:
            self.notebook.SetSelection(0)

        self.notebook.Show()

    def start_page(self, name):
        panel = wx.ScrolledWindow( self.notebook, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.FULL_REPAINT_ON_RESIZE,
                                   name=name )
        return panel
    def end_page(self, panel, sizer, header, select=False):
        panel.SetAutoLayout(1)
        #compat.SizerItem_SetSizer(panel, sizer)
        panel.SetSizer(sizer)
        sizer.Layout()
        sizer.Fit(panel)

        w, h = panel.GetClientSize()
        self.notebook.AddPage(panel, _(header),select=select)
        panel.SetScrollbars(1, 5, 1, int(math.ceil(h/5.0)))



class wxGladeArtProvider(wx.ArtProvider):
    def CreateBitmap(self, artid, client, size):
        if wx.Platform == '__WXGTK__' and artid == wx.ART_FOLDER:
            return wx.Bitmap(os.path.join(config.icons_path, 'closed_folder.xpm'), wx.BITMAP_TYPE_XPM)
        return wx.NullBitmap



class wxGladeFrame(wx.Frame):
    "Main frame of wxGlade (palette)"

    def __init__(self, parent=None):
        self._logger = logging.getLogger(self.__class__.__name__)
        style = wx.SYSTEM_MENU | wx.CAPTION | wx.MINIMIZE_BOX
        style |= wx.RESIZE_BORDER | wx.CLOSE_BOX
        version = config.version
        if version=='"faked test version"':
            version = "%s on Python %d.%d"%(version, sys.version_info.major, sys.version_info.minor)
        wx.Frame.__init__(self, parent, -1, "wxGlade v%s" % version, style=style, name='MainFrame')

        if parent is None:
            parent = self
        common.palette = self  # to provide a reference accessible by the various widget classes
        icon = compat.wx_EmptyIcon()
        bmp = wx.Bitmap( os.path.join(config.icons_path, "icon.xpm"), wx.BITMAP_TYPE_XPM )
        icon.CopyFromBitmap(bmp)
        self.SetIcon(icon)
        self.SetBackgroundColour( compat.wx_SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE) )

        self.create_menu(parent)

        # load the available code generators
        all_widgets = common.init_codegen()
        # build the palette for all_widgets
        sizer = wx.FlexGridSizer(0, 2, 0, 0)
        sizer.AddGrowableCol(0)
        self.SetAutoLayout(True)
        maxlen = max([len(all_widgets[sect]) for sect in all_widgets])  # the maximum number of buttons in a section
        for section in all_widgets:
            if section:
                sizer.Add(wx.StaticText(self, -1, "%s:" % section.replace('&', '&&')), 1, wx.ALIGN_CENTER_VERTICAL)

            bsizer = wx.GridSizer(cols=maxlen, hgap=2, vgap=2)
            for button in all_widgets[section]:
                bsizer.Add(button, flag=wx.ALL, border=1)
            sizer.Add(bsizer)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_CLOSE, self.cleanup)

        # the style for the property and tree frames
        frame_style = wx.DEFAULT_FRAME_STYLE
        frame_tool_win = config.preferences.frame_tool_win
        if frame_tool_win:
            frame_style |= wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT
            frame_style &= ~wx.MINIMIZE_BOX
            if wx.Platform != '__WXGTK__':
                frame_style |= wx.FRAME_TOOL_WINDOW

        # set window geometry
        main_geometry = None
        if config.preferences.remember_geometry:
            main_geometry = config.preferences.get_geometry('main')
            if isinstance(main_geometry, tuple):
                main_geometry = wx.Rect(*main_geometry)
        if not main_geometry:
            main_geometry = wx.Rect()
            main_geometry.TopLeft = wx.Display().GetClientArea().GetTopLeft()
            main_geometry.Size = (-1, -1)
        self._set_geometry(self, main_geometry)
        self.Show()
        main_geometry.Size = self.GetSize()

        # create the property and the tree frame
        self.create_property_panel(frame_style, icon, main_geometry)
        self.create_tree_frame(frame_style, icon, main_geometry)
        common.property_panel = self.property_frame

        # last visited directory, used on GTK for wxFileDialog
        self.cur_dir = config.preferences.open_save_path

        # set a drop target for us...
        self._droptarget = clipboard.FileDropTarget(self)
        self.SetDropTarget(self._droptarget)
        #self.tree_frame.SetDropTarget(self._droptarget)
        #self.property_frame.SetDropTarget(self._droptarget)

        # ALB 2004-10-15, autosave support...
        self.autosave_timer = None
        if config.preferences.autosave:
            self.autosave_timer = wx.Timer(self, -1)
            self.Bind(wx.EVT_TIMER, self.on_autosave_timer, self.autosave_timer)
            self.autosave_timer.Start( int(config.preferences.autosave_delay) * 1000 )

        self.create_statusbar()  # create statusbar for display of messages

        self.property_frame.SetAcceleratorTable(self.accel_table)
        self.tree_frame.SetAcceleratorTable(self.accel_table)

        self.Raise()

        # disable autosave checks during unittests
        if not getattr(sys, '_called_from_test', False):
            if common.check_autosaved(None):
                res = wx.MessageBox(
                    _('There seems to be auto saved data from last wxGlade session: do you want to restore it?'),
                    _('Auto save detected'), style=wx.ICON_QUESTION | wx.YES_NO)
                if res == wx.YES:
                    filename = common.get_name_for_autosave()
                    if self._open_app(filename, add_to_history=False):
                        self.cur_dir = os.path.dirname(filename)
                        common.app_tree.app.saved = False
                        common.app_tree.app.filename = None
                        self.user_message(_('Auto save loaded'))
                common.remove_autosaved()

    # menu and actions #################################################################################################
    def create_menu(self, parent):
        menu_bar = wx.MenuBar()

        compat.wx_ToolTip_SetDelay(1000)
        compat.wx_ToolTip_SetAutoPop(30000)

        append_menu_item = misc.append_menu_item

        # File menu
        file_menu = wx.Menu(style=wx.MENU_TEAROFF)

        NEW = append_menu_item(file_menu, -1, _("&New\tCtrl+N"), wx.ART_NEW)
        misc.bind_menu_item(self, NEW, self.new_app)

        item = append_menu_item(file_menu, -1, _("New from &Template...\tShift+Ctrl+N"))
        misc.bind_menu_item(self, item, self.new_app_from_template)

        OPEN = append_menu_item(file_menu, -1, _("&Open...\tCtrl+O"), wx.ART_FILE_OPEN)
        misc.bind_menu_item(self, OPEN, self.open_app)

        SAVE = append_menu_item(file_menu, -1, _("&Save\tCtrl+S"), wx.ART_FILE_SAVE)
        misc.bind_menu_item(self, SAVE, self.save_app)

        SAVE_AS = append_menu_item(file_menu, -1, _("Save As...\tShift+Ctrl+S"), wx.ART_FILE_SAVE_AS)
        misc.bind_menu_item(self, SAVE_AS, self.save_app_as)

        item = append_menu_item(file_menu, -1, _("Save As Template..."))
        misc.bind_menu_item(self, item, self.save_app_as_template)

        file_menu.AppendSeparator() # ----------------------------------------------------------------------------------

        item = append_menu_item(file_menu, wx.ID_REFRESH, _("&Refresh Preview\tF5"))
        misc.bind_menu_item(self, item, self.preview)

        GENERATE_CODE = append_menu_item(file_menu, -1, _("&Generate Code\tCtrl+G"), wx.ART_EXECUTABLE_FILE)
        misc.bind_menu_item(self, GENERATE_CODE, lambda: common.app_tree.app.generate_code())

        file_menu.AppendSeparator() # ----------------------------------------------------------------------------------

        item = append_menu_item(file_menu, -1, _("&Import from XRC..."))
        misc.bind_menu_item(self, item, self.import_xrc)

        file_menu.AppendSeparator() # ----------------------------------------------------------------------------------

        EXIT = append_menu_item(file_menu, -1, _('E&xit\tCtrl+Q'), wx.ART_QUIT)
        misc.bind_menu_item(self, EXIT, self.Close)

        menu_bar.Append(file_menu, _("&File"))

        # View menu
        view_menu = wx.Menu(style=wx.MENU_TEAROFF)

        TREE = append_menu_item(view_menu, -1, _("Show &Tree\tF2"))
        misc.bind_menu_item(self, TREE, self.show_tree)

        PROPS = append_menu_item(view_menu, -1, _("Show &Properties\tF3"))
        misc.bind_menu_item(self, PROPS, self.show_props_window)

        RAISE = append_menu_item(view_menu, -1, _("&Raise All\tF4"))
        misc.bind_menu_item(self, RAISE, self.raise_all)

        view_menu.AppendSeparator() # ----------------------------------------------------------------------------------

        item = append_menu_item(view_menu, -1, _('Template Manager...'))
        misc.bind_menu_item(self, item, self.manage_templates)

        view_menu.AppendSeparator() # ----------------------------------------------------------------------------------

        item = append_menu_item(view_menu, wx.ID_PREFERENCES, _('Preferences...'))
        misc.bind_menu_item(self, item, self.edit_preferences)

        menu_bar.Append(view_menu, _("&View"))

        # Help menu
        help_menu = wx.Menu(style=wx.MENU_TEAROFF)

        MANUAL = append_menu_item(help_menu, -1, _('Manual\tF1'), wx.ART_HELP)
        misc.bind_menu_item(self, MANUAL, self.show_manual)
        item = append_menu_item(help_menu, -1, _('Tutorial'))
        misc.bind_menu_item(self, item, self.show_tutorial)

        help_menu.AppendSeparator() # ----------------------------------------------------------------------------------

        item = append_menu_item(help_menu, wx.ID_ABOUT, _('About'))
        misc.bind_menu_item(self, item, self.show_about_box)

        menu_bar.Append(help_menu, _('&Help'))

        parent.SetMenuBar(menu_bar)
        # Mac tweaks...
        if wx.Platform == "__WXMAC__":
            if compat.IS_PHOENIX:
                wx.PyApp.SetMacAboutMenuItemId(wx.ID_ABOUT)
                wx.PyApp.SetMacPreferencesMenuItemId(wx.ID_PREFERENCES)
                wx.PyApp.SetMacExitMenuItemId(wx.ID_EXIT)
                wx.PyApp.SetMacHelpMenuTitleName(_('&Help'))
            else:
                wx.App_SetMacAboutMenuItemId(ABOUT_ID)
                wx.App_SetMacPreferencesMenuItemId(PREFS_ID)
                wx.App_SetMacExitMenuItemId(EXIT_ID)
                wx.App_SetMacHelpMenuTitleName(_('&Help'))

        # file history support
        self.file_history = wx.FileHistory(config.preferences.number_history)
        self.file_history.UseMenu(file_menu)
        files = common.load_history()
        files.reverse()
        for path in files:
            self.file_history.AddFileToHistory(path.strip())

        self.Bind(wx.EVT_MENU_RANGE, self.open_from_history, id=wx.ID_FILE1, id2=wx.ID_FILE9)

        self.accel_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('N'), NEW.GetId()),
            (wx.ACCEL_CTRL, ord('O'), OPEN.GetId()),
            (wx.ACCEL_CTRL, ord('S'), SAVE.GetId()),
            (wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('S'), SAVE_AS.GetId()),
            (wx.ACCEL_CTRL, ord('G'), GENERATE_CODE.GetId()),
            #(wx.ACCEL_CTRL, ord('I'), IMPORT_ID),
            (0, wx.WXK_F1, MANUAL.GetId()),
            (wx.ACCEL_CTRL, ord('Q'), EXIT.GetId()),
            (0, wx.WXK_F5, wx.ID_REFRESH),
            (0, wx.WXK_F2, TREE.GetId()),
            (0, wx.WXK_F3, PROPS.GetId()),
            (0, wx.WXK_F4, RAISE.GetId()),
            ])

    def open_from_history(self, event):
        if not self.ask_save():
            return
        pos = event.GetId() - wx.ID_FILE1
        filename = self.file_history.GetHistoryFile(pos)
        if not os.path.exists(filename):
            wx.MessageBox( _("The file %s doesn't exist.") % filename,
                           _('Information'), style=wx.CENTER | wx.ICON_INFORMATION | wx.OK )
            self.file_history.RemoveFileFromHistory(pos)
            common.remove_autosaved(filename)
            return
        if common.check_autosaved(filename):
            res = wx.MessageBox( _('There seems to be auto saved data for this file: do you want to restore it?'),
                                 _('Auto save detected'), style=wx.ICON_QUESTION | wx.YES_NO )
            if res == wx.YES:
                common.restore_from_autosaved(filename)
            else:
                common.remove_autosaved(filename)
        else:
            common.remove_autosaved(filename)

        if filename == common.app_tree.app.filename:
            # if we are re-loading the file, go the the previous position
            path = common.app_tree.get_selected_path()
        else:
            path = None

        self._open_app(filename)
        self.cur_dir = os.path.dirname(filename)
        if path is not None:
            common.app_tree.select_path(path)  # re-loaded file -> go to previous position

    # GUI elements: property frame, tree frame #########################################################################
    def create_property_panel(self, frame_style, icon, main_geometry):
        # create property editor frame
        self.property_frame = wxGladePropertyPanel(self, frame_style)
        self.property_frame.SetBackgroundColour( compat.wx_SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE) )
        self.property_frame.SetIcon(icon)

        # set geometry
        property_geometry = None
        if config.preferences.remember_geometry:
            property_geometry = config.preferences.get_geometry('properties')
            if isinstance(property_geometry, tuple):
                property_geometry = wx.Rect(*property_geometry)
        if not property_geometry:
            property_geometry = wx.Rect()
            property_geometry.Position = main_geometry.BottomLeft
            property_geometry.Size = (345, 350)
            # sometimes especially on GTK GetSize seems to ignore window decorations (bug still exists on wx3)
            if wx.Platform != '__WXMSW__': property_geometry.Y += 40
            # set size on Mac manually
            if wx.Platform == '__WXMAC__': property_geometry.Size = (345, 384)

        self._set_geometry(self.property_frame, property_geometry)
        self.property_frame.Show()

    def create_tree_frame(self, frame_style, icon, main_geometry):
        self.tree_frame = wx.Frame(self, -1, _('wxGlade: Tree'), style=frame_style, name='TreeFrame')
        self.tree_frame.SetIcon(icon)

        app = application.Application()
        common.app_tree = WidgetTree(self.tree_frame, app)
        self.tree_frame.SetSize((300, 300))

        def on_tree_frame_close(event):
            #menu_bar.Check(TREE_ID, False)
            self.tree_frame.Hide()
        self.tree_frame.Bind(wx.EVT_CLOSE, on_tree_frame_close)

        # set geometry
        tree_geometry = None
        if config.preferences.remember_geometry:
            tree_geometry = config.preferences.get_geometry('tree')
            if isinstance(tree_geometry, tuple):
                tree_geometry = wx.Rect(*tree_geometry)
        if not tree_geometry:
            tree_geometry = wx.Rect()
            tree_geometry.Position = main_geometry.TopRight
            tree_geometry.Size = (250, 350)
            # sometimes especially on GTK GetSize seems to ignore window decorations (bug still exists on wx3)
            if wx.Platform != '__WXMSW__':
                tree_geometry.X += 10
        self._set_geometry(self.tree_frame, tree_geometry)
        self.tree_frame.Show()

    def on_autosave_timer(self, event):
        res = common.autosave_current()
        if res == 2:
            self.user_message(_("Auto saving... done"))
        elif not res:
            self.autosave_timer.Stop()
            config.preferences.autosave = False
            self._logger.info(_('Disable autosave function permanently'))
            wx.MessageBox(
                _('The autosave function failed. It has been disabled\n'
                  'permanently due to this error. Use the preferences\n'
                  'dialog to re-enable this functionality.\n'
                  'The details have been written to the wxGlade log file\n\n'
                  'The log file is: %s' % config.log_file ),
                _('Autosave Failed'), wx.OK | wx.CENTRE | wx.ICON_ERROR )

    def edit_preferences(self):
        dialog = preferencesdialog.wxGladePreferences(config.preferences)
        if dialog.ShowModal() == wx.ID_OK:
            wx.MessageBox( _('Changes will take effect after wxGlade is restarted'),
                           _('Preferences saved'), wx.OK|wx.CENTRE|wx.ICON_INFORMATION )
            dialog.set_preferences()
        dialog.Destroy()

    def preview(self):
        """Generate preview of the current loaded project.
        
        A preview can be triggered by keyboard shortcut or by pressing the preview button.
        The preview can be triggered for all selected widgets.
        This doesn't mean that the widget is opened for editing."""

        if not common.app_tree.cur_widget or isinstance(common.app_tree.cur_widget, application.Application):
            preview_widget = common.app_tree.root.children[0].widget
        else:
            preview_widget = misc.get_toplevel_widget(common.app_tree.cur_widget)

        if preview_widget is None: return

        if preview_widget.preview_widget:
            # preview is already active: close and re-generate
            preview_widget.preview_widget.Close()
            wx.CallAfter(preview_widget.preview, None)
        else:
            preview_widget.preview(None)

    def show_tree(self):
        self.tree_frame.Show()
        self.tree_frame.Raise()
        common.app_tree.SetFocus()

    def show_props_window(self):
        self.property_frame.Show()
        self.property_frame.Raise()
        try:
            c = self.property_frame.GetSizer().GetChildren()
            if c: c[0].GetWindow().SetFocus()
        except (AttributeError, TypeError):
            self.property_frame.SetFocus()

    def raise_all(self):
        # when one window is raised, raise all
        children = self.GetChildren()
        for child in children:
            child = misc.get_toplevel_parent(child)
            if child.IsShown() and child.GetTitle(): child.Raise()
        self.Raise()

    # status bar for message display ###################################################################################
    def create_statusbar(self):
        self.CreateStatusBar(1)
        # ALB 2004-10-15  statusbar timer: delete user message after some time
        self.clear_sb_timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.on_clear_sb_timer, self.clear_sb_timer)

    def user_message(self, msg):
        # display a message, but clear it after a few seconds again
        sb = self.GetStatusBar()
        if sb:
            sb.SetStatusText(msg)
            self.clear_sb_timer.Start(5000, True)

    def on_clear_sb_timer(self, event):
        sb = self.GetStatusBar()
        if sb: sb.SetStatusText("")
    ####################################################################################################################

    def ask_save(self):
        """checks whether the current app has changed and needs to be saved:
        if so, prompts the user;
        returns False if the operation has been cancelled"""
        if not common.app_tree.app.saved:
            ok = wx.MessageBox(_("Save changes to the current app?"),
                               _("Confirm"), wx.YES_NO|wx.CANCEL|wx.CENTRE|wx.ICON_QUESTION)
            if ok == wx.YES:
                self.save_app()
            return ok != wx.CANCEL
        return True

    def new_app(self):
        "creates a new wxGlade project"
        if self.ask_save():
            common.app_tree.clear()
            common.app_tree.app.filename = None
            common.app_tree.app.saved = True
            self.user_message("")
            common.remove_autosaved()
            if config.preferences.autosave and self.autosave_timer is not None:
                self.autosave_timer.Start()

    def new_app_from_template(self):
        "creates a new wxGlade project from an existing template file"
        if not self.ask_save(): return
        infile = template.select_template()
        if infile:
            self._open_app(infile, add_to_history=False)
            common.app_tree.app.template_data = None

    def open_app(self):
        """loads a wxGlade project from an xml file
        NOTE: this is very slow and needs optimisation efforts
        NOTE2: the note above should not be True anymore :) """
        if not self.ask_save():
            return
        default_path = os.path.dirname(common.app_tree.app.filename or "") or self.cur_dir
        infile = wx.FileSelector(_("Open file"),
                                   wildcard="wxGlade files (*.wxg)|*.wxg|wxGlade Template files (*.wgt)|*.wgt|"
                                            "XML files (*.xml)|*.xml|All files|*",
                                   flags=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, default_path=default_path)
        if not infile: return
        if common.check_autosaved(infile):
            if wx.MessageBox( _("There seems to be auto saved data for this file: do you want to restore it?"),
                              _("Auto save detected"), style=wx.ICON_QUESTION|wx.YES_NO ) == wx.YES:
                common.restore_from_autosaved(infile)
            else:
                common.remove_autosaved(infile)
        if infile == common.app_tree.app.filename:
            # if we are re-loading the file, go the the previous position
            path = common.app_tree.get_selected_path()
        else:
            path = None
        self._open_app(infile)
        self.cur_dir = os.path.dirname(infile)

        if path is not None:
            common.app_tree.select_path(path)  # re-loaded file -> go to previous position

    def _open_app(self, filename, use_progress_dialog=True, add_to_history=True):
        "Load a new wxGlade project"

        error_msg = None
        infile = None
        old_dir = os.getcwd()

        common.app_tree.app.filename = filename

        start = time.clock()
        common.app_tree.clear()

        # disable auto-expansion of nodes
        common.app_tree.auto_expand = False

        try:
            try:
                self._logger.info( _('Read wxGlade project from file "%s"'), filename )
                os.chdir(os.path.dirname(filename))
                # decoding will done automatically by SAX XML library
                if compat.PYTHON2:
                    infile = open(filename)
                else:
                    infile = open(filename, "r", encoding="UTF8")

                if use_progress_dialog and config.preferences.show_progress:
                    p = ProgressXmlWidgetBuilder(input_file=infile)
                else:
                    p = XmlWidgetBuilder()

                p.parse(infile)
            except (EnvironmentError, SAXParseException, XmlParsingError) as msg:
                if config.debugging: raise
                if filename:
                    error_msg = _("Error loading file %s: %s") % (misc.wxstr(filename), misc.wxstr(msg))
                else:
                    error_msg = _("Error loading from a file-like object: %s") % misc.wxstr(msg)
            except Exception as inst:
                if config.debugging: raise
                if filename:
                    fn = os.path.basename(filename).encode('ascii','replace')
                    msg = _('loading file "%s"') % fn
                else:
                    msg = _('loading from a file-like object')
                bugdialog.Show(msg, inst)
        finally:
            if infile and filename:
                infile.close()

            if error_msg:
                common.app_tree.clear()
                common.app_tree.app.saved = True
                common.app_tree.auto_expand = True  # re-enable auto-expansion of nodes

                os.chdir(old_dir)

                wx.MessageBox(error_msg, _('Error'), wx.OK | wx.CENTRE | wx.ICON_ERROR)

                return False

        misc.set_focused_widget(common.app_tree.root.widget, force=True)

        common.app_tree.auto_expand = True  # re-enable auto-expansion of nodes

        common.app_tree.expand()
        if common.app_tree.app.is_template:
            self._logger.info(_("Template loaded"))
            common.app_tree.app.template_data = template.Template(filename)
            common.app_tree.app.filename = None

        end = time.clock()
        self._logger.info(_('Loading time: %.5f'), end - start)

        common.app_tree.app.saved = True
        common.property_panel.Raise()

        if hasattr(self, 'file_history') and filename is not None and add_to_history and \
           (not common.app_tree.app.is_template):
            self.file_history.AddFileToHistory(misc.wxstr(filename))

        if config.preferences.autosave and self.autosave_timer is not None:
            self.autosave_timer.Start()

        duration = end - start
        if filename:
            self.user_message( _("Loaded %s in %.2f seconds") % (misc.wxstr(os.path.basename(filename)), duration) )
        else:
            self.user_message( _("Loaded in %.2f seconds") % duration )

        return True

    def save_app(self):
        "saves a wxGlade project onto an xml file"
        if not common.app_tree.app.filename or common.app_tree.app.is_template:
            self.save_app_as()
        else:
            # check whether we are saving a template
            ext = os.path.splitext(common.app_tree.app.filename)[1].lower()
            if ext == ".wgt":
                common.app_tree.app.is_template = True
            self._save_app(common.app_tree.app.filename)

    def _save_app(self, filename):
        try:
            obuffer = compat.StringIO()
            common.app_tree.write(obuffer)
            common.save_file(filename, obuffer.getvalue(), 'wxg')
        except EnvironmentError as inst:
            common.app_tree.app.saved = False
            bugdialog.ShowEnvironmentError(_('Saving this project failed'), inst)
        except Exception as inst:
            common.app_tree.app.saved = False
            fn = os.path.basename(filename).encode('ascii', 'replace')
            bugdialog.Show(_('Save File "%s"') % fn, inst)
        else:
            common.app_tree.app.saved = True
            common.remove_autosaved()
            if config.preferences.autosave and self.autosave_timer is not None:
                self.autosave_timer.Start()
            self.user_message( _("Saved %s") % os.path.basename(filename) )

    def save_app_as(self):
        "saves a wxGlade project onto an xml file chosen by the user"
        # both flags occurs several times
        fn = wx.FileSelector( _("Save project as..."),
                              wildcard="wxGlade files (*.wxg)|*.wxg|wxGlade Template files (*.wgt) |*.wgt|"
                              "XML files (*.xml)|*.xml|All files|*",
                              flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                              default_filename=common.app_tree.app.filename or self.cur_dir)
        if not fn: return

        # check for file extension and add default extension if missing
        ext = os.path.splitext(fn)[1].lower()
        if not ext:
            fn = "%s.wxg" % fn

        common.app_tree.app.filename = fn
        #remove the template flag so we can save the file.
        common.app_tree.app.properties["is_template"].set(False)

        self.save_app()
        self.cur_dir = os.path.dirname(fn)
        self.file_history.AddFileToHistory(fn)

    def save_app_as_template(self):
        "save a wxGlade project as a template"
        data = getattr(common.app_tree.app, 'template_data', None)
        outfile, data = template.save_template(data)
        if outfile:
            common.app_tree.app.properties["is_template"].set(True)
            common.app_tree.app.template_data = data
            self._save_app(outfile)

    def cleanup(self, event):
        if self.ask_save():
            # first, let's see if we have to save the geometry...
            prefs = config.preferences
            if prefs.remember_geometry:
                prefs.set_geometry('main', self._get_geometry(self))
                prefs.set_geometry('tree', self._get_geometry(self.tree_frame))
                prefs.set_geometry('properties', self._get_geometry(self.property_frame))
                prefs.changed = True
            common.app_tree.clear()
            try:
                common.save_preferences()
            except Exception as e:
                wx.MessageBox( _('Error saving preferences:\n%s') % e,
                               _('Error'), wx.OK|wx.CENTRE|wx.ICON_ERROR )
            #self._skip_activate = True
            self.property_frame.Destroy()
            self.property_frame = None
            self.tree_frame.Destroy()
            self.tree_frame = None
            self.Destroy()
            common.remove_autosaved()  # ALB 2004-10-15
            wx.CallAfter(wx.GetApp().ExitMainLoop)

    def show_about_box(self):
        "show the about dialog;  @see: L{about.wxGladeAboutBox}"
        about_box = about.wxGladeAboutBox()
        about_box.ShowModal()
        about_box.Destroy()

    def show_manual(self):
        "Show the wxGlade user manual"
        #self._show_html(config.manual_file)
        self._show_html(config.tutorial_file)  # at the moment there's no new manual

    def show_tutorial(self):
        "Show the wxGlade tutorial"
        self._show_html(config.tutorial_file)

    def _show_html(self, html_file):
        "Open browser and show an HTML documentation"

        if wx.Platform == "__WXMAC__":
            os.system(r'open -a Help\ Viewer.app %s' % html_file)
        else:
            import webbrowser
            import threading
            # ALB 2004-08-15: why did this block the program????? (at least on linux - GTK)

            def go():
                webbrowser.open_new(html_file)
            t = threading.Thread(target=go)
            t.setDaemon(True)
            t.start()

    def show_and_raise(self):
        self.property_frame.Show()  # self.GetMenuBar().IsChecked(self.PROPS_ID))
        self.tree_frame.Show()      # self.GetMenuBar().IsChecked(self.TREE_ID))
        self.property_frame.Raise()
        self.tree_frame.Raise()
        self.Raise()

    def hide_all(self):
        self.tree_frame.Hide()
        self.property_frame.Hide()

    def import_xrc(self):
        import xrc2wxg

        if not self.ask_save():
            return

        infilename = wx.FileSelector( _("Import file"), wildcard="XRC files (*.xrc)" "|*.xrc|All files|*",
                                      flags=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, default_path=self.cur_dir)
        if infilename:
            ibuffer = compat.StringIO()
            try:
                xrc2wxg.convert(infilename, ibuffer)

                # Convert UTF-8 returned by xrc2wxg.convert() to Unicode
                tmp = ibuffer.getvalue().decode('UTF-8')
                ibuffer = compat.StringIO()
                [ibuffer.write('%s\n' % line) for line in tmp.split('\n')]
                ibuffer.seek(0)

                self._open_app(ibuffer)
                common.app_tree.app.saved = False
            except Exception as inst:
                fn = os.path.basename(infilename).encode('ascii', 'replace')
                bugdialog.Show(_('Import File "%s"') % fn, inst)

    def manage_templates(self):
        to_edit = template.manage_templates()
        if to_edit is not None and self.ask_save():
            # edit the template
            # TODO, you still need to save it manually...
            self._open_app(to_edit, add_to_history=False)
            wx.MessageBox( _("To save the changes to the template, edit the GUI as usual,\n"
                             "and then click File->Save As Template..."),
                           _("Information"), style=wx.OK|wx.ICON_INFORMATION )

    def _set_geometry(self, win, geometry):
        "Set position and/or size of widget; geometry must be wx.Point or wx.Rect"
        assert isinstance(geometry, (wx.Point, wx.Rect))
        if not geometry: return
        client_area = wx.Display().ClientArea

        if isinstance(geometry, wx.Point):
            if client_area.Contains(geometry):
                win.SetPosition(geometry)
        else:
            if client_area.Contains(geometry.TopLeft):
                if compat.IS_CLASSIC:
                    win.SetDimensions(*geometry.Get())
                else:
                    win.SetSize(*geometry.Get())

    def _get_geometry(self, widget):
        "Return widget position and size as wx.Rect"
        pos_size = widget.Rect
        return pos_size.Get()  # a tuple




class wxGlade(wx.App):
    """wxGlade application class
    
    @ivar _exception_orig: Reference to original implementation of logging.exception()"""

    def OnInit(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        # replace text based exception handler by a graphical exception dialog
        sys.excepthook = self.graphical_exception_handler

        # use graphical implementation to show caught exceptions
        self._exception_orig = logging.exception
        logging.exception = self.exception

        # needed for wx >= 2.3.4 to disable wxPyAssertionError exceptions
        self.SetAssertMode(0)

        common.init_preferences()
        if config.preferences.log_debug_info:
            log.setDebugLevel()

            # enable Python faulthandler to dump a traceback on SIGSEGV, SIGFPE, SIGABRT, SIGBUS, and SIGILL signals.
            try:
                import faulthandler
                faulthandler.enable()
                logging.info(_('Python faulthandler found and activated'))
            except ImportError:
                logging.debug(_('Python faulthandler not found'))
            except RuntimeError as details:
                logging.info(_('Python faulthandler found, but enabling failed: %s'), details)
            except Exception as details:
                logging.info(_('Generic error during faulthandler initialisation: %s'), details)

        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)  # avoid PyAssertionErrors
        compat.wx_ArtProviderPush(wxGladeArtProvider())

        frame = wxGladeFrame()
        self.SetTopWindow(frame)
        self.SetExitOnFrameDelete(True)

        self.Bind(wx.EVT_IDLE, self.OnIdle)

        return True

    def OnExit(self):
        "Restore original exception handler and logging.exception() on exit"
        sys.excepthook = sys.__excepthook__
        logging.exception = self._exception_orig
        return 0

    def OnIdle(self, event):
        "Idle tasks - currently show error messages only;  @see: L{show_msgdialog()}"
        self.show_msgdialog()
        event.Skip()

    def show_msgdialog(self):
        """\
        Check for log messages and show them

        @see: L{main.wxGlade.OnIdle()}
        @see: L{log.getBufferAsList()}
        @see: L{msgdialog.MessageDialog}
        """
        log_msg = log.getBufferAsString()
        if not log_msg:
            return

        # initialise message dialog
        msg_dialog = msgdialog.MessageDialog(None, -1, "")
        msg_dialog.msg_list.InsertColumn(0, "")

        # clear dialog and show new messages
        msg_dialog.msg_list.Freeze()
        msg_dialog.msg_list.DeleteAllItems()
        for line in log_msg.split('\n'):
            msg_dialog.msg_list.Append([line, ])
        msg_dialog.msg_list.SetColumnWidth(0, -1)
        msg_dialog.msg_list.Thaw()
        msg_dialog.ShowModal()
        msg_dialog.Destroy()

    def graphical_exception_handler(self, exc_type, exc_value, exc_tb):
        """\
        Show detailed information about uncaught exceptions in
        L{bugdialog.BugReport}.

        The shown exception will be logged to the log file in parallel.

        The exception information will be cleared after the bug dialog has
        closed.

        @param exc_type:  Type of the exception (normally a class object)
        @param exc_value: The "value" of the exception
        @param exc_tb:    Call stack of the exception

        @see: L{bugdialog.BugReport()}
        @see: L{bugdialog.Show()}
        """
        bugdialog.ShowEI(exc_type, exc_value, exc_tb)
        if compat.PYTHON2: sys.exc_clear()

    def exception(self, msg, *args, **kwargs):
        """\
        Graphical replacement of C{logging.exception()}.

        All exception details logged with C{logging.exception()} will be shown
        in L{bugdialog.BugReport}.

        The shown exception will be logged to the log file ding.

        The exception information will be cleared after the bug dialog has
        closed.

        @param msg: Short description of the exception
        @type msg:  str

        @see: L{bugdialog.BugReport}
        @see: L{bugdialog.ShowEI()}
        """
        if args:
            try:
                msg = msg % args
            except TypeError:
                log.exception_orig(_('Wrong format of a log message'))

        (exc_type, exc_value, exc_tb) = sys.exc_info()
        bugdialog.ShowEI(exc_type, exc_value, exc_tb, msg)
        if compat.PYTHON2: sys.exc_clear()



def main(filename=None):
    "if filename is not None, loads it"
    logging.info(_("Using wxPython %s"), config.wx_version)
    app = wxGlade()
    if filename is not None:
        win = app.GetTopWindow()
        win._open_app(filename, False)
        win.cur_dir = os.path.dirname(filename)
    app.MainLoop()