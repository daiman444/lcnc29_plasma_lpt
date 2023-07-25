#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import hal
import hal_glib
import linuxcnc
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk

from gladevcp.persistence import IniFile  # we use this one to save the states of the widgets on shut down and restart
from gladevcp.persistence import widget_defaults
from gladevcp.persistence import select_widgets
from gmoccapy import preferences
from gmoccapy import getiniinfo

INIPATH = os.environ.get('INI_FILE_NAME', '/dev/null')

class Panel:
    def __init__(self, halcomp, builder, useropts):
        self.lcnc = linuxcnc
        self.builder = builder
        self.b_g_o = builder.get_object
        self.inifile = self.lcnc.ini(INIPATH)
        self.defs = {IniFile.vars: {
            "pierce_hghtval": 7.0,
            "pierce_hghtmax": 15.0,
            "pierce_hghtmin": 1.0,
            "pierce_hghtincr": 0.5,
        }
            
        }
        


def get_handlers(halcomp, builder, useropts):
    return [Panel(halcomp, builder, useropts)]



