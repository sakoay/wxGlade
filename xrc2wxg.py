#!/usr/bin/env python2
"""
Converts an XRC resource file (in a format wxGlade likes, i.e. all windows
inside sizers, no widget unknown to wxGlade, ...) into a WXG file.

@copyright: 2002-2007 Alberto Griggio
@copyright: 2014-2016 Carsten Grohmann
@license: MIT (see LICENSE.txt) - THIS PROGRAM COMES WITH NO WARRANTY
"""

import logging
import xml.dom.minidom
import getopt
import os.path
import sys
import time

__version__ = '0.0.6'
_name = 'xrc2wxg'
"""\
Application name
"""

_default_props = {
    'bg': 'background',
    'content': 'choices',
    'enabled': 'disabled',
    'fg': 'foreground',
    'growablecols': 'growable_cols',
    'growablerows': 'growable_rows',
    'item': 'choice',
    'sashpos': 'sash_pos',
}
"""\
Mapping of default attribute names from XRC to WXG

@see: L{_class_props}
"""

_class_props = {
    'wxMenuItem': {
        'help': 'help_str',
    },
    'tool': {
        'bitmap': 'bitmap1',
        'tooltip': 'short_help',
        'longhelp': 'long_help',
        'toggle': 'type',
    }
}
"""\
Mapping of class specific attribute names from XRC to WXG.

The class names are XRC class names.

@see: L{_default_props}
"""

_counter_name = 1
"""\
Counter to create unique names
"""

_widgets = [
    'wxBitmapButton', 'wxBoxSizer', 'wxButton', 'wxCalendarCtrl',
    'wxCheckBox', 'wxCheckListBox', 'wxChoice', 'wxComboBox',
    'wxDatePickerCtrl', 'wxDialog', 'wxFlexGridSizer', 'wxFrame',
    'wxGauge', 'wxGrid', 'wxGridSizer', 'wxListBox', 'wxListCtrl',
    'wxMenuBar', 'wxMenu', 'wxNotebook', 'wxPanel', 'wxRadioBox',
    'wxRadioButton', 'wxScrolledWindow', 'wxSlider', 'wxSpinButton',
    'wxSpinCtrl', 'wxSplitterWindow', 'wxStaticBitmap', 'wxStaticBoxSizer',
    'wxStaticLine', 'wxStaticText', 'wxStatusBar', 'wxTextCtrl',
    'wxToggleButton', 'wxToolBar', 'wxTreeCtrl',
]
"""\
Supported widgets
"""

_special_class_names = [
    'notebookpage', 'separator', 'sizeritem', 'spacer', 'tool',
]
"""\
Widget names with special meaning
"""

_write_timestamp = True
"""\
Write a timestamp in the output file
"""


def get_child_elems(node):
    def ok(n):
        return n.nodeType == n.ELEMENT_NODE

    return filter(ok, node.childNodes)


def get_text_elems(node):
    def ok(n):
        return n.nodeType == n.TEXT_NODE

    return filter(ok, node.childNodes)


def convert(filename, output_file):
    """\
    Convert the given XRC file to a wxGlade file

    @note: The output content is UTF-8 encoded.

    @param filename: Source filename
    @type filename: str

    @param output_file: Filename, file or file-like object
    @type output_file:  str | StringIO
    """
    global _counter_name
    _counter_name = 1

    document = xml.dom.minidom.parse(filename)
    fix_fake_panels(document)
    set_base_classes(document)
    fix_default_properties(document)
    fix_class_properties(document)
    fix_widgets(document)
    fix_encoding(filename, document)
    if not hasattr(output_file, 'write'):
        output_file = open(output_file, 'wb')
        write_output(document, output_file)
        output_file.close()
    else:
        write_output(document, output_file)


def write_output(document, output):
    """\
    Writes an UTF-8 encoded pretty-printed XML copy of the given document to
    the output object.
    """
    dom_copy = xml.dom.minidom.Document()

    if _write_timestamp:
        msg = ' generated by %s %s on %s '%( _name, __version__, time.asctime() )
    else:
        msg = ' generated by xrc2wxg '

    comment = dom_copy.createComment(msg)
    dom_copy.appendChild(comment)
    dom_copy.appendChild(document.documentElement)

    pretty_xml = dom_copy.toprettyxml(indent='    ', encoding='UTF-8')
    for line in pretty_xml.splitlines():
        # ignore empty lines
        if not line.strip():
            continue
        output.write(line)
        output.write(b'\n')

    dom_copy.unlink()


