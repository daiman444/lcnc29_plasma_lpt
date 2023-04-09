#!/usr/bin/env python3
# -*- coding:UTF-8 -*-

import hal
import gladevcp.persistence

from hal_glib import GStat


GSTAT = GStat()

class PlasmaClass:
    def __init__(self, halcomp, builder, useropts):
        self.halcomp = halcomp
        self.builder = builder
        self.useropts = useropts
        self.builder.get_object('table1').set_sensitive(False)
        self.defs = {"pierce_hghtval": 7.0,
                     "pierce_hghtmax": 15.0,
                     "pierce_hghtmin": 1.0,
                     "pierce_hghtincr": 0.5,
                     "jump_hghtval": 0.0,
                     "jump_hghtmax": 15.0,
                     "jump_hghtmin": 0.0,
                     "jump_hghtincr": 0.5,
                     "cut_hghtval": 9.0,
                     "cut_hghtmax": 15.0,
                     "cut_hghtmin": 0.0,
                     "cut_hghtincr": 0.5,
                     "pierce_delval": 0.0,
                     "pierce_delmax": 5.0,
                     "pierce_delmin": 0.0,
                     "pierce_delincr": 0.1,
                     "safe_zval": 30.0,
                     "safe_zmax": 100.0,
                     "safe_zmin": 0.0,
                     "safe_zincr": 5.0,
                     "z_speedval": 750.0,
                     "z_speedmax": 1000.0,
                     "z_speedmin": 100.0,
                     "z_speedincr": 50.0,
                     "stop_delval": 13.0,
                     "stop_delmax": 20.0,
                     "stop_delmin": 0.0,
                     "stop_delincr": 1.0,
                     "cor_velval": 20.0,
                     "cor_velmax": 100.0,
                     "cor_velmin": 0.0,
                     "cor_velincr": 5.0,
                     "vel_tolval": 90.0,
                     "vel_tolmax": 100.0,
                     "vel_tolmin": 0.0,
                     "vel_tolincr": 5.0,
                     "feed_directval": 1,
                     "feed_directmax": 1,
                     "feed_directmin": -1,
                     "feed_directincr": 1,
                     "volts_reqval": 125,
                     "volts_reqmax": 130,
                     "volts_reqmin": 120,
                     "volts_reqincr": 1,
                     "hall_valueval": 125,
                     "hall_valuemax": 130,
                     "hall_valuemin": 120,
                     "hall_valueincr": 1,
                     }
        GSTAT.connect('all-homed', lambda w: self.all_homed('homed'))
        GSTAT.connect('mode-auto', lambda w: self.mode_change('auto'))
        GSTAT.connect('mode-manual', lambda w: self.mode_change('manual'))
        GSTAT.connect('mode-mdi', lambda w: self.mode_change('mdi'))

        self.widgets_in_mode = ['btn_go_to_zero', 'btn_gotoend', 'btn_xyz_zero',
                                'btn_x_zero', 'btn_y_zero', 'btn_z_zero',
                                'btn_set_coord_x', 'entry_coord_x', 'btn_set_coord_y',
                                'entry_coord_y', 'tbtn_plasma', 'tbtn_oxy',
                                ]

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


def get_handlers(halcomp, builder, useropts):
    return [PlasmaClass(halcomp, builder, useropts)]
