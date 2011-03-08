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
    
#    db_connector, _ = DatabaseManager(env)._get_connector()
#    for table in tables:
#        for stmt in db_connector.to_sql(table):
#            cursor.execute(stmt)

    temp_cursor = env.get_db_cnx().cursor()

    # We want to make space for a new report 4, so we grab everything
    # greater than 3 to work with.
    cursor.execute("SELECT key, report FROM requirement_report "
                   "WHERE key > 3 ORDER BY key DESC")

    for row in cursor:
            #renumber the reports by 1,  but not views.
            #If I were adding two reports, i would add by 2, etc.
        if row[1][0:7] == 'report/':
            report = 'report/' + str( int(row[1][7]) + 1)
        else:
            report = row[1]
        # This increases the key number of each report after
        # the third report, as well as the report number if
        # appropriate. Again, if I were adding two reports,
        # I would do "int(row[0])+2" below. 
        temp_cursor.execute("UPDATE requirement_report "
                            "SET key = %s, report = %s "
                            " WHERE key = %s",
                            (int(row[0])+1, report, row[0]))

    # Now that there is space, put in our report where we want it.
    cursor.execute("INSERT INTO requirement_report "
                   "(report, title, query, description, key) "
                   "VALUES ('report/4', 'Requirements by User', "
                   "\"SELECT r.creator AS __group__,"
                   "'<' || r.component || ' ' || fp.name || ' ' || "
                   "o.name || '>' AS 'Requirement', "
                   "r.description AS 'Description', "
                   "r.creator AS 'Creator' "
                   "FROM requirement r, fp, object o "
                   "WHERE r.status = 'enabled' "
                   "AND r.fp = fp.id "
                   "AND o.id = r.object "
                   "ORDER BY r.component, fp.name, o.name\", "
                   "'Show all requirements, grouped by author', 4)")
                   
                   
