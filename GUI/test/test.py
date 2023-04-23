#!/usr/bin/env python3
#! -*- coding: utf-8 -*-


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

if hasattr(Gtk, 'version'):
    print('GTK TRUE')
else:
    print('False')

