#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Frederic Mohier, frederic.mohier@gmail.com
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import math

from shinken.util import safe_print
from shinken.misc.perfdata import PerfDatas
from shinken.log import logger


# Will try to return a dict with:
# lnk: link to add in this perfdata thing
# title: text to show on it
# metrics: list of ('html color', percent) like [('#68f', 35), ('white', 64)]
def get_perfometer_table_values(elt):
    # first try to get the command name called
    cmd = elt.check_command.call.split('!')[0]
    logger.info("[WebUI] Looking for perfometer value for element: %s, command: %s", elt.get_full_name(), cmd)

    tab = {'check_http': manage_check_http_command,
           'check_ping': manage_check_ping_command,
           'check_tcp': manage_check_tcp_command,
           'check_ftp': manage_check_tcp_command,
        }

    f = tab.get(cmd, None)
    if f:
        return f(elt)

    try:
        r = manage_unknown_command(elt)
    except:
        return None
    return r


def manage_check_http_command(elt):
    safe_print('Get check_http perfdata of', elt.get_full_name())
    p = PerfDatas(elt.perf_data)
    if not 'time' in p:
        print "No time in p"
        return None

    m = p['time']
    v = m.value
    if not v:
        print "No value, I bailout"
        return None

    # Percent of ok should be time/1s
    pct = get_logarithmic(v, 1)
    # Now get the color
    # OK: #6f2 (102,255,34) green
    # Warning: #f60 (255,102,0) orange
    # Crit: #ff0033 (255,0,51)
    base_color = {0: (102, 255, 34), 1: (255, 102, 0), 2: (255, 0, 51)}
    state_id = get_stateid(elt)
    color = base_color.get(state_id, (179, 196, 255))
    s_color = 'RGB(%d,%d,%d)' % color
    lnk = '#'
    metrics = [(s_color, pct), ('white', 100-pct)]
    title = '%ss' % v
    #print "HTTP: return", {'lnk': lnk, 'metrics': metrics, 'title': title}
    return {'lnk': lnk, 'metrics': metrics, 'title': title}

def manage_check_ping_command(elt):
    safe_print('Get check_ping perfdata of', elt.get_full_name())
    p = PerfDatas(elt.perf_data)
    if not 'rta' in p:
        print "No rta in p"
        return None

    m = p['rta']
    v = m.value
    crit = m.critical
    if not v or not crit:
        print "No value, I bailout"
        return None

    # Percent of ok should be the log of time versus max/2
    pct = get_logarithmic(v, crit / 2)
    # Now get the color
    # OK: #6f2 (102,255,34) green
    # Warning: #f60 (255,102,0) orange
    # Crit: #ff0033 (255,0,51)
    base_color = {0: (102, 255, 34), 1: (255, 102, 0), 2: (255, 0, 51)}
    state_id = get_stateid(elt)
    color = base_color.get(state_id, (179, 196, 255))
    s_color = 'RGB(%d,%d,%d)' % color

    lnk = '#'
    metrics = [(s_color, pct), ('white', 100-pct)]
    title = '%sms' % v
    #print "HTTP: return", {'lnk': lnk, 'metrics': metrics, 'title': title}
    return {'lnk': lnk, 'metrics': metrics, 'title': title}


def manage_check_tcp_command(elt):
    safe_print('Get check_tcp perfdata of', elt.get_full_name())
    p = PerfDatas(elt.perf_data)
    if not 'time' in p:
        print "No time in p"
        return None

    m = p['time']
    v = m.value

    if not v or not m.max:
        print "No value, I bailout"
        return None

    # Percent of ok should be the log of time versus m.max / 2
    pct = get_logarithmic(v, m.max / 2)

    # Now get the color
    # OK: #6f2 (102,255,34) green
    # Warning: #f60 (255,102,0) orange
    # Crit: #ff0033 (255,0,51)
    base_color = {0: (102, 255, 34), 1: (255, 102, 0), 2: (255, 0, 51)}
    state_id = get_stateid(elt)
    color = base_color.get(state_id, (179, 196, 255))
    s_color = 'RGB(%d,%d,%d)' % color

    #pct = 100 * (v / m.max)
    # Convert to int
    #pct = int(pct)
    # Minimum 1%, maximum 100%
    #pct = min(max(1, pct), 100)
    lnk = '#'
    metrics = [(s_color, pct), ('white', 100-pct)]
    title = '%ss' % v
    #print "HTTP: return", {'lnk': lnk, 'metrics': metrics, 'title': title}
    return {'lnk': lnk, 'metrics': metrics, 'title': title}


def manage_unknown_command(elt):
    logger.debug("[WebUI] perfometer, manage command for: %s", elt.get_full_name())
    p = PerfDatas(elt.perf_data)
    if len(p) == 0:
        return None

    metric = None
    # Got some override name we know to be ok for printing
    if 'time' in p and p['time'].value is not None:
        metric = p['time']
    else:
        for v in p:
            if v.name is not None and v.value is not None:
                metric = v
                break
    if not metric:
        return metric
    
    name = metric.name
    value = metric.value
    logger.debug("[WebUI] perfometer, manage command, metric: %s=%d", name, value)
    if not value:
        return None

    
    pct = 0
    # Look if min/max are defined
    if metric.min and metric.max and (metric.max - metric.min != 0):
        pct = 100 * (value / (metric.max - metric.min))
    else:
        # Assume value is 100%
        pct = 100

    # Percentage is at least 1% and max 100%
    pct = max(1, pct)
    pct = min(pct, 100)
    
    # Title
    try:
        uom = '' or m.uom
        title = '%s=%s%s' % (name, value, uom)
    except:
        title = '%s=%s' % (name, value)

    # Link
    lnk = '#'

    # Get the color
    base = {0: 'success', 1: 'warning', 2: 'danger', 3: 'info'}
    color = base.get(elt.state_id, 'info')
    
    logger.debug("[WebUI] perfometer, manage command, metric: %s=%d -> %d", name, value, pct)

    return {'lnk': lnk, 'metrics': [(color, pct)], 'title': title}


def get_logarithmic(value, half):
    l_half = math.log(half, 10)
    print 'Half is', l_half
    l_value = math.log(value, 10)
    print "l value is", l_value
    # Get the percent of our value for what we asked for
    r = 50 + 10.0 * (l_value - l_half)
    # Make it an int between 1 and 100
    r = int(r)
    r = max(1, r)
    r = min(r, 100)

    return r
