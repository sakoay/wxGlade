"""\
Lisp generator functions for wxToggleButton objects

@copyright: 2002-2004 D. H. aka crazyinsomniac on sourceforge
@copyright: 2014 Carsten Grohmann
@license: MIT (see license.txt) - THIS PROGRAM COMES WITH NO WARRANTY
"""

import common
import wcodegen


class LispToggleButtonGenerator(wcodegen.LispWidgetCodeWriter):
    tmpl = '(setf %(name)s (%(klass)s_Create %(parent)s %(id)s ' \
           '%(label)s -1 -1 -1 -1 0))\n'
    has_setvalue = True

# end of class LispToggleButtonGenerator


def initialize():
    klass = 'wxToggleButton'
    common.class_names['EditToggleButton'] = klass
    common.register('lisp', klass, LispToggleButtonGenerator(klass))
