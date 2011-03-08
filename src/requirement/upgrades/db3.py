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
    cursor.execute("CREATE TEMPORARY TABLE fp_old AS SELECT * FROM fp")
    cursor.execute("DROP TABLE fp")
    cursor.execute("CREATE TEMPORARY TABLE fp_change_old AS SELECT * FROM fp_change")
    cursor.execute("DROP TABLE fp_change")
    cursor.execute("CREATE TEMPORARY TABLE hyp_change_old AS SELECT * FROM hyponym_change")
    cursor.execute("DROP TABLE hyponym_change")
    cursor.execute("CREATE TEMPORARY TABLE hyp_old AS SELECT * FROM hyponym")
    cursor.execute("DROP TABLE hyponym")


    tables = [
        Table('fp', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('description'),
            Column('status'),
            Column('time', type='int'),
            Column('changetime', type='int')],
        Table('fp_custom', key=('id', 'name'))[
            Column('id'),
            Column('name'),
            Column('value')],
        Table('fp_change', key=('id','time','field'))[
            Column('id', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
        Table('hyponym_change', key=('id', 'time', 'field'))[
            Column('id', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
        Table('hyponym', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('fp'),
            Column('status'),
            Column('changetime', type='int'),
            Column('time', type='int')]]

    db_connector, _ = DatabaseManager(env)._get_connector()
    
    for table in tables:
        for stmt in db_connector.to_sql(table):
            cursor.execute(stmt)
 # Insert all the data from the old tables into the new tables
    cursor.execute("INSERT INTO fp (name, description) "
                   "SELECT o.name, o.description "
                   "FROM fp_old AS o")
    cursor.execute("DROP TABLE fp_old")

    cursor.execute("INSERT INTO fp_change (id,time,author,field,"
                                           "oldvalue,newvalue) "
                   "SELECT o.id, o.time, o.author, o.field, "
                   "o.oldvalue, o.newvalue "
                   "FROM fp_change_old AS o")
    cursor.execute("DROP TABLE fp_change_old")

    cursor.execute("INSERT INTO hyponym (name, fp) "
                   "SELECT o.name, o.fp "
                   "FROM hyp_old AS o")
    cursor.execute("DROP TABLE hyp_old")

    cursor.execute("INSERT INTO hyponym_change (id,time,author,field,"
                                               "oldvalue,newvalue) "
                   "SELECT o.id, o.time, o.author, o.field, "
                   "o.oldvalue, o.newvalue "
                   "FROM hyp_change_old AS o")
    cursor.execute("DROP TABLE hyp_change_old")