def set_base_classes(document):
    for elem in document.getElementsByTagName('object'):
        klass = elem.getAttribute('class')
        if klass.startswith('wx'):
            elem.setAttribute('base', 'Edit' + klass[2:])
            name = elem.getAttribute('name')
            if not name:
                global _counter_name
                elem.setAttribute('name', 'object_%s' % _counter_name)
                _counter_name += 1


def fix_default_properties(document):
    """\
    Rename generic properties

    @see: L{_default_props}
    """
    # special case...
    for elem in document.getElementsByTagName('disabled'):
        elem.tagName = 'disabled_bitmap'

    # replace property names
    for prop in _default_props:
        for elem in document.getElementsByTagName(prop):
            elem.tagName = _default_props[prop]

            # invert property value after renaming from enabled to disabled
            if prop == "enabled":
                if elem.firstChild.data == u'0':
                    elem.firstChild.data = u'1'
                else:
                    elem.firstChild.data = u'0'

    document.documentElement.tagName = 'application'
    for attribute in ['version', 'xmlns']:
        if document.documentElement.hasAttribute(attribute):
            document.documentElement.removeAttribute(attribute)


def fix_class_properties(document):
    """\
    Rename class specific properties

    @see: L{_class_props}
    """
    for element in document.getElementsByTagName('object'):
        klass = element.getAttribute('class')
        if not klass or klass not in _class_props:
            continue
        for child in get_child_elems(element):
            old_tagname = child.tagName
            if old_tagname in _class_props[klass]:
                child.tagName = _class_props[klass][old_tagname]


def fix_widgets(document):
    fix_menubars(document)
    fix_toolbars(document)
    fix_custom_widgets(document)
    fix_sizeritems(document)
    fix_notebooks(document)
    fix_splitters(document)
    fix_spacers(document)
    fix_sliders(document)
    fix_scrolled_windows(document)
    fix_toplevel_names(document)
    fix_statusbar(document)


def fix_custom_widgets(document):
    for elem in document.getElementsByTagName('object'):
        klass = elem.getAttribute('class')
        if klass not in _widgets and klass not in _special_class_names:
            logging.warning('Unknown widget "%s" - fallback to generic '
                            'widget "CustomWidget"' % klass)
            elem.setAttribute('base', 'CustomWidget')
            args = document.createElement('arguments')
            for child in get_child_elems(elem):
                # if child is a 'simple' attribute, i.e
                # <child>value</child>, convert it to an 'argument'
                if len(child.childNodes) == 1 and \
                   child.firstChild.nodeType == child.TEXT_NODE:
                    arg = document.createElement('argument')
                    arg.appendChild(document.createTextNode(
                        child.tagName + ': ' + child.firstChild.data))
                    args.appendChild(arg)
                    # and remove it
                    elem.removeChild(child)
                    # otherwise, leave it where it is (it shouldn't hurt)
            elem.appendChild(args)


def fix_sizeritems(document):
    def issizeritem(node):
        return node.getAttribute('class') == 'sizeritem'

    def isobject(node):
        return node.tagName == 'object'

    for sitem in filter(issizeritem, document.getElementsByTagName('object')):
        for child in filter(isobject, get_child_elems(sitem)):
            sitem.appendChild(sitem.removeChild(child))
    fix_flag_property(document)


def fix_flag_property(document):
    for elem in document.getElementsByTagName('flag'):
        tmp = elem.firstChild.data.replace('CENTRE', 'CENTER')
        elem.firstChild.data = tmp.replace('GROW', 'EXPAND')
        if elem.firstChild.data.find('wxALIGN_CENTER_HORIZONTAL') < 0 and \
           elem.firstChild.data.find('wxALIGN_CENTER_VERTICAL') < 0:
            elem.firstChild.data = elem.firstChild.data.replace(
                'wxALIGN_CENTER', 'wxALIGN_CENTER_HORIZONTAL|'
                                  'wxALIGN_CENTER_VERTICAL')


def fix_menubars(document):
    def ismenubar(elem):
        return elem.getAttribute('class') == 'wxMenuBar'

    menubars = filter(ismenubar, document.getElementsByTagName('object'))
    for mb in menubars:
        fix_menus(document, mb)
        if mb.parentNode is not document.documentElement:
            mb_prop = document.createElement('menubar')
            mb_prop.appendChild(document.createTextNode('1'))
            mb.parentNode.insertBefore(mb_prop, mb)


