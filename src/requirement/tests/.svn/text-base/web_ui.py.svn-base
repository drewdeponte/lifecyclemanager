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

from trac.core import *
from trac.test import EnvironmentStub, Mock
from trac.requirement.web_ui import RequirementModule, NewrequirementModule
from trac.perm import PermissionCache
from trac.web.href import Href



import unittest
import time

class RequirementModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        
        self.requirement_module = RequirementModule(self.env)
        self.req = Mock(hdf=dict(), args=dict())
        self.req.href = Href('/trac')
        self.req.base_path = 'http://lm'

        cursor = self.env.db.cursor()
        cursor.execute("INSERT INTO permission VALUES ('joe', 'TRAC_ADMIN')")
        
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
                
        cursor.execute("INSERT INTO fp (id, name) VALUES (420, 'y')")
        cursor.execute("INSERT INTO object (id, name) VALUES (666, 'z')")
        cursor.execute("INSERT INTO requirement VALUES ('x', 420, 666, 0, 0, 'joe', 'enabled', 'foo bar')")
        cursor.execute("INSERT INTO requirement_change VALUES ('x', 420, 666, 0,'joe', 'blahd', 'foo bar', 'blahdsd')")
	cursor.execute("INSERT INTO wiki VALUES ('joe',1,122212,'author','foo','bar','comment',1)")
	cursor.execute("INSERT INTO ticket_change VALUES (1221,122212,'joe','foo','oldfoo','newfoo')")
        self.env.db.commit()
        
        self.req.authname = 'joe'
        self.req.perm = PermissionCache(self.env, self.req.authname)
        
    def test_match_request1(self):
        """Test non-match of request ''"""
        self.req.path_info = ''
        self.assertFalse(self.requirement_module.match_request(self.req))
        
    def test_match_request2(self):
        """Test non-match of request '/requirement'"""
        self.req.path_info = '/requirement'
        self.assertFalse(self.requirement_module.match_request(self.req))
        
    def test_match_request3(self):
        """Test match of request '/requirement/foo-bar-blah'"""
        self.req.path_info = '/requirement/foo-bar-blah'
        self.assertTrue(self.requirement_module.match_request(self.req))
        
    def test_match_request4(self):
        """Test match request of '/requirement/foo-bar-blah/'"""
        self.req.path_info = '/requirement/foo-bar-blah/'
        self.assertTrue(self.requirement_module.match_request(self.req))
    
    def test_process_request2(self):
        """Test existant requirement returns right template"""
        self.req.method = 'GET'
        self.req.path_info = '/requirement/x-y-z'
        self.assertEqual(self.requirement_module.process_request(self.req),
                        ('requirement.cs', None))
        
    def test_process_request3(self):
        """Test existant requirement sets title"""
        self.req.method = 'GET'
        self.req.path_info = '/requirement/x-y-z'
        self.requirement_module.process_request(self.req)
        self.assertEqual(self.req.hdf['title'], 'Requirements')
    
    def test_process_request4(self):
        """Test non-existant requirement error"""
        self.req.method = 'GET'
        self.req.path_info = '/requirement/non-exist-ant'
        self.assertRaises(TracError, self.requirement_module.process_request, self.req)
        self.req.method = 'GET'
        self.req.path_info = '/requirement/non-exist-ant'
    
def suite():
    return unittest.makeSuite(RequirementModuleTestCase, 'test')

if __name__ == '__main__':
    unittest.main()

        
