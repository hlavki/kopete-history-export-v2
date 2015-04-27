#!/usr/bin/python

##############################################################################
#
# Copyright (C) 20015 Michal Hlavac <miso@hlavki.eu>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import dateutil.parser
import os
from os.path import expanduser
import sqlite3
import sys
import xml.etree.ElementTree as ET


def export(accountId, dbPath, exportDir):
    conn = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    filesSql = """SELECT h1.other_id, strftime('%%Y-%%m', h1.datetime) AS day 
                    FROM history h1 
                    WHERE h1.other_id IN (
                        SELECT distinct(h2.other_id) 
                            FROM history h2 
                            WHERE h2.account='%s' AND h2.other_id NOT LIKE '%%@public.talk.google.com') 
                    GROUP BY h1.other_id, day ORDER BY day""" % accountId
    rows = cursor.execute(filesSql).fetchall()
    for row in rows:
        # @type otherId str
        otherId = row[0]
        day = row[1].split('-')
        rootEl = ET.Element("kopete-history")
        rootEl.set("version", "0.9")
        headEl = ET.SubElement(rootEl, "head")
        dateEl = ET.SubElement(headEl, "date")
        dateEl.set("month", day[1])
        dateEl.set("year", day[0])
        contactEl = ET.SubElement(headEl, "contact")
        contactEl.set("contactId", accountId)
        contactEl.set("type", "myself")
        contactEl = ET.SubElement(headEl, "contact")
        contactEl.set("contactId", otherId)
        print "Exporting history for buddy %s and day %s" % (otherId, "-".join(day))
        messagesSql = """SELECT id, protocol, account, direction, me_id, me_nick, other_id, other_nick, datetime, message 
                            FROM history 
                            WHERE other_id = '%s' AND strftime('%%Y-%%m', datetime) = '%s' 
                            ORDER BY datetime ASC""" % (otherId, "-".join(day))
        for brow in cursor.execute(messagesSql):
            msgEl = ET.SubElement(rootEl, "msg")
            msgEl.set("nick", brow[7] if brow[3] == "1" else brow[5])
            msgEl.set("in", brow[3])
            msgEl.set("from", brow[6] if brow[3] == "1" else brow[4])
            msgTime = dateutil.parser.parse(brow[8]);
            msgEl.set("time", "%d %d:%d:%d" % (msgTime.day, msgTime.hour, msgTime.minute, msgTime.second))
            msgEl.text = brow[9]
            indent(rootEl)

        tree = ET.ElementTree(rootEl)
        exportFileName = otherId.replace(".", "-") + "." + day[0] + day[1] + ".xml";
        tree.write(os.path.join(exportDir, exportFileName), xml_declaration=True, encoding='utf-8', method="xml")


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

if len(sys.argv) < 3:
    print 'Usage: ' + sys.argv[0] + '<account ID> <output directory>'
    sys.exit(1)

accountId = sys.argv[1]
exportDir = sys.argv[2]
dbPath = os.path.join(expanduser("~"), ".kde4/share/apps/kopete/kopete_history.db");

if not os.path.exists(exportDir):
    os.makedirs(exportDir)
    
export(accountId, dbPath, exportDir)