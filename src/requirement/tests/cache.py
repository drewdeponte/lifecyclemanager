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
from trac.ticket.model import Ticket
from trac.wiki.model import WikiPage
from trac.requirement.cache import CacheComponent
from trac.test import EnvironmentStub, Mock
from trac.requirement.model import RequirementTicketCache
from trac.requirement.model import RequirementWikiCache
from trac.requirement.api import RequirementSystem
from trac.requirement.cache import RequirementCacheSystem

import unittest

class CacheComponentTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.cache_component = CacheComponent(self.env)

        cursor = self.env.db.cursor()
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)
        
        # begin with reasonably full tables of data:        
        for component, fp, object, id in [('comp1', 'fp1', 'obj1', 1),
                                          ('comp1', 'fp1', 'obj2', 1),
                                          ('comp1', 'fp1', 'obj3', 1),
                                          ('comp1', 'fp2', 'obj1', 1),
                                          ('comp1', 'fp3', 'obj2', 2),
                                          ('comp2', 'fp1', 'obj3', 2),
                                          ('comp2', 'fp2', 'obj1', 2),
                                          ('comp3', 'fp4', 'obj4', 2),
                                          ('comp3', 'fp3', 'obj2', 2),
                                          ('comp3', 'fp3', 'obj1', 3),
                                          ('comp3', 'fp1', 'obj4', 3)]:
            cursor.execute("INSERT INTO requirement_ticket_cache "
                           "(component,fp,object,ticket) VALUES "
                           "(%s,%s,%s,%s)", (component, fp, object, id))

        for comment, flag, id in [('comment1', 'comment', 1),
                                  ('comment2', 'comment', 1),
                                  ('comment3', 'comment', 3)]:
            cursor.execute("INSERT INTO ticket_change "
                           "(newvalue,field,ticket) VALUES "
                           "(%s,%s,%s)", (comment, flag, id))


        self.env.db.commit()

    def _insert_ticket(self, summary, **kw):
        """Helper for inserting a ticket into the database"""
        ticket = Ticket(self.env)
        for k,v in kw.items():
            ticket[k] = v
        return ticket.insert()

    def _create_a_ticket(self):
        ticket = Ticket(self.env)
        ticket['reporter'] = 'santa'
        ticket['summary'] = '<comp4 foo bar>'
        ticket['description'] = '<comp5 pet cat>'
        ticket['keywords'] = '<comp6 do things>'
        ticket['foo'] = 'This is a custom field'
        return ticket

    def _create_a_wiki_page(self):
        page = WikiPage(self.env)
        page.text = '<comp5 pet cat>'
        page.name = 'TestPage'
        page.version = '1'
        return page

    def _create_a_cache_component(self):
        # short-hand method for making CacheComponents
        cache_component = CacheComponent(self.env)
        return cache_component

    def test_create_ticket(self):
        # insert a ticket into the db.
        ticket = self._create_a_ticket()
        self.assertEqual('santa', ticket['reporter'])
        self.assertEqual('<comp5 pet cat>', ticket['description'])
        self.assertEqual('This is a custom field', ticket['foo'])
        self.assertEqual('<comp4 foo bar>', ticket['summary'])
        self.assertEqual('<comp6 do things>', ticket['keywords'])
        ticket.insert()

    def test_create_a_wiki_page(self):
        # test basic page creation:
        page = self._create_a_wiki_page()
        self.assertEqual('TestPage', page.name)
        self.assertEqual('1', page.version)
        self.assertEqual('<comp5 pet cat>', page.text)        

    def test_wiki_page_added_1(self):
        # test for insertion into the db

        db = self.env.db
        cursor = db.cursor()

        sql = "INSERT INTO component VALUES ('comp5', 'anonymous', 'Described')"
        cursor.execute( sql )
        db.commit()

        # create a page:
        page = self._create_a_wiki_page()

        # first make sure it is not there to begin with:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, page.version))
        self.assertEqual(None, cursor.fetchone())

        # put it in the db:
        cache_component = self._create_a_cache_component()
        cache_component.wiki_page_added(page)

        # make sure it is there:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, page.version))
        self.assertEqual(('comp5', 'pet', 'cat', page.name, page.version), \
                         cursor.fetchone())

    def test_wiki_page_added_2(self):
        # check to make sure it does not insert duplicates
        
        cursor = self.env.db.cursor()

        page = self._create_a_wiki_page()
        cache_component = self._create_a_cache_component()
        cache_component.wiki_page_added(page)

        # first one is fine, the second one is not:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, page.version))
        row = cursor.fetchone()
        self.assertEqual(None, cursor.fetchone())

    def test_wiki_page_deleted(self):
        # test for deletion from the db:
        
        cursor = self.env.db.cursor()
        self._insert_component('comp5')

        # first make sure it is there to begin with.
        # create it and put it in the db:
        page = self._create_a_wiki_page()
        cache_component = self._create_a_cache_component()
        cache_component.wiki_page_added(page)

        cursor.execute("SELECT component,fp,object,wiki_name "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s",
                       ('comp5', 'pet', 'cat', page.name))
        self.assertEqual(('comp5', 'pet', 'cat', page.name), cursor.fetchone())

        # get it and delete it from the db:
        cache_component = self._create_a_cache_component()
        cache_component.wiki_page_deleted(page)

        # make sure no reference to this wiki page remains whatsoever:
        cursor.execute("SELECT component,fp,object,wiki_name "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s",
                       ('comp5', 'pet', 'cat', page.name))
        self.assertEqual(None, cursor.fetchone())

    def test_wiki_page_version_deleted(self):
        # test for deletion of version:
        cursor = self.env.db.cursor()
        self._insert_component('comp5')
        self._insert_component('comp6')

        # first make sure it is there to begin with.
        # create it and put it in the db:
        page = self._create_a_wiki_page()
        cache_component = self._create_a_cache_component()
        cache_component.wiki_page_added(page)

        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, page.version))
        self.assertEqual(('comp5', 'pet', 'cat', page.name, page.version), \
                         cursor.fetchone())

        # make a new one:
        new_page = self._create_a_wiki_page()

        # alter the page and register the change:
        new_page.text = '<comp6 cuddle cat>'
        new_page.version = '2'
        cache_component.wiki_page_added(new_page)

        # get the old one and delete it from the db:
        cache_component = self._create_a_cache_component()
        cache_component.wiki_page_version_deleted(page)

        # make sure it is gone:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, page.version))
        self.assertEqual(None, cursor.fetchone())

        # ...but make sure the newer version still remains:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp6', 'cuddle', 'cat', new_page.name, new_page.version))
        self.assertEqual(('comp6', 'cuddle', 'cat', new_page.name, new_page.version), \
                         cursor.fetchone())

    def test_wiki_page_changed(self):
        # test for changes to the db:
        cursor = self.env.db.cursor()
        self._insert_component('comp5')
        self._insert_component('comp6')

        # create a page and stick it in the db:
        page = self._create_a_wiki_page()
        cache_component = self._create_a_cache_component()
        cache_component.wiki_page_added(page)

        # make sure it is there:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, page.version))
        self.assertEqual(('comp5', 'pet', 'cat', 'TestPage', '1'), \
                         cursor.fetchone())

        # make sure the alterd version is not there:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp6', 'cuddle', 'cat', page.name, page.version))
        self.assertEqual(None, cursor.fetchone())

        # alter the page and register the change:
        page.text = '<comp6 cuddle cat>'
        page.version = '2'
        cache_component.wiki_page_changed(page, page.version, 42, \
                                          'worthless info', 'santa', '::1')

        # make sure the new stuff is there:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp6', 'cuddle', 'cat', page.name, page.version))
        self.assertEqual(('comp6', 'cuddle', 'cat', page.name, page.version), \
                         cursor.fetchone())

        # and the old stuff is not...:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, page.version))
        self.assertEqual(None, cursor.fetchone())

        # ...unless you are looking at the older version:
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version "
                       "FROM requirement_wiki_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and wiki_name=%s and wiki_version=%s",
                       ('comp5', 'pet', 'cat', page.name, '1'))
        self.assertEqual(('comp5', 'pet', 'cat', 'TestPage', '1'), \
                         cursor.fetchone())

    def test_ticket_created_2(self):
    # test for insertion into the db:

        cursor = self.env.db.cursor()
        self._insert_component('comp5')
        
        # first make sure it isnt there to begin with:
        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp5', 'pet', 'cat', 2))
        self.assertEqual(None, cursor.fetchone())

        # create it and put it in the db:
        ticket = self._create_a_ticket()
        ticket.insert()
        cache_component = self._create_a_cache_component()
        cache_component.ticket_created(ticket)

        # make sure its there:
        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp5', 'pet', 'cat', ticket.id))
        self.assertEqual(('comp5', 'pet', 'cat', ticket.id), cursor.fetchone())

    def test_ticket_created_3(self):
        # check to make sure it does not insert duplicates
        cursor = self.env.db.cursor()

        ticket = self._create_a_ticket()
        ticket.insert()
        cache_component = self._create_a_cache_component()
        cache_component.ticket_created(ticket)
        cache_component.ticket_created(ticket)

        # first one is fine, the second one is not:
        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp5', 'pet', 'cat', ticket.id))
        row = cursor.fetchone()
        self.assertEqual(None, cursor.fetchone())

    def test_ticket_deleted(self):
        # test for insertion into the db:
        
        cursor = self.env.db.cursor()
        self._insert_component('comp5')

        # first make sure it is there to begin with:
        # create it and put it in the db:
        ticket = self._create_a_ticket()
        ticket.insert()
        cache_component = self._create_a_cache_component()
        cache_component.ticket_created(ticket)

        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp5', 'pet', 'cat', ticket.id))
        self.assertEqual(('comp5', 'pet', 'cat', ticket.id), cursor.fetchone())

        # get it and delete it from the db:
        cache_component = self._create_a_cache_component()
        cache_component.ticket_deleted(ticket)

        # make sure it is gone:
        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp5', 'pet', 'cat', ticket.id))
        self.assertEqual(None, cursor.fetchone())

    def test_ticket_changed(self):

        cursor = self.env.db.cursor()
        self._insert_component('comp5')
        self._insert_component('comp6')
        self._insert_component('comp7')

        ticket = self._create_a_ticket()
        ticket.insert()
        cache_component = self._create_a_cache_component()
        cache_component.ticket_created(ticket)

        # insert a comment:
        ticket.save_changes('santa', '<comp7 get cat>') 

        ticket['summary'] = 'Nothing of consequence'
        cache_component.ticket_changed(ticket, 'garbage', 'santa', 'garbage')

        # make sure the correct entries remain:
        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp5', 'pet', 'cat', ticket.id))
        self.assertEqual(('comp5', 'pet', 'cat', ticket.id), cursor.fetchone())

        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp6', 'do', 'things', ticket.id))
        self.assertEqual(('comp6', 'do', 'things', ticket.id), cursor.fetchone())

        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp7', 'get', 'cat', ticket.id))
        self.assertEqual(('comp7', 'get', 'cat', ticket.id), cursor.fetchone())

        # ...but make sure this one is now gone:
        cursor.execute("SELECT component,fp,object,ticket "
                       "FROM requirement_ticket_cache "
                       "WHERE component=%s and fp=%s and object=%s"
                       " and ticket=%s",
                       ('comp4', 'foo', 'bar', ticket.id))
        self.assertEqual(None, cursor.fetchone())

        #sql = "DELETE FROM component"
        #cursor.execute( sql )
        #db.commit()


    def test_get_comments(self):
        
        # test to see if correct values are pulled out of the db
        #  (see entries in setup routine, above)
        cache_component = self._create_a_cache_component()
        comments = cache_component._get_comments(1)

        self.assertTrue('comment1' in comments)
        self.assertTrue('comment2' in comments)

        comments = cache_component._get_comments(2)
        self.assertEqual(None, comments)

        comments = cache_component._get_comments(3)
        self.assertTrue('comment3' in comments)


    def _insert_component(self, component):
        
        db = self.env.db
        cursor = db.cursor()

        sql = "INSERT INTO component VALUES ('%s', 'anonymous', 'Described')" % component
        cursor.execute( sql )
        db.commit()



class RequirementCacheSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.requirement_system = RequirementSystem(self.env)
        
        cursor = self.env.db.cursor()

        self._insert_component('comp1')
        self._insert_component('comp2')
        self._insert_component('comp_num_3')
        self._insert_component('comp_num_4')

        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)

        self.env.db.commit()
    
    def test_parse_data_for_req_references(self):
        my_str = """<comp1 open door>
requirement:comp2-close-door
<comp_num_3 start_vehicle red_truck>
requirement:comp_num_4-stop_vehicle-blue_car"""
        refs = RequirementCacheSystem(self.env).parse_data_for_req_references(my_str)
        self.assertNotEqual(None, refs)
        self.assertTrue(('comp1','open','door') in refs)
        self.assertTrue(('comp2','close','door') in refs)
        self.assertTrue(('comp_num_3','start_vehicle','red_truck') in refs)
        self.assertTrue(('comp_num_4','stop_vehicle','blue_car') in refs)
        
    def test_index_tickets(self):
        self._insert_component('comp4')
        self._insert_component('comp5')
        self._insert_component('comp6')
        ticket1 = Ticket(self.env)
        ticket1['reporter'] = 'santa'
        ticket1['summary'] = 'the num 1 summary'
        ticket1['description'] = '<comp5 pet cat>'
        ticket1['keywords'] = '<comp6 do things>'
        ticket1.insert()
        ticket2 = Ticket(self.env)
        ticket2['reporter'] = 'bob'
        ticket2['summary'] = 'the number 2 summary'
        ticket2['description'] = 'The desc requirement:comp4-feed-cat foo'
        ticket2['keywords'] = 'foo bar kitty'
        ticket2.insert()
        req_cache_sys = RequirementCacheSystem(self.env)
        req_cache_sys.index_tickets()
        req_ticket_cache = RequirementTicketCache(self.env, ticket1.id, 'comp5', 'pet', 'cat')
        self.assertEqual(req_ticket_cache.exists, True)
        req_ticket_cache = RequirementTicketCache(self.env, ticket1.id, 'comp6', 'do', 'things')
        self.assertEqual(req_ticket_cache.exists, True)
        req_ticket_cache = RequirementTicketCache(self.env, ticket2.id, 'comp4', 'feed', 'cat')
        self.assertEqual(req_ticket_cache.exists, True)
        
    def test_index_wikis(self):
        self._insert_component('comp16')
        self._insert_component('comp20')
        wiki1 = WikiPage(self.env, name="Testwiki1", version="1")
        wiki1.text = "This is the wiki <comp20 open door> text content."
        wiki1.save('adeponte', 'My comment', '192.168.1.2')
        wiki2 = WikiPage(self.env, name="Testwiki2", version="1")
        wiki2.text = "This is the wiki <comp16 close door> text content."
        wiki2.save('bob', 'His Comment', '182.123.321.456')
        req_cache_sys = RequirementCacheSystem(self.env)
        req_cache_sys.index_wikis()
        req_wiki_cache = RequirementWikiCache(self.env, 'comp20', 'open', 'door', 'Testwiki1', '1')
        self.assertEqual(req_wiki_cache.exists, True)
        req_wiki_cache = RequirementWikiCache(self.env, 'comp16', 'close', 'door', 'Testwiki2', '1')
        self.assertEqual(req_wiki_cache.exists, True)
        
    def test_need_index_wikis(self):
        need_index = RequirementCacheSystem(self.env)._need_index_wikis()
        self.assertEqual(need_index, True)
        req_wiki_cache = RequirementWikiCache(self.env, 'comp8', 'kill', 'monster', 'foopage', '2')
        req_wiki_cache.insert()
        need_index = RequirementCacheSystem(self.env)._need_index_wikis()
        self.assertEqual(need_index, False)
    
    def test_need_index_tickets(self):
        need_index = RequirementCacheSystem(self.env)._need_index_tickets()
        self.assertEqual(need_index, True)
        req_ticket_cache = RequirementTicketCache(self.env, '11','comp8', 'myfp', 'myobj')
        req_ticket_cache.insert()
        need_index = RequirementCacheSystem(self.env)._need_index_tickets(db=self.env.db)
        self.assertEqual(need_index, False)

    def _insert_component(self, component):    
        db = self.env.db
        cursor = db.cursor()
        sql = "INSERT INTO component VALUES ('%s', 'anonymous', 'Described')" % component
        cursor.execute( sql )
        db.commit()


def suite():
    suite = unittest.makeSuite(CacheComponentTestCase, 'test')
    req_cache_sys_suite = unittest.makeSuite(RequirementCacheSystemTestCase, 'test')
    suite.addTest(req_cache_sys_suite)
    return suite

if __name__ == '__main__':
    unittest.main()

