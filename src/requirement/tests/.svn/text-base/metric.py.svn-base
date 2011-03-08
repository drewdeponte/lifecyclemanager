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

from trac.requirement.metric import RequirementMetric
from trac.requirement.model import Requirement
from trac.test import EnvironmentStub, Mock

import unittest, time

class RequirementMetricTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.model = Requirement(self.env)
        self.metric = RequirementMetric(self.model)
        
        # Set midtime to one hour ago
        # This is used as a central point for mock data timestamps
        self.midtime = time.time() - (60*60)
        
        cursor = self.env.db.cursor()
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
        
        for component in ['comp1', 'comp2', 'comp3']:
            cursor.execute("INSERT INTO component (name) VALUES(%s)", (component,))
                    
        id = 1    
        for fp, changetime in [ ('fp1', self.midtime-2),
                                ('fp2', self.midtime-1),
                                ('fp3', self.midtime+1),
                                ('fp4', self.midtime+2)]:
            cursor.execute("INSERT INTO fp (id, name, status, time, changetime) "
                           "VALUES(%s, %s, 'enabled', %s, %s)", (id, fp, changetime, changetime))
            id += 1
        id = 1
        for object, changetime in [ ('obj1', self.midtime-2),
                                    ('obj2', self.midtime-1),
                                    ('obj3', self.midtime+1),
                                    ('obj4', self.midtime+2)]:
            cursor.execute("INSERT INTO object (id, name, status, time, changetime) "
                           "VALUES(%s, %s, 'enabled', %s, %s)", (id, object, changetime, changetime))
            id +=1

        # time/changetime are set to latest time/changetime from the corresponding fps/objs
        for component, fp, object, changetime in [  ('comp1', 1, 1, self.midtime-2),
                                                    ('comp1', 1, 2, self.midtime-1),
                                                    ('comp1', 1, 3, self.midtime+1),
                                                    ('comp1', 2, 1, self.midtime-1),
                                                    ('comp1', 3, 2, self.midtime+1),
                                                    ('comp2', 1, 3, self.midtime+1),
                                                    ('comp2', 2, 1, self.midtime-1),
                                                    ('comp3', 4, 4, self.midtime+2),
                                                    ('comp3', 3, 2, self.midtime+1),
                                                    ('comp3', 3, 1, self.midtime+1),
                                                    ('comp3', 1, 4, self.midtime+2)]:
            cursor.execute("INSERT INTO requirement (component,fp,object,status,time,changetime) "
                           "VALUES (%s,%s,%s,'enabled',%s,%s)", (component, fp, object, changetime, changetime))

        
        self.env.db.commit()
        
    def test_entropy1(self):
        total_entropy, _, _, _, _, _ = self.metric.entropy()
        self.assertAlmostEqual(total_entropy, 20.3317505, 3)
        
    def test_entropy2(self):
        _, avg_entropy, _, _, _, _ = self.metric.entropy()
        self.assertAlmostEqual(avg_entropy, 6.7772501, 3)
    
    def test_entropy3(self):
        _, _, components_entropies, _, _, _ = self.metric.entropy()
        self.assertAlmostEqual(components_entropies['comp1'], 10.1978428, 3)
        
    def test_entropy4(self):
        _, _, components_entropies, _, _, _ = self.metric.entropy()
        self.assertAlmostEqual(components_entropies['comp2'], 3.5497985, 3)
        
    def test_entropy5(self):
        _, _, components_entropies, _, _, _ = self.metric.entropy()
        self.assertAlmostEqual(components_entropies['comp3'], 6.5841091, 3)
        
    def test_entropy6(self):
        _, _, _, req_entropies, _, _ = self.metric.entropy()
        self.assertAlmostEqual(req_entropies['comp1',1,1], 2.5210272, 3)
        
    def test_entropy7(self):
        _, _, _, req_entropies, _, _ = self.metric.entropy()
        self.assertAlmostEqual(req_entropies['comp1',1,2], 2.3826814, 3)
        
    def test_entropy8(self):
        _, _, _, _, fp_entropies, _ = self.metric.entropy()
        self.assertAlmostEqual(fp_entropies[3], 0.8899750, 3)
        
    def test_entropy9(self):
        _, _, _, _, _, object_entropies = self.metric.entropy()
        self.assertAlmostEqual(object_entropies[3], 0.5287712, 3)

    def test_pmi1(self):
        pmis = self.metric.pmi()
        self.assertAlmostEqual(pmis[(1,1)], -0.862, 3)
        self.assertAlmostEqual(pmis[(3,2)], 1.2895, 3)

    def test_pmi2(self):
        # choose a timestamp one day ago to guarantee no reqs exist
        when = time.time() - (60*60*24)
        pmis = self.metric.pmi(None, when)
        self.assertEqual(len(pmis), 0)
        
    def test_pmi3(self):
        pmis = self.metric.pmi(None, self.midtime)
        self.assertAlmostEqual(pmis[(1,1)], -0.5849, 3)
        self.assertAlmostEqual(pmis[(2,1)], 0.4150, 3)
        
def suite():
    return unittest.makeSuite(RequirementMetricTestCase, 'test')

if __name__ == '__main__':
    unittest.main()
