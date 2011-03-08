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

import unittest

from trac.test import EnvironmentStub
from trac.requirement.model import Requirement
from trac.wiki.tests import formatter


REQUIREMENT_TEST_CASES="""
============================== requirement: link resolver
requirement:component1-fp1-object1
requirement:long_component_1-long_fp_1-long_object_1
requirement:x-y-z
------------------------------
<p>
<a class="existant requirement" href="/requirement/component1-fp1-object1" title="This is the description">requirement:component1-fp1-object1</a>
<a class="missing requirement" href="/requirement/long_component_1-long_fp_1-long_object_1" rel="nofollow">requirement:long_component_1-long_fp_1-long_object_1</a>
<a class="missing requirement" href="/requirement/x-y-z" rel="nofollow">requirement:x-y-z</a>
</p>
------------------------------
============================== requirement link shorthand form
&lt;component1 fp1 object1&gt;, &lt;long_component_1 long_fp_1 long_object_1&gt;, &lt;x y z&gt;
------------------------------
<p>
<a class="existant requirement" href="/requirement/component1-fp1-object1" title="This is the description">&lt;component1 fp1 object1&gt;</a>, <a class="missing requirement" href="/requirement/long_component_1-long_fp_1-long_object_1" rel="nofollow">&lt;long_component_1 long_fp_1 long_object_1&gt;</a>, <a class="missing requirement" href="/requirement/x-y-z" rel="nofollow">&lt;x y z&gt;</a>
</p>
------------------------------
============================== requirement link shorthand form, unescaped
<component1 fp1 object1>, <long_component_1 long_fp_1 long_object_1>, <x y z>
------------------------------
<p>
<a class="existant requirement" href="/requirement/component1-fp1-object1" title="This is the description">&lt;component1 fp1 object1&gt;</a>, <a class="missing requirement" href="/requirement/long_component_1-long_fp_1-long_object_1" rel="nofollow">&lt;long_component_1 long_fp_1 long_object_1&gt;</a>, <a class="missing requirement" href="/requirement/x-y-z" rel="nofollow">&lt;x y z&gt;</a>
</p>
------------------------------
============================== escaping the above
!<component1 fp1 object1>,
!<long_component_1 long_fp_1 long_object_1>,
!<x y z>
------------------------------
<p>
&lt;component1 fp1 object1&gt;,
&lt;long_component_1 long_fp_1 long_object_1&gt;,
&lt;x y z&gt;
</p>
------------------------------
&lt;component1 fp1 object1&gt;,
&lt;long_component_1 long_fp_1 long_object_1&gt;,
&lt;x y z&gt;
============================== InterTrac for requirements
trac<component1 fp1 object1>
------------------------------
<p>
<a class="ext-link" href="http://trac.edgewall.org/requirement/component1-fp1-object1" title="&lt;component1 fp1 object1&gt; in Trac's Trac"><span class="icon">trac&lt;component1 fp1 object1&gt;</span></a>
</p>
------------------------------
"""


def requirement_setup(rc):
    rc.env = EnvironmentStub()
    
    rc.env.config.set('intertrac', 'trac.title', "Trac's Trac")
    rc.env.config.set('intertrac', 'trac.url',
                    "http://trac.edgewall.org")
    rc.env.config.set('intertrac', 't', 'trac')
    cursor = rc.env.db.cursor()


    # Must insert components so that they are found 
    # when get_wiki_syntax() in api.py is called.
    # For a better explaination, inspect _get_component_regex()
    # located in api.py
    insert_component( rc.env.db, 'component1' )
    insert_component( rc.env.db, 'long_component_1' )
    insert_component( rc.env.db, 'x' )

    from trac.db.sqlite_backend import _to_sql
    from trac.requirement.db_default import schema
    for table in schema:
        for stmt in _to_sql(table):
            cursor.execute(stmt)
    rc.env.db.commit()

    requirement = Requirement(rc.env)
    requirement['component'] = 'component1'
    requirement['fp'] = 'fp1'
    requirement['object'] = 'object1'
    requirement['creator'] = 'bob'
    requirement['description'] = 'This is the description'
    requirement.insert()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.suite(REQUIREMENT_TEST_CASES, requirement_setup, __file__))
    return suite

def insert_component(db, component):
    cursor = db.cursor()
    sql = "INSERT INTO component VALUES ('%s', 'anonymous', 'Described')" % component
    cursor.execute( sql )
    db.commit()

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
    
    
