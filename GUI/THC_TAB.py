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
        self.hglib = hal_glib
        self.hglib_pin = hal_glib.GPin
        self.halcomp = halcomp
        self.builder = builder
        self.b_g_o = builder.get_object
        self.inifile = self.lcnc.ini(INIPATH)
        self.defaults = {IniFile.vars: defaults.defaults}   
        self.defs = self.defaults[IniFile.vars]    
        self.b_g_o('main_box').set_sensitive(False)
        # thc section
        self.v_measured_pin = self.halcomp.newpin('volts_measured', hal.HAL_FLOAT, hal.HAL_IN)
        self.v_measured = self.halcomp['volts_measured']
        #self.b_g_o('lbl_v_mesured').set_label('%s' % self.halcomp['volts_measured'])
        self.info_upd()
        
        get_ini_info = getiniinfo.GetIniInfo()
        prefs = preferences.preferences(get_ini_info.get_preference_file_path())
        theme_name = prefs.getpref("gtk_theme", "Follow System Theme", str)
        if theme_name == "Follow System Theme":
            theme_name = Gtk.Settings.get_default().get_property("gtk-theme-name")
        Gtk.Settings.get_default().set_string_property("gtk-theme-name", theme_name, "")
        self.ini_filename = __name__ + ".var"
        self.ini = IniFile(self.ini_filename, self.defaults, self.builder)
        self.ini.restore_state(self)
        
        GSTAT.connect('all-homed', lambda w: self.all_homed('homed'))
        GSTAT.connect('mode-auto', lambda w: self.mode_change('auto'))
        GSTAT.connect('mode-manual', lambda w: self.mode_change('manual'))
        GSTAT.connect('mode-mdi', lambda w: self.mode_change('mdi'))
        GSTAT.connect('periodic', self.info_upd)
        
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
        
        # toggle buttons
        self.b_g_o('tb_plasma').connect('toggled', self.pb_changes, 'plasma')
        self.b_g_o('tb_ox').connect('toggled', self.pb_changes, 'ox')
        
        
        
        # declaring widgets as a list.
        # push-buttons list for change values:
        self.widgets_list = ['cor_vel', 'vel_tol', 'pierce_hght',
                             'pierce_del', 'jump_hght', 'cut_hght',
                             'stop_del', 'safe_z', 'z_speed',
                             'vsetup', 
                             ]
        
        #list to set sensitive widgets on mode auto/mdi/manual
        self.widgets_in_mode = ['gotozero', 'gotoend', 'zero-xyz',
                                'zero-x', 'zero-y', 'zero-z',
                                'set_coord_x', 'txt_set_coord_x', 'set_coord_y',
                                'txt_set_coord_y', 'tb_plasma', 'tb_ox',
                                ]
        
        # after widgets_list declaration star the widget initialisation cycle:
        for name in self.widgets_list:
            # declaring defaults values to display
            lbl = 'lbl_' + name
            btn_plus = 'btn_' + name + '_plus'
            btn_minus = 'btn_' + name + '_minus'
            val = name + 'val'
            max = name + 'max'
            min = name + 'min'
            self.b_g_o(lbl).set_label('%s' % self.defs[name + 'val'])

            # declaring push-button '_plus' and connection to method
            self.b_g_o(btn_plus).connect('pressed', self.widget_value_change, name, 1)
            if self.defs[val] == self.defs[max]:
                self.b_g_o(btn_plus).set_sensitive(False)

            # declaring push-button '_minus' and connection to method
            self.b_g_o(btn_minus).connect('pressed', self.widget_value_change, name, -1)
            if self.defs[val] == self.defs[min]:
                self.b_g_o(btn_minus).set_sensitive(False)

            # declaring hal pin
            self.hglib_pin(self.halcomp.newpin(name, hal.HAL_FLOAT, hal.HAL_OUT)).value = self.defs[name + 'val']


    def info_upd(self, **args):
        self.b_g_o('lbl_v_mesured').set_label('%s' % self.halcomp['volts_measured'])
        pass
    
    def mode_change(self, stat):
        STATUS.poll()
        mode = STATUS.task_mode
        self.b_g_o('info1').set_label("%s" % mode)
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

    def widget_value_change(self, widget, name, value):
        self.defs[name + 'val'] += self.defs[name + 'incr'] * value
        if self.defs[name + 'val'] >= self.defs[name + 'max']:
            self.defs[name + 'val'] = self.defs[name + 'max']
            self.b_g_o('btn_' + name + '_plus').set_sensitive(False)
        elif self.defs[name + 'val'] <= self.defs[name + 'min']:
            self.defs[name + 'val'] = self.defs[name + 'min']
            self.b_g_o('btn_' + name + '_minus').set_sensitive(False)
        else:
            self.b_g_o('btn_' + name + '_plus').set_sensitive(True)
            self.b_g_o('btn_' + name + '_minus').set_sensitive(True)
        if name == 'freq_scale':
            self.b_g_o('lbl_' + name).set_label('%s' % self.defs[name + 'val'])
            self.halcomp[name] = self.defs[name + 'val']
        else:
            self.b_g_o('lbl_' + name).set_label('%s' % round(self.defs[name + 'val'], 1))
            self.halcomp[name] = round(self.defs[name + 'val'], 1)

    def pb_changes(self, w, d=None):
        if w.get_active() and d == 'plasma':
            self.b_g_o('tb_ox').set_active(False)
            self.b_g_o('tb_ox').set_sensitive(False)
            mcode = 'M64'
            p = 'P1'
        if not w.get_active() and d == 'plasma':
            self.b_g_o('tb_ox').set_sensitive(True)
            mcode = 'M65'
            p = 'P1'
        if w.get_active() and d == 'ox':
            self.b_g_o('tb_plasma').set_active(False)
            self.b_g_o('tb_plasma').set_sensitive(False)
            mcode = 'M64'
            p = 'P2'
        if not w.get_active() and d == 'ox':
            self.b_g_o('tb_plasma').set_sensitive(True)
            mcode = 'M65'
            p = 'P2'
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi(mcode + 'P0')
        self.command.mdi(mcode + p)
        self.command.mode(linuxcnc.MODE_MANUAL)

def get_handlers(halcomp, builder, useropts):
    return [Panel(halcomp, builder, useropts)]