def fix_menus(document, menubar):
    """\
    Rearrange the wxMenu elements

    All menus of a wxMenuBar have to span by <menus> and </menus>::
        <menus>
            <menu>
            ...
            </menu>
            <menu>
            ...
            </menu>
        </menus>
    """

    def ismenu(elem):
        return elem.getAttribute('class') == 'wxMenu'

    wxg_menus = document.createElement('menus')

    xrc_menus = filter(ismenu, get_child_elems(menubar))
    for menu in xrc_menus:
        try:
            label = [c for c in get_child_elems(menu)
                     if c.tagName == 'label'][0]
            label = label.firstChild.data
        except IndexError:
            label = ''
        new_menu = document.createElement('menu')
        new_menu.setAttribute('name', menu.getAttribute('name'))
        new_menu.setAttribute('label', label)
        fix_sub_menus(document, menu, new_menu)
        wxg_menus.appendChild(new_menu)
        menubar.removeChild(menu).unlink()

    menubar.appendChild(wxg_menus)


def fix_sub_menus(document, menu, new_menu):
    for child in get_child_elems(menu):
        klass = child.getAttribute('class')
        elem = document.createElement('')
        if klass == 'wxMenuItem':
            elem.tagName = 'item'
            name = document.createElement('name')
            name.appendChild(document.createTextNode(
                child.getAttribute('name')))
            elem.appendChild(name)
            for c in get_child_elems(child):
                elem.appendChild(c)
        elif klass == 'separator':
            elem.tagName = 'item'
            for name in 'label', 'id', 'name':
                e = document.createElement(name)
                e.appendChild(document.createTextNode('---'))
                elem.appendChild(e)
        elif klass == 'wxMenu':
            elem.tagName = 'menu'
            elem.setAttribute('name', child.getAttribute('name'))
            try:
                label = [c for c in get_child_elems(child) if
                         c.tagName == 'label'][0]
                label = label.firstChild.data
            except IndexError:
                label = ''
            elem.setAttribute('label', label)
            fix_sub_menus(document, child, elem)
        if elem.tagName:
            new_menu.appendChild(elem)


def fix_toolbars(document):
    def istoolbar(elem):
        return elem.getAttribute('class') == 'wxToolBar'

    toolbars = filter(istoolbar, document.getElementsByTagName('object'))
    for tb in toolbars:
        fix_tools(document, tb)
        if tb.parentNode is not document.documentElement:
            tb_prop = document.createElement('toolbar')
            tb_prop.appendChild(document.createTextNode('1'))
            tb.parentNode.insertBefore(tb_prop, tb)


def fix_tools(document, toolbar):
    tools = document.createElement('tools')
    for tool in [c for c in get_child_elems(toolbar) if
                 c.tagName == 'object']:
        if tool.getAttribute('class') == 'tool':
            new_tool = document.createElement('tool')
            tool_id = document.createElement('id')
            tool_id.appendChild(document.createTextNode(
                tool.getAttribute('name')))
            new_tool.appendChild(tool_id)
            for c in get_child_elems(tool):
                new_tool.appendChild(c)
            tools.appendChild(new_tool)
            toolbar.removeChild(tool).unlink()
        elif tool.getAttribute('class') == 'separator':
            new_tool = document.createElement('tool')
            tool_id = document.createElement('id')
            tool_id.appendChild(document.createTextNode('---'))
            new_tool.appendChild(tool_id)
            tools.appendChild(new_tool)
            toolbar.removeChild(tool).unlink()
        else:
            # some kind of control, unsupported at the moment, just remove it
            toolbar.removeChild(tool).unlink()
    toolbar.appendChild(tools)


def fix_notebooks(document):
    def ispage(node):
        return node.getAttribute('class') == 'notebookpage'

    def isnotebook(node):
        return node.getAttribute('class') == 'wxNotebook'

    for nb in filter(isnotebook, document.getElementsByTagName('object')):
        pages = filter(ispage, get_child_elems(nb))
        tabs = document.createElement('tabs')
        try:
            us = filter(lambda n: n.tagName == 'usenotebooksizer',
                        get_child_elems(nb))[0]
            nb.removeChild(us).unlink()
        except IndexError:
            pass
        for page in pages:
            tab = document.createElement('tab')
            obj = None
            for c in get_child_elems(page):
                if c.tagName == 'label':
                    tab.appendChild(c.firstChild)
                elif c.tagName == 'object':
                    tab.setAttribute('window', c.getAttribute('name'))
                    c.setAttribute('base', 'NotebookPane')
                    obj = c
            tabs.appendChild(tab)
            nb.replaceChild(obj, page)
        nb.insertBefore(tabs, nb.firstChild)


