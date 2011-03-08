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
    cursor.execute("CREATE TEMPORARY TABLE object_old AS SELECT * FROM object")
    cursor.execute("DROP TABLE object")
    
    tables = [
        Table('object', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('status'),
            Column('description'),
            Column('changetime', type='int'),
            Column('time', type='int')],
        Table('object_custom', key=('id','name'))[
            Column('id'),
            Column('name'),
            Column('value')],
        Table('fp_change', key=('id','time','field'))[
            Column('id', type='int'),
            Column('time'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
        Table('hyponym_change', key=('id', 'time', 'field'))[
            Column('id', type='int'),
            Column('time'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
        Table('object_change', key=('id', 'time', 'field'))[
            Column('id', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')]]
    
    db_connector, _ = DatabaseManager(env)._get_connector()
    for table in tables:
        for stmt in db_connector.to_sql(table):
            cursor.execute(stmt)
            
    # Insert the objects into the new table
    cursor.execute("INSERT INTO object (name, description) "
                   "SELECT o.name, o.description "
                   "FROM object_old AS o")
    cursor.execute("DROP TABLE object_old")
