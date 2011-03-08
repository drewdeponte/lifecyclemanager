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
from trac.requirement.model import Requirement
from trac.requirement.model import RequirementWikiCache
from trac.requirement.model import RequirementTicketCache
from trac.requirement.model import Object
from trac.requirement.model import Fp
from trac.requirement.model import Hyponym
from trac.test import EnvironmentStub, Mock

import unittest, time
    
class RequirementTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.requirement = Requirement(self.env)

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
        # A healthy list of requirements
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
        
        self.env.config.set('requirement-custom', 'foo', 'text')
        self.env.config.set('requirement-custom', 'cbon', 'checkbox')
        self.env.config.set('requirement-custom', 'cboff', 'checkbox')
        
    def _insert_requirement(self, description, **kw):
        """Helper for inserting a requirement into the database"""
        requirement = Requirement(self.env)
        for k,v in kw.items():
            requirement[k] = v
        return requirement.insert()
    
    def _create_a_requirement(self):
        requirement = Requirement(self.env)
        requirement['component'] = 'component1'
        requirement['fp'] = 1
        requirement['object'] = 1
        requirement['creator'] = 'bob'
        requirement['description'] = 'Foo'
        requirement['foo'] = 'This is a custom field'
        return requirement

    def test_create_requirement_1(self):
        requirement = self._create_a_requirement()
        self.assertEqual('bob', requirement['creator'])
        self.assertEqual('Foo', requirement['description'])
        self.assertEqual('This is a custom field', requirement['foo'])
        requirement.insert()
        
    def test_create_requirement_2(self):
        requirement = self._create_a_requirement()
        requirement.insert()
        # Retrieving requirement
        requirement2 = Requirement(self.env, 'component1', 1, 1)
        self.assertEqual('component1', requirement2.component)
        self.assertEqual(1, requirement2.fp)
        self.assertEqual(1, requirement2.object)
        self.assertEqual('bob', requirement2['creator'])
        self.assertEqual('Foo', requirement2['description'])
        self.assertEqual('This is a custom field', requirement2['foo'])
        
    def _modify_a_requirement(self):
        requirement2 = self._create_a_requirement()
        requirement2.insert()
        requirement2['description'] = 'Bar'
        requirement2['foo'] = 'New value'
        requirement2.save_changes('santa', 'this is my comment')
        return requirement2

    def test_create_requirement_3(self):
        self._modify_a_requirement()
        # Retrieving requirement
        requirement3 = Requirement(self.env, 'component1', 1, 1)
        self.assertEqual('component1', requirement3.component)
        self.assertEqual(1, requirement3.fp)
        self.assertEqual(1, requirement3.object)
        self.assertEqual(requirement3['creator'], 'bob')
        self.assertEqual(requirement3['description'], 'Bar')
        self.assertEqual(requirement3['foo'], 'New value')

    def test_create_requirement_4(self):
        requirement3 = self._modify_a_requirement()
        # Testing get_changelog()
        log = requirement3.get_changelog()
        self.assertEqual(len(log), 3)
        ok_vals = ['foo', 'description', 'comment']
        #self.failUnless(log[0]['field'] in ok_vals)
        #self.failUnless(log[1]['field'] in ok_vals)
        #self.failUnless(log[2]['field'] in ok_vals)
        
    def test_create_requirement_duplicate(self):
        requirement1 = Requirement(self.env)
        requirement1['component'] = 'component1'
        requirement1['fp'] = 1
        requirement1['object'] = 1
        requirement1['creator'] = 'john'
        requirement1['description'] = 'foo'
        requirement1.insert()
        
        requirement2 = Requirement(self.env)
        requirement2['component'] = 'component1'
        requirement2['fp'] = 1
        requirement2['object'] = 1
        requirement2['creator'] = 'cindy'
        requirement2['description'] = 'bar'

        self.assertRaises(TracError, Requirement.insert, requirement2)

    def test_requirement_default_values(self):
        """
        Verify that a requirement uses default values specified in the configuration
        when created.
        """

        # Add a custom field of type 'text' with a default value
        self.env.config.set('requirement-custom', 'foo', 'text')
        self.env.config.set('requirement-custom', 'foo.value', 'Something')

        # Add a custom field of type 'select' with a default value specified as
        # the value itself
        self.env.config.set('requirement-custom', 'bar', 'select')
        self.env.config.set('requirement-custom', 'bar.options', 'one|two|three')
        self.env.config.set('requirement-custom', 'bar.value', 'two')

        # Add a custom field of type 'select' with a default value specified as
        # index into the options list
        self.env.config.set('requirement-custom', 'baz', 'select')
        self.env.config.set('requirement-custom', 'baz.options', 'one|two|three')
        self.env.config.set('requirement-custom', 'baz.value', '2')

        requirement = Requirement(self.env)
        self.assertEqual('Something', requirement['foo'])
        self.assertEqual('two', requirement['bar'])
        self.assertEqual('three', requirement['baz'])

    def test_set_field_stripped(self):
        """
        Verify that whitespace around requirement fields is stripped, except for
        textarea fields.
        """
        requirement = Requirement(self.env)
        requirement['component'] = '  component1  '
        requirement['fp'] = 4
        requirement['object'] = 8
        requirement['description'] = '  bar  '
        self.assertEqual('component1', requirement['component'])
        self.assertEqual(4, requirement['fp'])
        self.assertEqual(8, requirement['object'])
        self.assertEqual('  bar  ', requirement['description'])
        
    def test_get_components(self):
        requirement = Requirement(self.env)
        self.assertEqual(requirement.get_components(),
                         ['comp1','comp2','comp3'])

    def test_get_components_metrics1(self):
        requirement = Requirement(self.env)
        self.assertEqual(requirement.get_components_metrics(),
                         (['comp1','comp2','comp3'],
                          {'comp1': 5,
                           'comp2': 2,
                           'comp3': 4}))

    def test_get_components_metrics2(self):
        requirement = Requirement(self.env)
        
        # choose a timestamp one day ago to guarantee no reqs exist
        when = time.time() - (60*60*24)
        
        self.assertEqual(requirement.get_components_metrics(None, when),
                         ([],{}))

    def test_get_components_metrics3(self):
        requirement = Requirement(self.env)
        self.assertEqual(requirement.get_components_metrics(None, self.midtime),
                         (['comp1','comp2'],
                          {'comp1': 3,
                           'comp2': 1}))
                         
    def test_get_fps1(self):
        # Test get_fps which returns a list of fps
        # dict = False (default) ->  list of fp ids enabled stated 
        #       during the timestamp given.
        # dict = True -> return dictionary eg {'id':'name'}
        # This test is for the default case see next test case

        requirement = Requirement(self.env)
        result = [1,2,3,4]
        self.assertEqual(requirement.get_fps(), result)

    def test_get_fps2(self):
        # Test get_fps with dictionary set to True
        # When dict=True, returns type is a dicitonary
        # eg {'id':'name'}
        # See test_get_fps1()

        requirement = Requirement(self.env)
        result = {}
        result[1] = u'fp1'
        result[2] = u'fp2'
        result[3] = u'fp3'
        result[4] = u'fp4'
        self.assertEqual(requirement.get_fps(None, None, True), result)

    def test_get_fps3(self):
        # Test get_fps with timestamp set to somthing other than None
        # When timstamp is given fps is given fps given to that point
        # See test_get_fps1()

        requirement = Requirement(self.env)
        
        # choose a timestamp one day ago to guarantee no fps exist
        when = time.time() - (60*60*24)
        self.assertEqual(requirement.get_fps(None, when, False), [])

    def test_get_fp_metrics1(self):
        # test base case
        requirement = Requirement(self.env)
        fps = [1,2,3,4]
        fps_obj = {}
        fps_obj[1] = {1: 1, 2: 1, 3: 2, 4: 1}
        fps_obj[2] = {1: 2}
        fps_obj[3] = {1: 1, 2: 2}
        fps_obj[4] = {4: 1}
        fps_counts  = {1: 5, 2: 2, 3: 3, 4: 1}
        list = (fps, fps_obj, fps_counts)
        self.assertEqual(requirement.get_fp_metrics(), list)
        
    def test_get_fp_metrics2(self):
        # test timestamp
        requirement = Requirement(self.env)
        
        # choose a timestamp one day ago to guarantee no fps exist
        when = time.time() - (60*60*24)
        
        fps = []
        fps_obj = {}
        fps_counts  = {}
        list = (fps, fps_obj, fps_counts)
        self.assertEqual(requirement.get_fp_metrics(None, when), list)
        
    def test_get_fp_metrics3(self):
        # test base case
        requirement = Requirement(self.env)
        fps = [1,2]
        fps_obj = {}
        fps_obj[1] = {1: 1, 2: 1}
        fps_obj[2] = {1: 2}
        fps_counts  = {1: 2, 2: 2}
        list = (fps, fps_obj, fps_counts)
        self.assertEqual(requirement.get_fp_metrics(None, self.midtime), list)
        
    def test_get_objects1(self):
        # tests default non-dict case
        object = Object(self.env)
        self.assertEqual(object.get_objects(),
                         [1, 2, 3, 4])
                         
    def test_get_objects2(self):
        # tests dict case
        object = Object(self.env)
        result = {}
        result[1] = u'obj1'
        result[2] = u'obj2'
        result[3] = u'obj3'
        result[4] = u'obj4'
        self.assertEqual(object.get_objects(None, None, True), result)

    def test_get_objects3(self):
        # tests timestamp non-dict case
        # before any reqs have been defined
        object = Object(self.env)
        
        # choose a timestamp one day ago to guarantee no objs exist
        when = time.time() - (60*60*24)
        self.assertEqual(object.get_objects(None, when, False), [])
        
    def test_get_objects4(self):
        # tests timestamp non-dict case
        # when only some reqs have been defined
        object = Object(self.env)
        
        # use midtime to get only part of the reqs
        self.assertEqual(object.get_objects(None, self.midtime, False), [1,2])
        
    def test_get_object_metrics(self):
        requirement = Requirement(self.env)
        obj = [1,2,3,4]
        obj_fps = {}
        obj_fps[1] = {1: 1, 2: 2, 3: 1}
        obj_fps[2] = {1: 1, 3: 2}
        obj_fps[3] = {1: 2}
        obj_fps[4] = {1: 1, 4: 1}
        obj_counts = {1: 4, 2: 3, 3: 2, 4: 2}
        list = (obj, obj_fps, obj_counts)
        self.assertEqual(requirement.get_object_metrics(), list)

    def test_get_object_metrics2(self):
        # tests a time stamp one day ago to guarantee no objs exist 
        requirement = Requirement(self.env)
        when = time.time() - (60*60*24)
        result = ([], {}, {})
        self.assertEqual(requirement.get_object_metrics(None, when), result)


    def test_get_objects_prefix_1(self):
        requirement = Requirement(self.env)
        obj = Object(self.env)
        obj['name']= 'testobj'
        obj.insert()
        self.assertEqual(requirement.get_objects_prefix('t'),
                         [(obj['name'],'')])

    def test_get_objects_prefix_2(self):
        requirement = Requirement(self.env)
        requirement['description'] = 'bar'
        self.assertEqual(requirement.get_objects_prefix(''),
                         [('obj1',''),('obj2',''),('obj3',''),('obj4','')])

    def test_get_requirements_matrix1(self):
        # test base case
        requirement = Requirement(self.env)
        matrix = requirement.get_requirements_matrix()
        self.assertEqual(matrix[1][1], 1)
        self.assertEqual(matrix[3][2], 2)
        self.assertEqual(matrix[1][4], 1)

    def test_get_requirements_matrix2(self):
        # test with timestamp
        # before any reqs have been defined
        requirement = Requirement(self.env)
        
        # choose a timestamp one day ago to guarantee no reqs exist
        when = time.time() - (60*60*24)
        matrix = requirement.get_requirements_matrix(None, None, when)
        self.assertEqual(len(matrix), 0)
        
    def test_get_requirements_matrix3(self):
        # test with timestamp
        # when some reqs have been defined
        requirement = Requirement(self.env)
        
        # use midtime so that only some reqs are defined
        matrix = requirement.get_requirements_matrix(None, None, self.midtime)
        self.assertEqual(matrix[1][1], 1)
        self.assertEqual(matrix[1][2], 1)
        self.assertEqual(matrix[2][1], 2)
        
    def test_get_requirements_matrix_rowsum(self):
        requirement = Requirement(self.env)
        matrix = requirement.get_requirements_matrix()
        self.assertEqual(requirement.get_requirements_matrix_rowsum(matrix, 1), 5)
        self.assertEqual(requirement.get_requirements_matrix_rowsum(matrix, 3), 3)
        self.assertEqual(requirement.get_requirements_matrix_rowsum(matrix, 4), 1)

    def test_get_requirements_matrix_colsum(self):
        requirement = Requirement(self.env)
        matrix = requirement.get_requirements_matrix()
        self.assertEqual(requirement.get_requirements_matrix_colsum(matrix, 1), 4)
        self.assertEqual(requirement.get_requirements_matrix_colsum(matrix, 2), 3)
        self.assertEqual(requirement.get_requirements_matrix_colsum(matrix, 4), 2)

    def test_get_requirements_count(self):
        requirement = Requirement(self.env)
        matrix = requirement.get_requirements_matrix()
        self.assertEqual(requirement.get_requirements_count(matrix), 11)

    def test_get_pairings(self):
        requirement = Requirement(self.env)
        self.assertEqual(requirement.get_pairings(), 
                         [(1,1),(1,2), \
                          (1,3), (1,4), \
                          (2,1), (3,1), \
                          (3,2), (4,4)])
        
    def test_get_component_req_count(self):
        requirement = Requirement(self.env)
        cursor = self.env.db.cursor()
        cursor.execute("INSERT INTO component (name) "
                       "VALUES('longer_comp_name')")
        self.assertEqual(requirement.get_component_req_count(),
                         [('            comp1', 5),
                          ('            comp2', 2),
                          ('            comp3', 4),
                          (' longer_comp_name', 0)])
 
    def test_get_changed_reqs_since_validation(self):
        
        cursor = self.env.db.cursor()
        cursor.execute("INSERT INTO requirement_validation (date,uid) "
                       "VALUES ('8','santa')")
        testreq = Requirement(self.env, component='comp1', fp=1, object=2)
        testreq['status'] = 'out-of-date'
        testreq['description'] = 'I am a description!'
        testreq.save_changes('Bob', 'ood', when=24)

        self.assertEqual((1,1),testreq.get_changed_reqs_since_validation())

    def test_get_changed_reqs_since_validation2(self):
        Requirement(self.env).validate_requirements()
        testreq = Requirement(self.env)

        self.assertEqual((0,0),testreq.get_changed_reqs_since_validation())

    def test_get_type_req_tickets(self):
        cursor = self.env.db.cursor()

        cursor.execute("INSERT INTO ticket (id, status, description) "
                       "VALUES (1, 'closed', '<comp1 1 1>')")

        cursor.execute("INSERT INTO requirement_ticket_cache (component, fp, object, ticket) "
                       "VALUES ('comp1', 'fp1', 'obj1', 1)")

        self.assertEqual([0,1,10], Requirement(self.env).get_type_req_tickets())

        cursor.execute("INSERT INTO ticket (id, status, description) "
                       "VALUES (2, 'new', '<comp1 2 1>')")

        cursor.execute("INSERT INTO requirement_ticket_cache (component, fp, object, ticket) "
                       "VALUES ('comp1', 'fp2', 'obj1', 2)")

        self.assertEqual([1,1,9], Requirement(self.env).get_type_req_tickets())

        cursor.execute("INSERT INTO ticket (id, status, description) "
                       "VALUES (3, 'new', '<comp3 4 4>')")

        cursor.execute("INSERT INTO requirement_ticket_cache (component, fp, object, ticket) "
                       "VALUES ('comp3', 'fp4', 'obj4', 3)")

        self.assertEqual([2,1,8], Requirement(self.env).get_type_req_tickets())

        cursor.execute("INSERT INTO ticket (id, status, description) "
                       "VALUES (4, 'closed', '<comp3 4 4>')")

        cursor.execute("INSERT INTO requirement_ticket_cache (component, fp, object, ticket) "
                       "VALUES ('comp3', 'fp4', 'obj4', 4)")

        self.assertEqual([2,1,8], Requirement(self.env).get_type_req_tickets())

    def test_set_ood_by_fp(self):
        """
        Note: It is not possible to check for race conditions in
        this test case, because there would be two comments saved in 
        less than a second, which gives our database integrity errors.
        However, they have been visually be tested on the web interface
        and there are no errors due to race conditions, but collisions 
        are still possible if two different things commit at the same time.
        """
        #create fp.
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("INSERT INTO fp (id, name, status) "
                       "VALUES (5982, 'fish', 'enabled') ")

        my_req = Requirement(self.env)
        my_req['component'] = 'comp1'
        my_req['fp'] = 5982
        my_req['object'] = 2
        my_req.insert()
        #disable fp.
        my_fp = Fp(self.env, id=5982)
        my_fp['status'] = 'disabled'
        my_fp.save_changes('God', 'I felt like it') 
        my_req = Requirement(self.env, component='comp1',
                             fp=5982, object=2)
        self.assertEqual(my_req['status'], 'out-of-date')

    def test_get_val_times(self):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("INSERT INTO requirement_validation (date, uid) "
                       "VALUES (1010, 'birthday') ")
        my_req = Requirement(self.env)
        val_times = my_req.get_val_times()
        self.assertEqual([1010],val_times)

    def test_get_num_req(self):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("INSERT INTO requirement (component,fp,object,time) "
                       "VALUES (1,2,3,4) ")
        my_req = Requirement(self.env)
        num_req = my_req.get_num_req(5)
        self.assertEqual(1,num_req)
 
    def test_get_num_req2(self):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("INSERT INTO requirement (component,fp,object,time) "
                       "VALUES (1,2,3,4) ")
        my_req = Requirement(self.env)
        num_req = my_req.get_num_req(3)
        self.assertEqual(0,num_req)

    def test_enable_ood_by_fp(self):

        #create fp.
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("INSERT INTO fp (id, name, status) "
                       "VALUES (99, 'borg', 'disabled') ")

        my_req = Requirement(self.env)
        my_req['component'] = 'comp1'
        my_req['fp'] = 99
        my_req['object'] = 2
        my_req.insert()
        self.assertEqual(my_req['status'], 'out-of-date')
        #enable fp
        my_fp = Fp(self.env, id=99)
        my_fp['status'] = 'enabled'
        my_fp.save_changes('fishes', 'we are one')
        my_req = Requirement(self.env, component='comp1',
                             fp=99, object=2)
        self.assertEqual(my_req['status'], 'enabled')

    def test_set_ood_by_object(self):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("INSERT INTO object (id, name, status) "
                       "VALUES (78, 'fishes', 'enabled') ")

        my_req = Requirement(self.env)
        my_req['component'] = 'comp1'
        my_req['fp'] = 1
        my_req['object'] = 78
        my_req.insert()
        
        my_obj = Object(self.env, id=78)
        my_obj['status'] = 'disabled'
        my_obj.save_changes('Persirailimus', 'Is better than god') 
        my_req = Requirement(self.env, component='comp1',
                             fp=1, object=78)
        self.assertEqual(my_req['status'], 'out-of-date')

    def test_enable_ood_by_object(self):

        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("INSERT INTO object (id, name, status) "
                       "VALUES (9009, 'ror', 'disabled') ")

        my_req = Requirement(self.env)
        my_req['component'] = 'comp1'
        my_req['fp'] = 2
        my_req['object'] = 9009
        my_req.insert()
        self.assertEqual(my_req['status'], 'out-of-date')

        my_obj = Object(self.env, id=9009)
        my_obj['status'] = 'enabled'
        my_obj.save_changes('fishes', 'are not food!')
        my_req = Requirement(self.env, component='comp1',
                             fp=2, object=9009)
        self.assertEqual(my_req['status'], 'enabled')

