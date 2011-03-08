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
from trac.ticket.api import ITicketChangeListener
from trac.wiki.api import IWikiChangeListener
#from trac.wiki.model import WikiPage
from api import RequirementSystem
from model import RequirementWikiCache
from model import RequirementTicketCache
import re

class RequirementCacheSystem(object):
    """Class representing the requirement cache system.
    
    The purpose of this class it to encapsulate and group a number of
    functions used to handle requirement relationship caching. Beyond
    that, it attempts to provide a trivial, unified, well organized
    interface to these function.
    """
    
    def __init__(self, env):
        """Construct an instance of the RequirementCacheSystem class.
        
        Construct an instance of the RequirementCacheSystem class with
        the appropriate default values.
        """
        
        self.env = env
        
    def parse_data_for_req_references(self, data):
        """Parse the given data for references to requirements.
        
        This function goes through the passed data and identifies any
        references to requirements. The references are returned as a
        list of tuples in which the tuples contain three entries;
        component, functional primitive, and object in that order. In
        the case that no matches are found a value of None is returned.
        """
        
        req_ref_list = []

        rexps = [RequirementSystem(self.env).get_wiki_syntax().next()[0],
                r'requirement:(?P<component>\w+)-(?P<fp>\w+)-(?P<object>\w+)']

        for rexp in rexps:
            compre = re.compile(rexp)
            matchiter = compre.finditer(data)
            if matchiter:
                for match in matchiter:
                    req_ref_list.append((match.group('component'),
                                         match.group('fp'),
                                         match.group('object')))

        if (len(req_ref_list) == 0):
            return None
        else:
            return req_ref_list
                   
    def index_wikis(self, db=None):
        """Index all requirement references found in wikis.
        
        Iterate through all the wiki pages, their invidual, and their
        associated comments in the database parsing them for references
        to requirements. If new references are found then they are
        added appropriately to the database cache tables.
        """
        
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        if (self._need_index_wikis()):
            # Select all the wikis from the wiki table and parse them
            # all for any references to requirements. If any
            # requirement references exist, create a
            # RequirementWikiCache object for it and insert it into
            # the database if it does not already exist in the databse.
            cursor.execute("SELECT name, version, text, comment FROM wiki")
            for name, version, text, comment in cursor:
                # parse the wiki text and create references
                if text:
                    refs = self.parse_data_for_req_references(text)
                
                    if refs:
                        for (component, fp, object) in refs:
                            req_wiki_cache = RequirementWikiCache(self.env, component, fp, object, name, version)
                            if not (req_wiki_cache.exists):
                                req_wiki_cache.insert(db=db)
                
                # parse the comment and create references
                if comment:
                    refs = self.parse_data_for_req_references(comment)
                
                    if refs:
                        for (component, fp, object) in refs:
                            req_wiki_cache = RequirementWikiCache(self.env, component, fp, object, name, version)
                            if not (req_wiki_cache.exists):
                                req_wiki_cache.insert(db=db)
                                        
    def index_tickets(self, db=None):
        """Index all requirement references found in tickets.
        
        Iterate through all the ticket descriptions, their recorded
        changes, and their associated comments in the database parsing
        them for references to requirements. If new references are
        found then they are added appropriately to the database cache
        tables.
        """
        
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("SELECT id, description FROM ticket")
        for id, description in cursor:
            # parse the description
            refs = self.parse_data_for_req_references(description)
            
            if refs:
                for (component, fp, object) in refs:
                    req_ticket_cache = RequirementTicketCache(self.env, id, component, fp, object)
                    if not (req_ticket_cache.exists):
                        req_ticket_cache.insert(db=db)
            
        cursor.execute("SELECT ticket, newvalue FROM ticket_change WHERE field = 'description' or field = 'comment'")
        for id, textdata in cursor:
            # parse the description modification or comment
            refs = self.parse_data_for_req_references(textdata)
            
            if refs:
                for (component, fp, object) in refs:
                    req_ticket_cache = RequirementTicketCache(self.env, id, component, fp, object)
                    if not (req_ticket_cache.exists):
                        req_ticket_cache.insert(db=db)
        
    def _need_index_wikis(self, db=None):
        """Check if wikis need to be indexed.
        
        Check the cache database tables to see if any relationships
        have previously been defined between wikis and requirements.
        If they have not, then it returns a value of True, otherwise
        it returns False.
        """
        
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        # Select all items from requirement_wiki_cache table and if 
        # there are no entries then I need to try and index the
        # requirement to wiki relationships.
        cursor.execute("SELECT component,fp,object,wiki_name,wiki_version FROM requirement_wiki_cache")
        row = cursor.fetchone()
        if row:
            return False
        else:
            return True

    def _need_index_tickets(self, db=None):
        """Check if tickets need to be indexed.
        
        Check the cache database tables to see if any relationships
        have previously been defined between tickets and requirements.
        If they have not, then it returns a value of True, otherwise
        it returns False.
        """
        
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        # Select all items from requirement_ticket_cache table and
        # if there are no entries then I need to try and index the
        # requirement to ticket relationships
        cursor.execute("SELECT component,fp,object,ticket FROM requirement_ticket_cache")
        row = cursor.fetchone()
        if row:
            return False
        else:
            return True

