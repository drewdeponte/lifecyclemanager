#
# Copyright 2007-2008 Lifecycle Manager Development Team
# http://www.insearchofartifice.com/lifecyclemanager/wiki/DevTeam
#
# This file is part of Lifecycle Manager.
#
# Lifecycle Manager is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lifecycle Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lifecycle Manager.  If not, see
# <http://www.gnu.org/licenses/>.

from trac.db import Table, Column, Index, DatabaseManager

def do_upgrade(env, ver, cursor):
    """changes reports to respect out-of-date status and fixes pmi data

    This upgrade has two parts, the first is to change reports that 
    check for enabled status, and allows them to still see out-of-date
    requirements. The second part adds creation times and changetimes 
    to rows in the fp/object tables that don't have times because they
    were added to the database before the models were built. This is
    important because some functions (like PMI) rely on comparisons 
    against those times. 
    """
    # These are the reports that need to be updated, and their 
    # new queries. 
    query_list = [ ('report/1',  
                    "SELECT r.component AS __group__, "
                    "'<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>' as 'Requirement', "
                    "r.description AS 'Description', "
                    "r.creator AS 'Creator' "
                    "FROM requirement r, fp, object o "
                    "WHERE r.status <> 'disabled' "
                    "AND r.fp = fp.id "
                    "AND o.id = r.object "
                    "ORDER BY r.component, fp.name, o.name"),
                   ('report/2',
                    "SELECT o.name AS __group__, "
                    "'<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>' AS 'Requirement', "
                    "r.description AS 'Description', "
                    "r.creator AS 'Creator' "
                    "FROM requirement r, fp, object o "
                    "WHERE r.status <> 'disabled' "
                    "AND r.fp = fp.id "
                    "AND o.id = r.object "
                    "ORDER BY o.name, r.component, fp.name"),
                   ('report/3',
                    "SELECT fp.name AS __group__, "
                    "'<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>' AS 'Requirement', "
                    "r.description AS 'Description', "
                    "r.creator AS 'Creator' "
                    "FROM requirement r, fp, object o "
                    "WHERE r.status <> 'disabled' "
                    "AND r.fp = fp.id "
                    "AND o.id = r.object "
                    "ORDER BY fp.name, r.component, o.name"),
                   ('report./4',
                     "SELECT r.creator AS __group__, "
                    "'<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>' AS 'Requirement', "
                    "r.description AS 'Description' "
                    "FROM requirement r, fp, object o "
                    "WHERE r.status <> 'disabled' "
                    "AND r.fp = fp.id "
                    "AND o.id = r.object "
                    "ORDER BY r.creator, r.component, fp.name, o.name"),
                   ('report/5',
                    "SELECT ('<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>') AS __group__, "
                    "'#' || rtc.ticket AS 'ticket', "
                    "t.summary AS 'summary' "
                    "FROM object o INNER JOIN fp INNER JOIN requirement r "
                    "LEFT JOIN requirement_ticket_cache rtc "
                    "LEFT JOIN ticket t "
                    "WHERE (o.id = r.object) AND (fp.id = r.fp) "
                    "AND (r.status <> 'disabled') "
                    "AND (r.component = rtc.component AND "
                    "fp.name = rtc.fp AND "
                    "o.name = rtc.object "
                    ") AND (t.id = rtc.ticket) "),
                   ('report/6', 
                    "SELECT m.name AS __group__, "
                    "'<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>' as 'Requirement', "
                    "r.description AS 'Description', "
                    "r.creator AS 'Creator' "
                    "FROM object o INNER JOIN fp INNER JOIN requirement r "
                    "LEFT JOIN milestone m "
                    "WHERE (o.id = r.object) AND (fp.id = r.fp) "
                    "AND (r.status <> 'disabled') "
                    "AND (r.changetime < m.due) "
                    "ORDER BY m.name, r.component, fp.name, o.name"),
                   ('report/7',
                    "SELECT m.name AS __group__, "
                    "'<' || r.component || ' ' || r.fp || ' ' || "
                    "r.object || '>' as 'Requirement', "
                    "r.description AS 'Description', "
                    "r.creator AS 'Creator' "
                    "FROM milestone m "
                    "INNER JOIN "
                    "(SELECT r.component AS component, "
                    "fp.name AS fp, "
                    "o.name AS object, "
                    "r.description AS description, "
                    "r.creator AS creator, "
                    "t.milestone AS milestone "
                    "FROM object o INNER JOIN fp INNER JOIN requirement r "
                    "LEFT JOIN requirement_ticket_cache rtc  "
                    "LEFT JOIN ticket t "
                    "WHERE (o.id = r.object) AND (fp.id = r.fp) "
                    "AND (r.status <> 'disabled') "
                    "AND (r.component = rtc.component AND "
                    "fp.name = rtc.fp AND "
                    "o.name = rtc.object "
                    ") AND ("
                    "t.id = rtc.ticket"
                    ")"
                    "GROUP BY t.milestone, r.component, fp.name, o.name "
                    "ORDER BY r.component, fp.name, o.name "
                    ") r "
                    "ON r.milestone = m.name "
                    "ORDER BY r.milestone"),
                   ('report/9',
                    "SELECT '<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>' AS __group__, "
                    "w.name as 'Wiki', "
                    "w.comment as 'Comment', "
                    "w.version as 'Version', "
                    "w.author AS 'Creator' "
                    "FROM object o INNER JOIN fp INNER JOIN requirement r "
                    "LEFT JOIN requirement_wiki_cache rwc "
                    "LEFT JOIN wiki w "
                    "WHERE (o.id = r.object) AND (fp.id = r.fp) "
                    "AND (r.status <> 'disabled') "
                    "AND ("
                    "r.component = rwc.component AND "
                    "fp.name = rwc.fp AND "
                    "o.name = rwc.object "
                    ") AND ("
                    "w.name = rwc.wiki_name AND "
                    "w.version = rwc.wiki_version "
                    ") "
                    "ORDER BY r.component, fp.name, o.name"),
                   ('report/10',
                    "SELECT w.name AS __group__, "
                    "'<' || r.component || ' ' || fp.name || ' ' || "
                    "o.name || '>' as Requirement, "
                    "r.description as 'Description', "
                    "r.creator as 'Creator' "
                    "FROM object o INNER JOIN fp INNER JOIN requirement r "
                    "LEFT JOIN requirement_wiki_cache rwc "
                    "LEFT JOIN wiki w "
                    "WHERE (o.id = r.object) AND (fp.id = r.fp) "
                    "AND (r.status <> 'disabled') "
                    "AND ("
                    "r.component = rwc.component AND "
                    "fp.name = rwc.fp AND "
                    "o.name = rwc.object "
                    ") AND ("
                    "w.name = rwc.wiki_name AND "
                    "w.version = rwc.wiki_version AND "
                    "w.version = (SELECT MAX(version) "
                    "FROM wiki "
                    "WHERE name = rwc.wiki_name)"
                    ") "
                    "ORDER BY w.name, r.component, fp.name, o.name")]

    # We add each query to its appropriate row in the report table.
    for report, query in query_list:
        cursor.execute("UPDATE requirement_report "
                       "SET query=%s"
                       "WHERE report=%s",
                       (query, report))

    # For the second part we find all of the fps and objects that 
    # DO NOT have times associated with them, and give them a creation 
    # time based on the creation of the first requirement that
    # references them

    # Dictionary that hold the id as key, and time as its paired value.
    fps = {}
    cursor.execute("SELECT fp, MIN(time) FROM requirement "
                   "GROUP BY fp")
    for row in cursor:
        fps[row[0]] = row[1]

    fp_needs_time = []
    fp_needs_changetime =[]
    
    cursor.execute("SELECT id FROM fp WHERE time IS NULL")
    for row in cursor:
        fp_needs_time.append(row[0])
        if row[0] not in fps:
            fps[row[0]] = 1
    cursor.execute("SELECT id FROM fp WHERE changetime IS NULL")
    for row in cursor:
        fp_needs_changetime.append(row[0])
        if row[0] not in fps:
            fps[row[0]] = 1

    # The actual updates
    for id in fp_needs_time:
        cursor.execute("UPDATE fp SET time=%s where id=%s", 
                       (fps[id], id))
    for id in fp_needs_changetime:
        cursor.execute("UPDATE fp SET changetime=%s where id=%s",
                       (fps[id], id))

    # Same process for objects
   
    objects = {}
    cursor.execute("SELECT object, MIN(time) FROM requirement "
                   "GROUP BY object")
    for row in cursor:
        objects[row[0]] = row[1]

    object_needs_time = []
    object_needs_changetime =[]
    
    cursor.execute("SELECT id FROM object WHERE time IS NULL")
    for row in cursor:
        object_needs_time.append(row[0])
        if row[0] not in objects:
            objects[row[0]] = 1

    cursor.execute("SELECT id FROM object WHERE changetime IS NULL")
    for row in cursor:
        object_needs_changetime.append(row[0])
        if row[0] not in objects:
            objects[row[0]] = 1


    for id in object_needs_time:
        cursor.execute("UPDATE object SET time=%s where id=%s", 
                       (objects[id], id))
    for id in object_needs_changetime:
        cursor.execute("UPDATE object SET changetime=%s where id=%s",
                       (objects[id], id))

