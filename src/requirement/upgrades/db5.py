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
    cursor.execute("CREATE TEMPORARY TABLE hyp_old AS SELECT * FROM hyponym")
    cursor.execute("DROP TABLE hyponym")
    cursor.execute("CREATE TEMPORARY TABLE hyp_cust_old AS SELECT * "
                   "FROM hyponym_custom")
    cursor.execute("DROP TABLE hyponym_custom")
    cursor.execute("CREATE TEMPORARY TABLE req_old AS SELECT * "
                   "FROM requirement")
    cursor.execute("DROP TABLE requirement")
    cursor.execute("CREATE TEMPORARY TABLE req_change_old AS SELECT * "
                   "FROM requirement_change")
    cursor.execute("DROP TABLE requirement_change")
    cursor.execute("CREATE TEMPORARY TABLE req_cust_old AS SELECT * "
                   "FROM requirement_custom")
    cursor.execute("DROP TABLE requirement_custom")

    tables = [
        Table('hyponym', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('fp', type='int'),
            Column('status'),
            Column('changetime', type='int'),
            Column('time', type='int')],
        Table('hyponym_custom', key=('id','name'))[
            Column('id', type='int'),
            Column('name'),
            Column('value')],
        Table('requirement', key=('component','fp','object'))[
            Column('component'),
            Column('fp', type='int'),
            Column('object', type='int'),
            Column('time', type='int'),
            Column('changetime', type='int'),
            Column('creator'),
            Column('status'),
            Column('description')],
        Table('requirement_change', key=('component','fp','object','time','field'))[
            Column('component'),
            Column('fp', type='int'),
            Column('object', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
        Table('requirement_custom', key=('component','fp','object','name'))[
            Column('component'),
            Column('fp', type='int'),
            Column('object', type='int'),
            Column('name'),
            Column('value')]]


    db_connector, _ = DatabaseManager(env)._get_connector()
    for table in tables:
        for stmt in db_connector.to_sql(table):
            cursor.execute(stmt)
    cursor.execute("INSERT INTO hyponym (id,name,fp,status,changetime,time) "
                   "SELECT h.id,h.name,fp.id,h.status,h.changetime,h.time "
                   "FROM fp, hyp_old h WHERE h.fp = fp.name")
    cursor.execute("DROP TABLE hyp_old")

    cursor.execute("INSERT INTO hyponym_custom (id,name,value) "
                   "SELECT h.id,h.name,h.value FROM hyp_cust_old h")
    cursor.execute("DROP TABLE hyp_cust_old")

    cursor.execute("INSERT INTO requirement "
                   "(component,fp,object,time,changetime,creator,status) "
                   "SELECT r.component,fp.id,o.id,r.time,r.changetime, "
                   "r.creator, r.status "
                   "FROM fp,object o, req_old r "
                   "WHERE fp.name=r.fp AND o.name = r.object")
    cursor.execute("DROP TABLE req_old")

    cursor.execute("INSERT INTO requirement_change "
                   "(component,fp,object,time,author,field,oldvalue,newvalue) "
                   "SELECT r.component,fp.id,o.id,r.time,r.author, "
                   "r.field, r.oldvalue, r.newvalue "
                   "FROM fp,object o, req_change_old r "
                   "WHERE fp.name=r.fp AND o.name = r.object")
    cursor.execute("DROP TABLE req_change_old")
                    
    cursor.execute("INSERT INTO requirement_custom "
                   "(component,fp,object,name,value) "
                   "SELECT r.component,fp.id,o.id,r.name,r.value "
                   "FROM fp,object o, req_cust_old r "
                   "WHERE fp.name=r.fp AND o.name = r.object")
    cursor.execute("DROP TABLE req_cust_old")