class CacheComponent(Component):
    implements(ITicketChangeListener,IWikiChangeListener)

    # ITicketChangeListener methods

    def ticket_created(self, ticket):
        """Called when a ticket is created.

        This basically takes the ticket data and parses it for references
        to requirements and then creates a relationship map between
        requirements and this ticket. Note: There should be no need
        to check for duplicates or deletions because this is when a ticket
        is just being created.
        """

        searchfields = ['summary', 'description', 'keywords']

        for field in searchfields:
            refs = RequirementCacheSystem( \
                       self.env).parse_data_for_req_references(ticket[field])

            if refs:
                for (component, fp, object) in refs:
                    req_ticket_cache = RequirementTicketCache(self.env, 
                                                              ticket.id,
                                                              component, 
                                                              fp, 
                                                              object)
                    if not (req_ticket_cache.exists):
                        req_ticket_cache.insert()

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        The method takes the ticket, deletes the old relationships 
        mapping requirements to the ticket and creates new ones.
        """
       
        # delete all old information related to this ticket:
        req_ticket_cache = RequirementTicketCache(self.env, ticket.id)
        if (req_ticket_cache.ticket_in_table):
            req_ticket_cache.delete()

        # insert current information:
        searchfields = ['summary', 'description', 'keywords']
        
        for field in searchfields:
            refs = RequirementCacheSystem( \
                       self.env).parse_data_for_req_references(ticket[field])

            if refs:
                for (component, fp, object) in refs:
                    req_ticket_cache = RequirementTicketCache(self.env,
                                                              ticket.id,
                                                              component,
                                                              fp,
                                                              object)
                    if not (req_ticket_cache.exists):
                        req_ticket_cache.insert()

        # insert information gleaned from the comment history:
        comments = self._get_comments(ticket.id)

        if comments:
            for comment in comments:
                refs = RequirementCacheSystem( \
                           self.env).parse_data_for_req_references(comment)

                if refs:
                    for (component, fp, object) in refs:
                        req_ticket_cache = RequirementTicketCache(self.env,
                                                                  ticket.id,
                                                                  component,
                                                                  fp,
                                                                  object)
                        if not (req_ticket_cache.exists):
                            req_ticket_cache.insert()

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted.

        This basically takes the ticket that was deleted and
        removes all relationships from the database mapping requirements
        to the the ticket.
        """

        req_ticket_cache = RequirementTicketCache(self.env, ticket.id)
        if (req_ticket_cache.ticket_in_table):
            req_ticket_cache.delete()

    # IWikiChangeListener methods    
    
    def wiki_page_added(self, page):
        """Called whenever a new Wiki page is added.
        
        This basically takes the page data and parses it for references
        to requirements and then creates a relationship map between
        requirements and this wiki page. Note: There should be no need
        to check for duplicates or deletions because this is when a wiki
        page is just being created.
        """
        
        refs = RequirementCacheSystem(self.env).parse_data_for_req_references(page.text)

        if refs:
            for (component, fp, object) in refs:
                req_wiki_cache = RequirementWikiCache(self.env, component, fp, object, page.name, page.version)
                if not (req_wiki_cache.exists):
                    req_wiki_cache.insert()
        
    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        """Called whenever a page has been modified.
        
        This basically takes the page and finds the changes, and if the
        changes effect requirement references to this wiki page then
        the relationships in the database are updated properly to
        reflect the changes.
        """
        
        refs = RequirementCacheSystem(self.env).parse_data_for_req_references(page.text)

        if refs:
            for (component, fp, object) in refs:
                req_wiki_cache = RequirementWikiCache(self.env, component, fp, object, page.name, version)
                if not (req_wiki_cache.exists):
                    req_wiki_cache.insert()
        
    def wiki_page_deleted(self, page):
        """Called when a page has been deleted.
        
        This basically takes the page that was deleted and removes all
        relationships from the database mapping requirements to this
        wiki page because the wiki page no longer exists.
        """
        
        refs = RequirementCacheSystem(self.env).parse_data_for_req_references(page.text)

        if refs:
            for (component, fp, object) in refs:
                req_wiki_cache = RequirementWikiCache(self.env, component, fp, object, page.name, page.version)
                if (req_wiki_cache.exists):
                    req_wiki_cache.delete_by_page()
        
    def wiki_page_version_deleted(self, page):
        """Called when a version of a page has been deleted.
        
        This basically takes the page version that was deleted and
        removes all relationships from the database mapping requirements
        to this version of the wiki page because the version of the wiki
        page no longer exists.
        """
        
        refs = RequirementCacheSystem(self.env).parse_data_for_req_references(page.text)

        if refs:
            for (component, fp, object) in refs:
                req_wiki_cache = RequirementWikiCache(self.env, component, fp, object, page.name, page.version)
                if (req_wiki_cache.exists):
                    req_wiki_cache.delete()
 
    def _get_comments(self, id, db=None):
        """Get a collection of comments to search for the given ticket id.

        This function finds all comments associated with the given
        ticket and returns them as a list.  In the case that
        no matches are found a value of None is returned.
        """
        
        comment_list = []

        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()

        cursor.execute("SELECT newvalue "
                       "FROM ticket_change "
                       "WHERE field='comment' and ticket=%s", (id,))
       
        row = cursor.fetchone()
        while (row):
            for comment in row:
                comment_list.append(comment)
            row = cursor.fetchone()
            
        if (len(comment_list) == 0):
            return None
        else:
            return comment_list