def fix_splitters(document):
    def issplitter(node):
        return node.getAttribute('class') == 'wxSplitterWindow'

    def ispane(node):
        return node.tagName == 'object'

    for sp in filter(issplitter, document.getElementsByTagName('object')):
        panes = filter(ispane, get_child_elems(sp))
        assert len(panes) <= 2, "Splitter window with more than 2 panes!"
        for i, pane in enumerate(panes):
            e = document.createElement('window_%s' % (i + 1))
            e.appendChild(document.createTextNode(pane.getAttribute('name')))
            sp.insertBefore(e, sp.firstChild)
        for orient in filter(lambda n: n.tagName == 'orientation',
                             get_child_elems(sp)):
            if orient.firstChild.data == 'vertical':
                orient.firstChild.data = 'wxVERTICAL'
            elif orient.firstChild.data == 'horizontal':
                orient.firstChild.data = 'wxHORIZONTAL'


def fix_fake_panels(document):
    def isframe(node):
        return node.getAttribute('class') == 'wxFrame'

    for frame in filter(isframe, document.getElementsByTagName('object')):
        for c in get_child_elems(frame):
            if c.tagName == 'object' and c.getAttribute('class') == 'wxPanel' \
                    and c.getAttribute('name') == '':
                elems = get_child_elems(c)
                if len(elems) == 1 and \
                   elems[0].getAttribute('class').find('Sizer') != -1:
                    frame.replaceChild(elems[0], c)


def fix_spacers(document):
    def isspacer(node):
        return node.getAttribute('class') == 'spacer'

    for spacer in filter(isspacer, document.getElementsByTagName('object')):
        spacer.setAttribute('name', 'spacer')
        spacer.setAttribute('base', 'EditSpacer')
        sizeritem = document.createElement('object')
        sizeritem.setAttribute('class', 'sizeritem')
        for child in get_child_elems(spacer):
            if child.tagName == 'size':
                w, h = [s.strip() for s in child.firstChild.data.split(',')]
                width = document.createElement('width')
                width.appendChild(document.createTextNode(w))
                height = document.createElement('height')
                height.appendChild(document.createTextNode(h))
                spacer.removeChild(child).unlink()
                spacer.appendChild(width)
                spacer.appendChild(height)
            else:
                sizeritem.appendChild(spacer.removeChild(child))
        spacer.parentNode.replaceChild(sizeritem, spacer)
        sizeritem.appendChild(spacer)


def fix_scrolled_windows(document):
    def isscrollwin(node):
        return node.getAttribute('class') == 'wxScrolledWindow'

    for sw in filter(isscrollwin, document.getElementsByTagName('object')):
        e = document.createElement('scrollable')
        e.appendChild(document.createTextNode('1'))
        sw.insertBefore(e, sw.firstChild)


def fix_toplevel_names(document):
    names = {}
    for widget in get_child_elems(document.documentElement):
        klass = widget.getAttribute('class')
        if not klass:
            continue  # don't add a new 'class' attribute if it doesn't exist
        if klass == 'wxPanel':
            widget.setAttribute('base', 'EditTopLevelPanel')
        klass_name = kn = klass.replace('wx', 'My')
        name = widget.getAttribute('name')
        i = 1
        while klass_name in names or klass_name == name:
            klass_name = kn + str(i)
            i += 1
        widget.setAttribute('class', klass_name)


def fix_sliders(document):
    def isslider(node):
        klass = node.getAttribute('class')
        return klass == 'wxSlider' or klass == 'wxSpinCtrl'

    for slider in filter(isslider, document.getElementsByTagName('object')):
        v1, v2 = 0, 100
        for child in get_child_elems(slider):
            if child.tagName == 'min':
                v1 = child.firstChild.data.strip()
                slider.removeChild(child).unlink()
            elif child.tagName == 'max':
                v2 = child.firstChild.data.strip()
                slider.removeChild(child).unlink()
        rng = document.createElement('range')
        rng.appendChild(document.createTextNode('%s, %s' % (v1, v2)))
        slider.appendChild(rng)