class RequirementWikiCacheTestCase(unittest.TestCase):
    """Class to group test cases for the RequirementWikiCache model.
    
    This class is specificly designed to group test cases and unit
    tests into one class so that they may be integrated into the
    standard python unittest modules unit testing framework.
    """

    def setUp(self):
        """Setup the test case environment.
        
        This is used to setup the initial environment for the rest of
        the tests.
        """
        
        self.env = EnvironmentStub()
        self.requirement_wiki_cache = RequirementWikiCache(self.env)

        cursor = self.env.db.cursor()
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
        
    def _create_a_req_wiki_cache(self):
        """Create a predifined requirement to wiki relationship object.
        
        Create a requirement to wiki relationship object with static
        predefined values so that the RequirementWikiCache objects
        used in the test are consistent with respect to their values.
        """
        
        req_wiki_cache = RequirementWikiCache(self.env, 'comp1', 'open', 'door', 'footest', '1')
        return req_wiki_cache

    def test_create_req_wiki_cache_1(self):
        """Test creation of a RequirementWikiCache object.
        
        This creates the predefined RequirementWikiCache object and
        tests to make sure the values match their associated predefined
        values after creation is complete.
        """        
        req_wiki_cache = self._create_a_req_wiki_cache()
        self.assertEqual('comp1', req_wiki_cache.component)
        self.assertEqual('open', req_wiki_cache.fp)
        self.assertEqual('door', req_wiki_cache.object)
        self.assertEqual('footest', req_wiki_cache.wiki_name)
        self.assertEqual('1', req_wiki_cache.wiki_version)
        self.assertEqual(False, req_wiki_cache.exists)

    def test_create_req_wiki_cache_2(self):
        """Test creation and insertion of RequirementWikiCache object.
        
        This creates the predefined RequirementWikiCache object and
        then performs an insert on it. Once the insert is complete
        it creates a secondary RequirementWikiCache object with the
        same values as the predefined one, and then checks to make sure
        that the values match the predefined ones and that it has been
        properly inserted into the database.
        """
        
        req_wiki_cache = self._create_a_req_wiki_cache()
        req_wiki_cache.insert()
        req_wiki_cache2 = RequirementWikiCache(self.env, 'comp1', 'open', 'door', 'footest', '1')
        self.assertEqual('comp1', req_wiki_cache2.component)
        self.assertEqual('open', req_wiki_cache2.fp)
        self.assertEqual('door', req_wiki_cache2.object)
        self.assertEqual('footest', req_wiki_cache2.wiki_name)
        self.assertEqual('1', req_wiki_cache2.wiki_version)
        self.assertEqual(True, req_wiki_cache2.exists)
        
    def test_delete_req_wiki_cache_1(self):
        """Test deletion of a requirement to wiki relationship.
        
        This creates the predefined RequirementWikiCache object and
        then performs an insert on it. Once the insert is complete it
        creates a secondary RequirementWikiCache object using the same
        values as the predefined one. It then deletes the relationship
        using the secondary object. Then it creates a third instance of
        RequirementWikiCache class using still the same predefined
        values and verifies that the relationship is no longer in the
        database.
        """
        
        req_wiki_cache = self._create_a_req_wiki_cache()
        req_wiki_cache.insert()
        req_wiki_cache2 = RequirementWikiCache(self.env, 'comp1', 'open', 'door', 'footest', '1')
        req_wiki_cache2.delete()
        req_wiki_cache3 = RequirementWikiCache(self.env, 'comp1', 'open', 'door', 'footest', '1')
        self.assertEqual('comp1', req_wiki_cache3.component)
        self.assertEqual('open', req_wiki_cache3.fp)
        self.assertEqual('door', req_wiki_cache3.object)
        self.assertEqual('footest', req_wiki_cache3.wiki_name)
        self.assertEqual('1', req_wiki_cache3.wiki_version)
        self.assertEqual(False, req_wiki_cache3.exists)
        
    def test_delete_req_wiki_cache_by_page_1(self):
        """Test deletion of a requirement to wiki relationships for a wiki page.
        
        This creates the predefined RequirementWikiCache object and
        then performs an insert on it. Once the insert is complete it
        creates a secondary RequirementWikiCache object relating the
        same predefined requirement to the same predifined wiki page,
        however to a different version. It then inserts the secondary
        relationship. Then it creates a third relationship object
        using the predefined values and tells it to delete relationships
        matching the predefined values neglecting the wiki page version.
        Then it creates a fourth and fifth relationship object using the
        predefined values and verifies that the relationships have
        been removed from the database table.
        """
        
        req_wiki_cache = self._create_a_req_wiki_cache()
        req_wiki_cache.insert()
        req_wiki_cache2 = RequirementWikiCache(self.env, 'comp1','open','door','footest','2')
        req_wiki_cache2.insert()
        req_wiki_cache3 = RequirementWikiCache(self.env, 'comp1','open','door','footest','1')
        req_wiki_cache3.delete_by_page()
        req_wiki_cache4 = RequirementWikiCache(self.env, 'comp1','open','door','footest','1')
        self.assertEqual('comp1', req_wiki_cache4.component)
        self.assertEqual('open', req_wiki_cache4.fp)
        self.assertEqual('door', req_wiki_cache4.object)
        self.assertEqual('footest', req_wiki_cache4.wiki_name)
        self.assertEqual('1', req_wiki_cache4.wiki_version)
        self.assertEqual(False, req_wiki_cache4.exists)
        req_wiki_cache5 = RequirementWikiCache(self.env, 'comp1','open','door','footest','2')
        self.assertEqual('comp1', req_wiki_cache5.component)
        self.assertEqual('open', req_wiki_cache5.fp)
        self.assertEqual('door', req_wiki_cache5.object)
        self.assertEqual('footest', req_wiki_cache5.wiki_name)
        self.assertEqual('2', req_wiki_cache5.wiki_version)
        self.assertEqual(False, req_wiki_cache5.exists)
        
    def test_update_req_wiki_cache_1(self):
        """Test updating of a requirement to wiki relationship.
        
        This creates the predefined RequirementWikiCache object and
        inserts it into the database table. Then it creates a secondary
        RequirementWikiCache object using the predefined values and
        checks to verify that it is in the database. Then it performs
        an update.
        """
        
        req_wiki_cache = self._create_a_req_wiki_cache()
        req_wiki_cache.insert()
        req_wiki_cache2 = RequirementWikiCache(self.env,'comp1','open','door','footest','1')
        self.assertEqual('comp1', req_wiki_cache2.component)
        self.assertEqual('open', req_wiki_cache2.fp)
        self.assertEqual('door', req_wiki_cache2.object)
        self.assertEqual('footest', req_wiki_cache2.wiki_name)
        self.assertEqual('1', req_wiki_cache2.wiki_version)
        self.assertEqual(True, req_wiki_cache2.exists)
        req_wiki_cache2.update()
 
class RequirementTicketCacheTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.requirement_ticket_cache = RequirementTicketCache(self.env)

        cursor = self.env.db.cursor()
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
        
    def _create_a_req_ticket_cache(self):
        req_ticket_cache = RequirementTicketCache(self.env, 1, 'comp1', 'open', 
                                          'door')
        return req_ticket_cache

    def test_create_req_ticket_cache_1(self):
        req_ticket_cache = self._create_a_req_ticket_cache()
        self.assertEqual('comp1', req_ticket_cache.component)
        self.assertEqual('open', req_ticket_cache.fp)
        self.assertEqual('door', req_ticket_cache.object)
        self.assertEqual(1, req_ticket_cache.ticket_id)
        self.assertEqual(False, req_ticket_cache.ticket_in_table)
        self.assertEqual(False, req_ticket_cache.exists)
        req_ticket_cache.insert()
        self.assertEqual(True, req_ticket_cache.ticket_in_table)
        self.assertEqual(True, req_ticket_cache.exists)

    def test_create_req_ticket_cache_2(self):
        req_ticket_cache = self._create_a_req_ticket_cache()
        req_ticket_cache.insert()
        req_ticket_cache2 = RequirementTicketCache(self.env, 1, 'comp1', 
                                                   'open', 'door')
        self.assertEqual('comp1', req_ticket_cache2.component)
        self.assertEqual('open', req_ticket_cache2.fp)
        self.assertEqual('door', req_ticket_cache2.object)
        self.assertEqual(1, req_ticket_cache2.ticket_id)
        self.assertEqual(True, req_ticket_cache.ticket_in_table)
        self.assertEqual(True, req_ticket_cache.exists)

    def test_delete_req_ticket_cache_1(self):
        req_ticket_cache = self._create_a_req_ticket_cache()
        req_ticket_cache.insert()
        req_ticket_cache2 = RequirementTicketCache(self.env, 1, 'comp2', 
                                                   'close', 'window')
        req_ticket_cache2.insert()
        req_ticket_cache3 = RequirementTicketCache(self.env, 1, 'comp2', 
                                                   'close', 'window')
        req_ticket_cache3.delete()
        req_ticket_cache4 = RequirementTicketCache(self.env, 1, 'comp1', 
                                                   'open', 'door')
        req_ticket_cache5 = RequirementTicketCache(self.env, 1, 'comp2', 
                                                   'close', 'window')
        self.assertEqual('comp1', req_ticket_cache4.component)
        self.assertEqual('open', req_ticket_cache4.fp)
        self.assertEqual('door', req_ticket_cache4.object)
        self.assertEqual(1, req_ticket_cache4.ticket_id)
        self.assertEqual(False, req_ticket_cache4.ticket_in_table)
        self.assertEqual(False, req_ticket_cache4.exists)
        self.assertEqual(False, req_ticket_cache5.exists)

class ObjectTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub()
        self.object = Object(self.env)

        cursor = self.env.db.cursor()
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
        query = "INSERT into object (name,description,status,id) " + \
                "values ('create', 'foo desc', 'tooshy', '543')"
        cursor.execute(query)
        
        query = "INSERT into object (name,description,status,id) " + \
                "values ('squish', 'bar desc', 'BAM!', '24')"
        cursor.execute(query)

    def test_create_obj_given_nothing(self):
        my_object = Object(self.env)
        self.assertEqual(None, my_object.obj_id)
        self.assertEqual(None, my_object.time_created)
        self.assertEqual(None, my_object.time_changed)
        self.assertEqual(0, len(my_object.values))

    def test_insert_given_nothing(self):
        my_object = Object(self.env)
        my_object['name'] = 'fart'
        my_object['description'] = 'bar'
        my_object['status'] = 'bad'
        my_object.insert()

        self.assertNotEqual(None, my_object['id'])
        self.assertEqual('fart', my_object['name'])
        self.assertEqual('bar', my_object['description'])
        self.assertEqual('enabled', my_object['status'])

        cursor = self.env.db.cursor()
        cursor.execute("SELECT id from object WHERE name = 'fart' AND" +
                       " description = 'bar' AND status = 'enabled'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], my_object['id'])        

    def test_insert_given_time(self):
        my_object = Object(self.env)
        my_object['name'] = 'gwen'
        my_object['description'] = 'bar'
        my_object['status'] = 'bad'
        
        my_object.insert(when=23)

        cursor = self.env.db.cursor()
        cursor.execute("SELECT description,status,time,changetime" +
                        " from object WHERE name = 'gwen'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], my_object['description'])
        self.assertEqual(row[1], 'enabled')
        self.assertEqual(row[2], my_object.time_created)
        self.assertEqual(row[3], my_object.time_changed)
 
    def test_create_obj_given_good_name(self):
        
        my_object = Object(self.env, name='create' )
        self.assertEqual(543, my_object['id'])
        self.assertEqual('create', my_object['name'])
        self.assertEqual('foo desc', my_object['description'])
        self.assertEqual('tooshy', my_object['status'])

    def test_create_obj_given_good_id(self):
        
        my_object = Object(self.env, id = 543)
        self.assertEqual(543, my_object['id'])
        self.assertEqual('create', my_object['name'])
        self.assertEqual('foo desc', my_object['description'])
        self.assertEqual('tooshy', my_object['status'])
       
    def test_create_obj_given_good_name_and_id(self):
         
        my_object = Object(self.env, id = 543, name='create')
        self.assertEqual(543, my_object['id'])
        self.assertEqual('create', my_object['name'])
        self.assertEqual('foo desc', my_object['description'])
        self.assertEqual('tooshy', my_object['status'])
                          
    def test_create_obj_given_bad_name(self):
        mybool = None
        try: 
            my_object = Object(self.env, name = 'notthere')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)

    def test_create_obj_given_bad_id(self):

        mybool = None
        try: 
            my_object = Object(self.env, id = 42)
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)
    
    def test_create_obj_given_unmatching_id_name(self):

        mybool = None
        try: 
            my_object = Object(self.env, id = 24, name = 'create')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)

    def test_create_obj_given_missing_id_and_existing_name(self):

        mybool = None
        try: 
            my_object = Object(self.env, id = 812, name = 'create')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)

    def test_create_obj_given_missing_name_and_existing_id(self):

        mybool = None
        try: 
            my_object = Object(self.env, id = 24, name = 'fudge')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)


    def test_populate_with_values(self):
        values = {'name': 'foo', 'description': 'footest', 'status': 'enabled'}
        my_object = Object(self.env)

        my_object.populate(values)

        self.assertEqual(my_object.values['name'], 'foo')
        self.assertEqual(my_object.values['description'], 'footest')
        self.assertEqual(my_object.values['status'], 'enabled')

    def test_save_changes_given_nothing(self):
        
        values = {'name': 'foo', 'description': 'footest', 'status': 'enabled'}
        my_object = Object(self.env)
        my_object.populate(values)
        my_object.insert()

        my_object['description'] = 'yo mamma so foo'
        my_object['status'] = 'disabled'
        my_object.save_changes('me','because')
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT description,status FROM object WHERE name = 'foo'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 'yo mamma so foo')
        self.assertEqual(row[1], 'disabled')
        
    def test_save_changes_given_time(self):
        
        values = {'name': 'foo', 'description': 'footest', 'status': 'enabled'}
        my_object = Object(self.env)
        my_object.populate(values)
        my_object.insert(when=52)

        my_object['description'] = 'yo mamma so foo'
        my_object['status'] = 'disabled'
        my_object.save_changes('me','because',when=25)
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT time,changetime FROM object WHERE name = 'foo'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 52)
        self.assertEqual(row[1], 25)


    def test_save_changes_given_cnum(self):

        values = {'name': 'foo', 'description': 'footest', 'status': 'enabled'}
        my_object = Object(self.env)
        my_object.populate(values)
        my_object.insert(when=52)

        my_object['description'] = 'yo mamma so foo'
        my_object['status'] = 'disabled'
        my_object.save_changes('me','because',cnum=40)
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT oldvalue FROM object_change WHERE id =%s" %
                      my_object.values['id'])

        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], '40')

    def test_save_changes_given_cnum_and_time(self):

        values = {'name': 'foo', 'description': 'footest', 'status': 'enabled'}
        my_object = Object(self.env)
        my_object.populate(values)
        my_object.insert(when=52)

        my_object['description'] = 'yo mamma so foo'
        my_object['status'] = 'disabled'
        my_object.save_changes('me','because',cnum=40, when=25)
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT oldvalue FROM object_change WHERE id =%s" %
                      my_object.values['id'])

        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], '40')

        cursor.execute("SELECT time,changetime FROM object WHERE name = 'foo'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 52)
        self.assertEqual(row[1], 25)

    def test_get_changelog_given_no_args(self):
        
        values = {'name': 'foo', 'description': 'footest', 'status': 'enabled'}
        my_object = Object(self.env)
        my_object.populate(values)

        my_object.insert()
        my_object['description'] = 'yo mamma so foo'
        my_object.save_changes('me','because',cnum=4)
        
        my_log = my_object.get_changelog()
        for record in my_log:
            time, author, field, oldvalue, newvalue = record

            if field == 'comment':

                self.assertEqual(author, 'me')
                self.assertEqual(field, 'comment')
                self.assertEqual(oldvalue, '4')
                self.assertEqual(newvalue, 'because')

            else:
                self.assertEqual(author, 'me')
                self.assertEqual(field, 'description')
                self.assertEqual(oldvalue, 'footest')
                self.assertEqual(newvalue, 'yo mamma so foo')
        
    def test_get_changelog_given_time(self):
        
        values = {'name': 'foo', 'description': 'footest', 'status': 'enabled'}
        my_object = Object(self.env)
        my_object.populate(values)

        my_object.insert()
        my_object['description'] = 'yo mamma so foo'
        my_object.save_changes('me','because',cnum=4,when=65)

        my_object['description'] = 'bee kowz'
        my_object.save_changes('me','mattresses',cnum=5,when=69)
        
        my_log = my_object.get_changelog(when=65)
        for record in my_log:
            time, author, field, oldvalue, newvalue = record

            if field == 'comment':

                self.assertEqual(author, 'me')
                self.assertEqual(field, 'comment')
                self.assertEqual(oldvalue, '4')
                self.assertEqual(newvalue, 'because')

            else:
                self.assertEqual(author, 'me')
                self.assertEqual(field, 'description')
                self.assertEqual(oldvalue, 'footest')
                self.assertEqual(newvalue, 'yo mamma so foo')


    def test_get_obj_info(self):
        cursor = self.env.db.cursor()
        cursor.execute("INSERT INTO object (name, description) "
                       "VALUES ('log', 'big, heavy, wood')")

        self.assertEqual(Object(self.env).get_obj_info(), 
                [{'name':'create', 'description':'foo desc', 
                    'status':'tooshy'},
                 {'name':'log', 'description':'big, heavy, wood', 
                    'status':''},
                 {'name':'squish', 'description':'bar desc', 
                    'status':'BAM!'}])


    def test_set_on_fly_obj(self):
        cursor = self.env.db.cursor()        
        cursor.execute("INSERT INTO on_the_fly "
                       "VALUES ('object','disabled')")
                       
        Object(self.env).set_on_fly_obj('enabled')
        cursor.execute("SELECT status FROM on_the_fly "
                       "WHERE name ='object'")
        row = cursor.fetchone()
        self.assertNotEqual(None,row)
        self.assertEqual(row[0], 'enabled')

class FpTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()

        cursor = self.env.db.cursor()
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
        query = "INSERT into fp (name,description,status,id) " + \
                "values ('fly', 'levitate', 'disabled', '10')"
        cursor.execute(query)
        
        query = "INSERT into fp (name,description,status,id) " + \
                "values ('squish', 'press', 'disabled', '300')"
        cursor.execute(query)
        
        
        
    
    def test_create_fp_with_existing_name(self):
        my_fp = Fp(self.env, name='fly')
        
        self.assertEqual('fly', my_fp['name'])
        self.assertEqual('levitate', my_fp['description'])
        self.assertEqual('disabled', my_fp['status'])
        self.assertEqual(10, my_fp['id'])

    def test_create_fp_with_wrong_name(self):
        bad_flag = None
        try:
            my_fp = Fp(self.env, name='wrong')
        except TracError:
            bad_flag = True

        self.assertEqual(True, bad_flag)

    def test_create_fp_with_existing_id(self):
        my_fp = Fp(self.env, id=300)

        self.assertEqual('squish', my_fp['name'])
        self.assertEqual('press', my_fp['description'])
        self.assertEqual('disabled', my_fp['status'])
        self.assertEqual(300, my_fp.fp_id)

    def test_create_fp_with_wrong_id(self):
        bad_flag = None
        try:
            my_fp = Fp(self.env, id=45)
        except TracError:
            bad_flag = True
    
        self.assertEqual(True, bad_flag)

    def test_create_fp_with_matched_name_and_id(self):
        my_fp = Fp(self.env, name='fly', id=10)

        self.assertEqual('fly', my_fp['name'])
        self.assertEqual('levitate', my_fp['description'])
        self.assertEqual('disabled', my_fp['status'])
        self.assertEqual(10, my_fp['id'])

    def test_create_fp_with_mismatched_name_and_id(self):
        bad_flag = None
        try:
            my_fp = Fp(self.env, name='fly', id=300)
        except TracError:
            bad_flag = True

        self.assertEqual(True, bad_flag)

    def test_populate_fp_with_good_values(self):
        #also tests initialization without parameters
        my_fp = Fp(self.env)
    
        my_fp.populate({'name':'do', 'description':'stuff',
                        'status':'bad'})

        self.assertEqual('do', my_fp['name'])
        self.assertEqual('stuff', my_fp['description'])
        self.assertEqual('bad', my_fp['status'])

    def test_populate_fp_with_bad_values(self):
        my_fp = Fp(self.env)

        my_fp.populate({'fred':'monkey', 'Dr':'Amoussou'})
        
        self.assertEqual(False,my_fp.values.has_key('fred'))
        self.assertEqual(False, my_fp.values.has_key('Dr'))
        
    def test_insert_fp_given_nothing(self):
        my_fp = Fp(self.env)
        
        my_fp.populate({'name':'grope', 'description':'to fondle',
                        'status':'disabled'})

        my_fp.insert()
        cursor = self.env.db.cursor()        
        cursor.execute("SELECT description,status,id FROM fp "
                       "WHERE name ='grope'")
        row = cursor.fetchone()
        self.assertNotEqual(None,row)
        self.assertEqual(row[0], 'to fondle')
        self.assertEqual(row[1], 'enabled')
        self.assertEqual(row[2], my_fp.fp_id)

    def test_insert_fp_given_time(self):
        my_fp = Fp(self.env)

        my_fp.populate({'name':'frag', 'description':'to pwn upon',
                        'status':'terminated'})
        my_fp.insert(when=23)
        cursor = self.env.db.cursor()
        cursor.execute("SELECT description,status,id FROM fp "
                       "WHERE name ='frag'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 'to pwn upon')
        self.assertEqual(row[1], 'enabled')
        self.assertEqual(row[2], my_fp.fp_id)
        self.assertEqual(my_fp['status'], 'enabled')

    def test_fp_save_changes_given_nothing(self):
        my_fp = Fp(self.env)
        my_fp.populate({'name':'run', 'description':'move quickly'})
        my_fp.insert()
        my_fp['description'] = 'super jog'
        my_fp.save_changes('Jesus','I shall save you')
        cursor = self.env.db.cursor()
        cursor.execute("SELECT name,description,status,time,changetime"
                       " FROM fp WHERE id=" + str(my_fp.fp_id))
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 'run')
        self.assertEqual(row[1], 'super jog')
        self.assertEqual(row[2], 'enabled')
        self.assertEqual(row[3], my_fp.time_created)
        self.assertEqual(row[4], my_fp.time_changed)
        
        cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                       "FROM fp_change WHERE id=" + str(my_fp.fp_id))
        for row in cursor:
            if row[2] == 'description':
                self.assertEqual(row[0], my_fp.time_changed)
                self.assertEqual(row[1], 'Jesus')
                self.assertEqual(row[3], 'move quickly')
                self.assertEqual(row[4], 'super jog')
            elif row[2] == 'comment':
                self.assertEqual(row[0], my_fp.time_changed)
                self.assertEqual(row[1], 'Jesus')
                self.assertEqual(row[4], 'I shall save you')
            else:
                self.assertEqual(True,False)

    def test_fp_save_changes_given_time(self):
        my_fp = Fp(self.env)
        my_fp.populate({'name':'run', 'description':'move quickly'})
        my_fp.insert(when=5)
        my_fp['description'] = 'super jog'
        my_fp.save_changes('Jesus','I shall save you',when=10)
        cursor = self.env.db.cursor()
        cursor.execute("SELECT name,description,status,time,changetime"
                       " FROM fp WHERE id=" + str(my_fp.fp_id))
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 'run')
        self.assertEqual(row[1], 'super jog')
        self.assertEqual(row[2], 'enabled')
        self.assertEqual(row[3], 5)
        self.assertEqual(row[4], 10)
        
        cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                       "FROM fp_change WHERE id=" + str(my_fp.fp_id))
        for row in cursor:
            if row[2] == 'description':
                self.assertEqual(row[0], 10)
                self.assertEqual(row[1], 'Jesus')
                self.assertEqual(row[3], 'move quickly')
                self.assertEqual(row[4], 'super jog')
            elif row[2] == 'comment':
                self.assertEqual(row[0], 10)
                self.assertEqual(row[1], 'Jesus')
                self.assertEqual(row[4], 'I shall save you')
            else:
                self.assertEqual(True,False)

    def test_get_changelog_given_nothing(self):
        my_fp = Fp(self.env)
        my_fp.populate({'name':'go', 'description':'a'})
        my_fp.insert()
        my_fp['description'] = 'b'
        my_fp.save_changes('Guy-Alain','BeCowse!')
        my_log = my_fp.get_changelog()
        for record in my_log:
            time, author, field, oldvalue, newvalue = record

        if field == 'comment':
            self.assertEqual(author, 'Guy-Alain')
            self.assertEqual(newvalue, 'BeCowse!')
        else:
            self.assertEqual(author, 'Guy-Alain')
            self.assertEqual(field, 'description')            
            self.assertEqual(oldvalue, 'a')
            self.assertEqual(newvalue, 'b')

    def test_get_changelog_given_time(self):

        values = {'name': 'foo', 'description': 'footest', 
                  'status':'enabled'}
        my_fp = Fp(self.env)
        my_fp.populate(values)

        my_fp.insert()
        my_fp['description'] = 'yo mamma so foo'
        my_fp.save_changes('me','because',cnum=4,when=65)

        my_fp['description'] = 'bee kowz'
        my_fp.save_changes('me','mattresses',cnum=5,when=69)

        my_log = my_fp.get_changelog(when=65)
        for record in my_log:
            time, author, field, oldvalue, newvalue = record

            if field == 'comment':

                self.assertEqual(author, 'me')
                self.assertEqual(field, 'comment')
                self.assertEqual(oldvalue, '4')
                self.assertEqual(newvalue, 'because')

            else:
                self.assertEqual(author, 'me')
                self.assertEqual(field, 'description')
                self.assertEqual(oldvalue, 'footest')
                self.assertEqual(newvalue, 'yo mamma so foo')
    def test_get_fp_hyp_info(self):
                
        cursor = self.env.db.cursor()
        cursor.execute( "INSERT INTO fp (name,id,description,status) "
                        "VALUES ('frag', '17', 'to pwn', 'enabled')")
        cursor.execute( "INSERT INTO hyponym (name,fp,status) "
                        "VALUES ('hover','10', 'disabled')")
        cursor.execute( "INSERT INTO hyponym (name, fp, status) "
                        "VALUES ('zoom', '10','enabled')")
        cursor.execute( "INSERT INTO hyponym (name, fp, status) "
                        "VALUES ('splode', '17','enabled')")

        self.assertEqual(Fp(self.env).get_fp_hyp_info(),
        [{  'fp':('fly','disabled'), 
            'hyponyms':[('hover','disabled'), ('zoom','enabled')], 
            'description':'levitate'},
         {  'fp':('frag','enabled'), 
            'hyponyms':[('splode','enabled')], 
            'description':'to pwn'},
         {  'fp':('squish','disabled'), 
            'hyponyms':[], 
            'description':'press'}])

    def test_set_on_fly_fp(self):
        cursor = self.env.db.cursor()        
        cursor.execute("INSERT INTO on_the_fly "
                       "VALUES ('fp','enabled')")
                       
        Fp(self.env).set_on_fly_fp('enabled')
        cursor.execute("SELECT status FROM on_the_fly "
                       "WHERE name ='fp'")
        row = cursor.fetchone()
        self.assertNotEqual(None,row)
        self.assertEqual(row[0], 'enabled')

class HyponymTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub()
        self.hyponym = Hyponym(self.env)

        cursor = self.env.db.cursor()
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
        query = "INSERT into hyponym (name,fp,status,id) " + \
                "values ('make', 'spam fp', 'robotic', '42')"
        cursor.execute(query)
        
        query = "INSERT into hyponym (name,fp,status,id) " + \
                "values ('squish', 'eggs fp', 'lithovore', '13')"
        cursor.execute(query)

        cursor.execute("INSERT into fp (id, name, description) "
                       "VALUES(7,'frag', 'to pwn') ")

        cursor.execute("INSERT into hyponym (id, name, fp) "
                       "VALUES(1,'smite', 7)")

    def test_create_hyp_given_nothing(self):
        my_hyponym = Hyponym(self.env)
        self.assertEqual(None, my_hyponym.hyp_id)
        self.assertEqual(None, my_hyponym.time_created)
        self.assertEqual(None, my_hyponym.time_changed)
        self.assertEqual(0, len(my_hyponym.values))

    def test_insert_given_nothing(self):
        my_hyponym = Hyponym(self.env)
        my_hyponym['name'] = 'monkey'
        my_hyponym['fp'] = 'junk'
        my_hyponym['status'] = 'awesome'
        my_hyponym.insert()

        self.assertNotEqual(None, my_hyponym['id'])
        self.assertEqual('monkey', my_hyponym['name'])
        self.assertEqual('junk', my_hyponym['fp'])
        self.assertEqual('enabled', my_hyponym['status'])

        cursor = self.env.db.cursor()
        cursor.execute("SELECT id from hyponym WHERE name = 'monkey' AND" +
                       " fp = 'junk' AND status = 'enabled'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], my_hyponym['id'])        

    def test_insert_given_time(self):
        my_hyponym = Hyponym(self.env)
        my_hyponym['name'] = 'rubble'
        my_hyponym['fp'] = 'jump'
        my_hyponym['status'] = 'dead'
        
        my_hyponym.insert(when=23)

        cursor = self.env.db.cursor()
        cursor.execute("SELECT fp,status,time,changetime" +
                        " from hyponym WHERE name = 'rubble'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], my_hyponym['fp'])
        self.assertEqual(row[1], 'enabled')
        self.assertEqual(row[2], my_hyponym.time_created)
        self.assertEqual(row[3], my_hyponym.time_changed)
 
    def test_create_hyp_given_good_name(self):
        
        my_hyponym = Hyponym(self.env, name='make' )
        self.assertEqual(42, my_hyponym['id'])
        self.assertEqual('make', my_hyponym['name'])
        self.assertEqual('spam fp', my_hyponym['fp'])
        self.assertEqual('robotic', my_hyponym['status'])

    def test_create_hyp_given_good_id(self):
        
        my_hyponym = Hyponym(self.env, id = 42)
        self.assertEqual(42, my_hyponym['id'])
        self.assertEqual('make', my_hyponym['name'])
        self.assertEqual('spam fp', my_hyponym['fp'])
        self.assertEqual('robotic', my_hyponym['status'])
       
    def test_create_hyp_given_good_name_and_id(self):
         
        my_hyponym = Hyponym(self.env, id = 42, name='make')
        self.assertEqual(42, my_hyponym['id'])
        self.assertEqual('make', my_hyponym['name'])
        self.assertEqual('spam fp', my_hyponym['fp'])
        self.assertEqual('robotic', my_hyponym['status'])
                          
    def test_create_hyp_given_bad_name(self):
        mybool = None
        try: 
            my_hyponym = Hyponym(self.env, name = 'nonexistant')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)

    def test_create_hyp_given_bad_id(self):

        mybool = None
        try: 
            my_hyponym = Hyponym(self.env, id = 63)
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)
    
    def test_create_hyp_given_unmatching_id_name(self):

        mybool = None
        try: 
            my_hyponym = Hyponym(self.env, id = 13, name = 'make')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)

    def test_create_hyp_given_missing_id_and_existing_name(self):

        mybool = None
        try: 
            my_hyponym = Hyponym(self.env, id = 812, name = 'make')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)

    def test_create_hyp_given_missing_name_and_existing_id(self):

        mybool = None
        try: 
            my_hyponym = Hyponym(self.env, id = 13, name = 'qwerty')
        except TracError:
            mybool = True

        self.assertEqual(True, mybool)


    def test_populate_with_values(self):
        values = {'name': 'spam', 'fp': 'mellon', 'status': 'enabled'}
        my_hyponym = Hyponym(self.env)

        my_hyponym.populate(values)

        self.assertEqual(my_hyponym.values['name'], 'spam')
        self.assertEqual(my_hyponym.values['fp'], 'mellon')
        self.assertEqual(my_hyponym.values['status'], 'enabled')

    def test_save_changes_given_nothing(self):
        
        values = {'name': 'spam', 'fp': 'mellon', 'status': 'enabled'}
        my_hyponym = Hyponym(self.env)
        my_hyponym.populate(values)
        my_hyponym.insert()

        my_hyponym['fp'] = 'bring me a shubbery'
        my_hyponym['status'] = 'disabled'
        my_hyponym.save_changes('Batman','hotdog')
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT fp,status FROM hyponym WHERE name = 'spam'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 'bring me a shubbery')
        self.assertEqual(row[1], 'disabled')
        
    def test_save_changes_given_time(self):
        
        values = {'name': 'spam', 'fp': 'mellon', 'status': 'enabled'}
        my_hyponym = Hyponym(self.env)
        my_hyponym.populate(values)
        my_hyponym.insert(when=52)

        my_hyponym['fp'] = 'bring me a shubbery'
        my_hyponym['status'] = 'disabled'
        my_hyponym.save_changes('Batman','hotdog',when=25)
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT time,changetime FROM hyponym WHERE name = 'spam'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 52)
        self.assertEqual(row[1], 25)


    def test_save_changes_given_cnum(self):

        values = {'name': 'spam', 'fp': 'mellon', 'status': 'enabled'}
        my_hyponym = Hyponym(self.env)
        my_hyponym.populate(values)
        my_hyponym.insert(when=52)

        my_hyponym['fp'] = 'bring me a shubbery'
        my_hyponym['status'] = 'disabled'
        my_hyponym.save_changes('Batman','hotdog',cnum=40)
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT oldvalue FROM hyponym_change WHERE id =%s" %
                      my_hyponym.values['id'])

        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], '40')

    def test_save_changes_given_cnum_and_time(self):

        values = {'name': 'spam', 'fp': 'mellon', 'status': 'enabled'}
        my_hyponym = Hyponym(self.env)
        my_hyponym.populate(values)
        my_hyponym.insert(when=52)

        my_hyponym['fp'] = 'bring me a shubbery'
        my_hyponym['status'] = 'disabled'
        my_hyponym.save_changes('Batman','hotdog',cnum=40, when=25)
        
        cursor = self.env.db.cursor()
        cursor.execute("SELECT oldvalue FROM hyponym_change WHERE id =%s" %
                      my_hyponym.values['id'])

        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], '40')

        cursor.execute("SELECT time,changetime FROM hyponym WHERE name = 'spam'")
        row = cursor.fetchone()
        self.assertNotEqual(None, row)
        self.assertEqual(row[0], 52)
        self.assertEqual(row[1], 25)

    def test_get_changelog_given_no_args(self):
        
        values = {'name': 'spam', 'fp': 'mellon', 'status': 'enabled'}
        my_hyponym = Hyponym(self.env)
        my_hyponym.populate(values)

        my_hyponym.insert()
        my_hyponym['fp'] = 'bring me a shubbery'
        my_hyponym.save_changes('Batman','hotdog',cnum=4)
        
        my_log = my_hyponym.get_changelog()
        for record in my_log:
            time, author, field, oldvalue, newvalue = record

            if field == 'comment':

                self.assertEqual(author, 'Batman')
                self.assertEqual(field, 'comment')
                self.assertEqual(oldvalue, '4')
                self.assertEqual(newvalue, 'hotdog')

            else:
                self.assertEqual(author, 'Batman')
                self.assertEqual(field, 'fp')
                self.assertEqual(oldvalue, 'mellon')
                self.assertEqual(newvalue, 'bring me a shubbery')
        
    def test_get_changelog_given_time(self):
        
        values = {'name': 'spam', 'fp': 'mellon', 'status': 'enabled'}
        my_hyponym = Hyponym(self.env)
        my_hyponym.populate(values)

        my_hyponym.insert()
        my_hyponym['fp'] = 'bring me a shubbery'
        my_hyponym.save_changes('Batman','hotdog',cnum=4,when=65)

        my_hyponym['fp'] = 'tank'
        my_hyponym.save_changes('Batman','mattresses',cnum=5,when=69)
        
        my_log = my_hyponym.get_changelog(when=65)
        for record in my_log:
            time, author, field, oldvalue, newvalue = record

            if field == 'comment':

                self.assertEqual(author, 'Batman')
                self.assertEqual(field, 'comment')
                self.assertEqual(oldvalue, '4')
                self.assertEqual(newvalue, 'hotdog')

            else:
                self.assertEqual(author, 'Batman')
                self.assertEqual(field, 'fp')
                self.assertEqual(oldvalue, 'mellon')
                self.assertEqual(newvalue, 'bring me a shubbery')

    def test_swap_with_fp(self):
        my_hyp = Hyponym(self.env, id=1)

        self.assertEqual('smite', my_hyp['name'])
        my_hyp.swap_with_fp('me', 'testing')
        self.assertEqual('frag', Hyponym(self.env, id=1)['name'])
        self.assertEqual('smite', Fp(self.env, id=7)['name'])
        

def suite():
    suite = unittest.makeSuite(RequirementTestCase, 'test')
    req_wiki_cache_test_case_suite = unittest.makeSuite(
        RequirementWikiCacheTestCase, 'test')
    req_ticket_cache_test_case_suite = unittest.makeSuite(
        RequirementTicketCacheTestCase, 'test')
    obj_test_case_suite = unittest.makeSuite(ObjectTestCase, 'test')
    fp_test_case_suite = unittest.makeSuite(FpTestCase, 'test')
    hyp_test_case_suite = unittest.makeSuite(HyponymTestCase, 'test')
    suite.addTest(req_wiki_cache_test_case_suite)
    suite.addTest(req_ticket_cache_test_case_suite)
    suite.addTest(obj_test_case_suite)
    suite.addTest(fp_test_case_suite)
    suite.addTest(hyp_test_case_suite)
    return suite

if __name__ == '__main__':
    unittest.main()
