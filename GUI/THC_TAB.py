#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import hal
import hal_glib
import linuxcnc
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk

class Panel:
    def __init__(self, halcomp, builder, useropts):
        self.builder = builder
        self.b_g_o = builder.get_object
        self.b_g_o('window1').set_sensitive(False)
        self.b_g_o('label10').set_label('huyamba')

def get_handlers(halcomp, builder, useropts):
    return [Panel(halcomp, builder, useropts)]