def fix_statusbar(document):
    """\
    Rearrange the wxStatusBar elements

    XRC format::

        <object class="wxStatusBar" name="Mp3_SB">
            <fields>2</fields>
            <widths>-2, -1</widths>
            <style>wxST_SIZEGRIP</style>
        </object>


    WXG format::

        <statusbar>1</statusbar>
        <object class="wxStatusBar" name="Mp3_SB" base="EditStatusBar">
            <fields>
                <field width="-2">Mp3_To_Ogg_statusbar</field>
                <field width="-1"></field>
            </fields>
            <style>wxST_SIZEGRIP</style>
        </object>
    """
    for statusbar in document.getElementsByTagName('object'):
        if statusbar.getAttribute('class') != 'wxStatusBar':
            continue

        fields = statusbar.getElementsByTagName('fields')
        widths = statusbar.getElementsByTagName('widths')

        new_fields = document.createElement('fields')

        if fields:
            fields_count = int(fields[0].firstChild.data)
        else:
            fields_count = 1

        if widths:
            widths_data = widths[0].firstChild.data
            widths_data = widths_data.split(',')
        else:
            widths_data = []

        if fields_count > len(widths_data):
            delta = fields_count - len(widths_data)
            widths_data += ["-1"] * delta

        for pos in range(fields_count):
            field = document.createElement('field')
            field.appendChild(document.createTextNode(''))
            field.setAttribute('width', widths_data[pos])
            new_fields.appendChild(field)

        # delete rearranged fields
        for field in fields:
            statusbar.removeChild(field).unlink()
        for width in widths:
            statusbar.removeChild(width).unlink()

        # add new created elements
        statusbar.appendChild(new_fields)

        # marker <statusbar>1</statusbar> to enable the statusbar within
        # wxGlade
        if statusbar.parentNode is not document.documentElement:
            statusbar_prop = document.createElement('statusbar')
            statusbar_prop.appendChild(document.createTextNode('1'))
            statusbar.parentNode.insertBefore(statusbar_prop, statusbar)


def fix_encoding(filename, document):
    # first try to find the encoding of the xml doc
    import re

    enc = re.compile(r'^\s*<\?xml\s+.*(encoding\s*=\s*"(.*?)").*\?>')
    tag = re.compile(r'<.+?>')
    for line in open(filename):
        match = re.match(enc, line)
        if match:
            document.documentElement.setAttribute('encoding', match.group(2))
            return
        elif re.match(tag, line):
            break

    # if it's not specified, try to find a child of the root called
    # 'encoding': I don't know why, but XRCed does this
    for child in document.documentElement.childNodes:
        if child.nodeType == child.ELEMENT_NODE and \
           child.tagName == 'encoding':
            if child.firstChild is not None and \
               child.firstChild.nodeType == child.TEXT_NODE:
                document.documentElement.setAttribute(
                    'encoding', child.firstChild.data)
            document.documentElement.removeChild(child)


def usage():
    msg = """\
usage: python %s OPTIONS <INPUT_FILE.xrc> [WXG_FILE]

OPTIONS:
  -d, --debug: debug mode, i.e. you can see the whole traceback of each error

If WXG_FILE is not given, it defaults to INPUT_FILE.wxg
    """ % _name
    print( msg)
    sys.exit(1)


def print_exception():
    msg = """\
An error occurred while trying to convert the XRC file.
\n
If you think this is a bug, or if you want to know more about the cause of the
error, run this script again in debug mode (-d switch). If you find a bug,
please report it to the mailing list (wxglade-general@lists.sourceforge.net),
or enter a bug report at the SourceForge bug tracker.

Please note that this doesn't handle ALL XRC files correctly, but only those
which already are in a format which wxGlade likes (this basically means that
every non-toplevel widget must be inside sizers, but there might be other
cases).
"""
    logging.exception(msg)
    sys.exit(1)


def main():
    try:
        options, args = getopt.getopt(sys.argv[1:], "d", ['debug'])
    except getopt.GetoptError:
        usage()
    if not args:
        usage()
    infilename = args[0]
    try:
        out_filename = args[1]
    except IndexError:
        out_filename = os.path.splitext(infilename)[0] + '.wxg'
    if not options:
        try:
            convert(infilename, out_filename)
        except:
            # catch the exception and print a nice message
            print_exception()
    else:  # if in debug mode, let the traceback be printed
        convert(infilename, out_filename)


if __name__ == '__main__':
    _name = os.path.basename(sys.argv[0])
    main()