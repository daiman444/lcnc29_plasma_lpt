#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import hal
import hal_glib
import linuxcnc
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
import defaults

from gi.repository import Gtk
from gi.repository import Gdk

from gladevcp.persistence import IniFile  # we use this one to save the states of the widgets on shut down and restart
from gladevcp.persistence import widget_defaults
from gladevcp.persistence import select_widgets
from gmoccapy import preferences
from gmoccapy import getiniinfo

GSTAT = hal_glib.GStat()
STATUS = linuxcnc.stat()
INIPATH = os.environ.get('INI_FILE_NAME', '/dev/null')

class Panel:
    def __init__(self, halcomp, builder, useropts):
        self.lcnc = linuxcnc
        self.command = linuxcnc.command()
        self.builder = builder
        self.b_g_o = builder.get_object
        self.inifile = self.lcnc.ini(INIPATH)
        self.defs = {IniFile.vars: defaults.defaults}   
        self.defs = self.defs[IniFile.vars]    
        self.b_g_o('main_box').set_sensitive(False)
        
        GSTAT.connect('all-homed', lambda w: self.all_homed('homed'))
        GSTAT.connect('mode-auto', lambda w: self.mode_change('auto'))
        GSTAT.connect('mode-manual', lambda w: self.mode_change('manual'))
        GSTAT.connect('mode-mdi', lambda w: self.mode_change('mdi'))
        
        self.b_g_o('gotozero').connect('pressed', self.go_to_zero, 'G90 G0 Z30 X0 Y0 F800')
        self.b_g_o('zero-xyz').connect('pressed', self.m_d_i, 'G92 X0 Y0 Z0')
        self.b_g_o('zero-x').connect('pressed', self.m_d_i, 'G92 X0')
        self.b_g_o('zero-y').connect('pressed', self.m_d_i, 'G92 Y0')
        self.b_g_o('zero-z').connect('pressed', self.m_d_i, 'G92 Z0')
        self.b_g_o('gotoend').connect('pressed', self.gotoend)
        self.b_g_o('set_coord_x').connect('pressed', self.setcoord, 'x')
        self.b_g_o('set_coord_y').connect('pressed', self.setcoord, 'y')
        
        # feed direction
        self.pin_feed_dir_plus = hal_glib.GPin(halcomp.newpin('feed-dir-plus', hal.HAL_BIT, hal.HAL_IN))
        self.pin_feed_dir_plus.connect('value-changed', self.feed_direction_change, 1)

        self.pin_feed_dir_minus = hal_glib.GPin(halcomp.newpin('feed-dir-minus', hal.HAL_BIT, hal.HAL_IN))
        self.pin_feed_dir_minus.connect('value-changed', self.feed_direction_change, -1)

        self.pin_feed_dir = hal_glib.GPin(halcomp.newpin('feed-dir', hal.HAL_FLOAT, hal.HAL_OUT))
        self.pin_feed_dir.value = 1

        self.btn_feed_dir_plus = builder.get_object('btn_feed_plus')
        self.btn_feed_dir_plus.connect('pressed', self.feed_direction_change, 1)
        self.btn_feed_dir_plus.set_sensitive(False)

        self.btn_feed_dir_minus = builder.get_object('btn_feed_minus')
        self.btn_feed_dir_minus.connect('pressed', self.feed_direction_change, -1)
        self.btn_feed_dir_minus.set_sensitive(True)

        self.lbl_feed_dir = self.builder.get_object('lbl_feed_dir')
        self.lbl_feed_dir.set_label('FWD')

        # declaring widgets as a list.
        # push-buttons list for change values:
        self.widgets_list = ['cor_vel', 'vel_tol', 'pierce_hght',
                             'jump_hght', 'pierce_del', 'cut_hght',
                             'stop_del', 'safe_z', 'z_speed',
                             'vsetup', 'freq_scale', 'arc_ok_min',
                             'arc_ok_max', 'periods', 'vtol', 
                             ]
        #list to set sensitive widgets on mode auto/mdi/manual
        self.widgets_in_mode = ['gotozero', 'gotoend', 'zero-xyz',
                                'zero-x', 'zero-y', 'zero-z',
                                'set_coord_x', 'txt_set_coord_x', 'set_coord_y',
                                'txt_set_coord_y', 'tb_plasma', 'tb_ox',
                                ]
 
 
    def mode_change(self, stat):
        STATUS.poll()
        mode = STATUS.task_mode
        self.b_g_o('label4').set_label("%s" % mode)
        if mode == linuxcnc.MODE_MDI or mode == linuxcnc.MODE_AUTO:
            for i in self.widgets_in_mode:
                self.b_g_o(i).set_sensitive(False)
        if mode == linuxcnc.MODE_MANUAL:
            for i in self.widgets_in_mode:
                self.b_g_o(i).set_sensitive(True)
                
    def all_homed(self, stat):
        if stat == 'homed':
            self.b_g_o('main_box').set_sensitive(True)
   
    def m_d_i(self, w, mdi=None):
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi(mdi)
        self.command.wait_complete()
        self.command.mode(linuxcnc.MODE_MANUAL)
        
    def go_to_zero(self, w, d=None):
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi(d)
        self.command.wait_complete([180])
        self.command.mode(linuxcnc.MODE_MANUAL)
        
    def gotoend(self, w, d=None):
        x_limit = self.inifile.find('AXIS_X', 'MIN_LIMIT')
        y_limit = self.inifile.find('AXIS_Y', 'MAX_LIMIT')
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi('G53 G00 Z0 ')
        self.command.mdi('G53 X{0} Y{1}'.format(x_limit, y_limit))
        self.command.wait_complete([180])
        self.command.mode(linuxcnc.MODE_MANUAL)

    def setcoord(self, widget, data=None):
        coord = self.builder.get_object('txt_set_coord_' + data).get_text()
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi('G92{0}{1}'.format(data, float(coord)))
        self.command.mode(linuxcnc.MODE_MANUAL)
        
    def feed_direction_change(self, widget, value):
        if isinstance(widget, hal_glib.GPin):
            if widget.get() is True:
                self.pin_feed_dir.value += self.defs['feed_directincr'] * value
        if isinstance(widget, gi.overrides.Gtk.Button):
            self.pin_feed_dir.value += self.defs['feed_directincr'] * value
        if self.pin_feed_dir.value >= self.defs['feed_directmax']:
            self.pin_feed_dir.value = self.defs['feed_directmax']
            self.btn_feed_dir_plus.set_sensitive(False)
            self.lbl_feed_dir.set_label('FWD')
        elif self.pin_feed_dir.value <= self.defs['feed_directmin']:
            self.pin_feed_dir.value = self.defs['feed_directmin']
            self.btn_feed_dir_minus.set_sensitive(False)
            self.lbl_feed_dir.set_label('BWD')
        else:
            self.btn_feed_dir_plus.set_sensitive(True)
            self.btn_feed_dir_minus.set_sensitive(True)
            self.lbl_feed_dir.set_label('STOP')
            

def get_handlers(halcomp, builder, useropts):
    return [Panel(halcomp, builder, useropts)]



