#!/usr/bin/env python3
# -*- coding:UTF-8 -*-

import os
import hal
import hal_glib
import linuxcnc
import gladevcp.persistence
# TODO how to gi
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
#from gi.repository import Gtk
#from gi.overrides import Gtk
#from gi.repository import Gdk
#from gi.repository import GdkPixbuf
#from gi.repository import GLib

from hal_glib import GStat, GPin

GSTAT = GStat()
INIPATH = os.environ.get('INI_FILE_NAME', '/dev/null')

class PlasmaClass:
    def __init__(self, halcomp, builder, useropts):
        self.halcomp = halcomp
        self.builder = builder
        self.useropts = useropts
        self.command = linuxcnc.command()
        self.inifile = linuxcnc.ini(INIPATH)
        self.defs = {"pierce_val": 7.0,
                     "pierce_max": 15.0,
                     "pierce_min": 1.0,
                     "pierce_incr": 0.5,
                     "jump_val": 0.0,
                     "jump_max": 15.0,
                     "jump_min": 0.0,
                     "jump_incr": 0.5,
                     "cut_val": 9.0,
                     "cut_max": 15.0,
                     "cut_min": 0.0,
                     "cut_incr": 0.5,
                     "pierce_delay_val": 0.0,
                     "pierce_delay_max": 5.0,
                     "pierce_delay_min": 0.0,
                     "pierce_delay_incr": 0.1,
                     "safe_z_val": 30.0,
                     "safe_z_max": 100.0,
                     "safe_z_min": 0.0,
                     "safe_z_incr": 5.0,
                     "search_vel_val": 750.0,
                     "search_vel_max": 1000.0,
                     "search_vel_min": 100.0,
                     "search_vel_incr": 50.0,
                     "purge_val": 13.0,
                     "purge_max": 20.0,
                     "purge_min": 0.0,
                     "purge_incr": 1.0,
                     "correction_val": 20.0,
                     "correction_max": 100.0,
                     "correction_min": 0.0,
                     "correction_incr": 5.0,
                     "corner_lock_val": 90.0,
                     "corner_lock_max": 100.0,
                     "corner_lock_min": 0.0,
                     "corner_lock_incr": 5.0,
                     "feed_direct_val": 1,
                     "feed_direct_max": 1,
                     "feed_direct_min": -1,
                     "feed_direct_incr": 1,
                     }

        self.builder.get_object('table1').set_sensitive(False)

        GSTAT.connect('all-homed', lambda w: self.all_homed('homed'))
        GSTAT.connect('mode-auto', lambda w: self.mode_change('auto'))
        GSTAT.connect('mode-manual', lambda w: self.mode_change('manual'))
        GSTAT.connect('mode-mdi', lambda w: self.mode_change('mdi'))

        self.builder.get_object('btn_go_to_zero').connect('pressed', self.go_to_zero, 'G90 G0 Z30 X0 Y0 F800')
        self.builder.get_object('btn_xyz_zero').connect('pressed', self.go_to_zero, 'G92 X0 Y0 Z0')
        self.builder.get_object('btn_x_zero').connect('pressed', self.go_to_zero, 'G92 X0')
        self.builder.get_object('btn_y_zero').connect('pressed', self.go_to_zero, 'G92 Y0')
        self.builder.get_object('btn_z_zero').connect('pressed', self.go_to_zero, 'G92 Z0')
        self.builder.get_object('btn_gotoend').connect('pressed', self.gotoend)
        self.builder.get_object('btn_set_coord_x').connect('pressed', self.setcoord, 'x')
        self.builder.get_object('btn_set_coord_y').connect('pressed', self.setcoord, 'y')

        self.widgets_in_mode = ['btn_go_to_zero', 'btn_gotoend', 'btn_xyz_zero',
                                'btn_x_zero', 'btn_y_zero', 'btn_z_zero',
                                'btn_set_coord_x', 'entry_coord_x', 'btn_set_coord_y',
                                'entry_coord_y', 'tbtn_plasma', 'tbtn_oxy',
                                ]

        # feed direction
        self.pin_feed_dir_plus = GPin(halcomp.newpin('btn-feed-fwd', hal.HAL_BIT, hal.HAL_IN))
        self.pin_feed_dir_plus.connect('value-changed', self.feed_direction_change, 1)

        self.pin_feed_dir_minus = GPin(halcomp.newpin('btn-feed-back', hal.HAL_BIT, hal.HAL_IN))
        self.pin_feed_dir_minus.connect('value-changed', self.feed_direction_change, -1)

        GPin(halcomp.newpin('feed-dir', hal.HAL_FLOAT, hal.HAL_OUT)).value = 1

        self.builder.get_object('btn_feed_fwd').connect('pressed', self.feed_direction_change, 1)
        self.builder.get_object('btn_feed_fwd').set_sensitive(False)

        self.builder.get_object('btn_feed_back').connect('pressed', self.feed_direction_change, -1)
        self.builder.get_object('btn_feed_back').set_sensitive(True)

        self.builder.get_object('lbl_feed').set_label('FWD')

        # declaring widgets as a list.
        # push-buttons list for change values:
        self.widgets_list = ['safe_z', 'search_vel', 'correction',
                             'corner_lock', 'pierce', 'pierce_delay',
                             'jump', 'cut', 'purge', ]

        # for a simplified call to dictionary values, we will declare a variable
        # referring to the dictionary:
        #self.defs = self.defaults[IniFile.vars]

        # after widgets_list declaration star the widget initialisation cycle:
        for name in self.widgets_list:
            # declaring defaults values to display
            self.builder.get_object('lbl_' + name).set_label('%s' % self.defs[name + '_val'])

            # declaring push-button '_plus' and connection to method
            self.builder.get_object('btn_' + name + '_plus').connect('pressed', self.widget_value_change, name, 1)
            if self.defs[name + '_val'] == self.defs[name + '_max']:
                self.builder.get_object('btn_' + name + '_plus').set_sensitive(False)

            # declaring push-button '_minus' and connection to method
            self.builder.get_object('btn_' + name + '_minus').connect('pressed', self.widget_value_change, name, -1)
            if self.defs[name + 'val'] == self.defs[name + '_min']:
                self.builder.get_object('btn_' + name + '_minus').set_sensitive(False)

            # declaring hal pin
            GPin(halcomp.newpin(name, hal.HAL_FLOAT, hal.HAL_OUT)).value = self.defs[name + '_val']

    def go_to_zero(self, w, d=None):
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi(d)
        self.command.wait_complete()
        self.command.mode(linuxcnc.MODE_MANUAL)

    def gotoend(self, w, d=None):
        x_limit = self.inifile.find('AXIS_X', 'MIN_LIMIT')
        y_limit = self.inifile.find('AXIS_Y', 'MAX_LIMIT')
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi('G53G00Z0')
        self.command.wait_complete()
        self.command.mdi(f'G53 X{x_limit} Y{y_limit}')
        self.command.wait_complete()
        self.command.mode(linuxcnc.MODE_MANUAL)

    def setcoord(self, widget, data=None):
        coord = self.builder.get_object('entry_coord_' + data).get_text()
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.mdi(f'G92{data}{coord}')
        self.command.wait_complete()
        self.command.mode(linuxcnc.MODE_MANUAL)

    def all_homed(self, stat):
        if stat == 'homed':
            self.builder.get_object('table1').set_sensitive(True)

    def mode_change(self, stat):
        if stat == 'auto' or stat == 'mdi':
            for i in self.widgets_in_mode:
                self.builder.get_object(i).set_sensitive(False)
        if stat == 'manual':
            for i in self.widgets_in_mode:
                self.builder.get_object(i).set_sensitive(True)

    def feed_direction_change(self, widget, value):
        self.builder.get_object('lbl_print1').set_label(str(type(widget)))
        self.builder.get_object('lbl_print2').set_label(str(value))

        if isinstance(widget, hal_glib.GPin):
            if widget.get() is True:
                self.pin_feed_dir.value += self.defs['feed_direct_val' * value]
                self.builder.get_object('lbl_print1').set_label(str(widget + value))
        if isinstance(widget, Gtk.Button):
            GPin(self.halcomp.newpin('feed-dir', hal.HAL_FLOAT, hal.HAL_OUT)).value += self.defs['feed_direct_val' * value]
            self.builder.get_object('lbl_print1').set_label(str(widget + value))
        if self.pin_feed_dir.value >= self.defs['feed_direct_max']:
            self.pin_feed_dir.value = self.defs['feed_direct_max']
            self.btn_feed_dir_plus.set_sensitive(False)
            self.lbl_feed_dir.set_label('FWD')
        elif self.pin_feed_dir.value <= self.defs['feed_direct_min']:
            self.pin_feed_dir.value = self.defs['feed_direct_min']
            self.btn_feed_dir_minus.set_sensitive(False)
            self.lbl_feed_dir.set_label('BWD')
        else:
            self.btn_feed_dir_plus.set_sensitive(True)
            self.btn_feed_dir_minus.set_sensitive(True)
            self.lbl_feed_dir.set_label('STOP')

    def widget_value_change(self, widget, name, value):
        self.defs[name + '_val'] += self.defs[name + '_incr'] * value
        if self.defs[name + '_val'] >= self.defs[name + '_max']:
            self.defs[name + '_val'] = self.defs[name + '_max']
            self.b_g_o('btn_' + name + '_plus').set_sensitive(False)
        elif self.defs[name + '_val'] <= self.defs[name + '_min']:
            self.defs[name + '_val'] = self.defs[name + '_min']
            self.b_g_o('btn_' + name + '_minus').set_sensitive(False)
        else:
            self.b_g_o('btn_' + name + '_plus').set_sensitive(True)
            self.b_g_o('btn_' + name + '_minus').set_sensitive(True)
        self.b_g_o('lbl_' + name).set_label('%s' % round(self.defs[name + '_val'], 1))
        self.halcomp[name] = round(self.defs[name + '_val'], 1)


def get_handlers(halcomp, builder, useropts):
    return [PlasmaClass(halcomp, builder, useropts)]
