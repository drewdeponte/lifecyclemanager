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
    tables = [
        Table('requirement_data_cache', key=('component','fp','object','name'))[
            Column('component'),
            Column('fp'),
            Column('object'),
            Column('name'),
            Column('data', type='blob')]]


    db_connector, _ = DatabaseManager(env)._get_connector()
    for table in tables:
        for stmt in db_connector.to_sql(table):
            cursor.execute(stmt)
