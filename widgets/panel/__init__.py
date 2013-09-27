"""
Panel widget module initialization

@copyright: 2002-2007 Alberto Griggio
@license: MIT (see license.txt) - THIS PROGRAM COMES WITH NO WARRANTY
"""

def initialize():
    import config
    import codegen
    codegen.initialize()
    if config.use_gui:
        import panel
        global EditTopLevelPanel; EditTopLevelPanel = panel.EditTopLevelPanel
        global EditPanel; EditPanel = panel.EditPanel
        return panel.initialize()
