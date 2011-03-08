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

import re
from cStringIO import StringIO

from trac import util
from trac.core import *
from trac.db import get_column_names
from trac.perm import IPermissionRequestor
from trac.util import sorted
from trac.util.datefmt import format_date, format_time, format_datetime, \
                              http_date
from trac.util.html import html, Markup
from trac.util.text import unicode_urlencode, to_unicode
from trac.web import IRequestHandler
from trac.web.chrome import add_link, add_stylesheet, add_script, ITemplateProvider
from trac.wiki import wiki_to_html, Formatter
from trac.Timeline import ITimelineEventProvider
from metric import RequirementMetric
from model import Requirement
from model import Fp
from model import Object

import time

class ViewModule(Component):
    implements(IRequestHandler)
    
    doc_type = None # Default doc type
    event_providers = ExtensionPoint(ITimelineEventProvider)

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/requirements/view/(\w+)', req.path_info)
        if match:
            if match.group(1):
                req.args['view'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.assert_permission('REQUIREMENT_VIEW')
        
        if req.perm.has_permission('REQUIREMENT_CREATE'):
            req.hdf['report.add_requirement_href'] = req.href.newrequirement()
        
        db = self.env.get_db_cnx()
        
        req.hdf['graph_path'] = req.href.requirement() + '/graph/'
        req.hdf['link_requirement_href'] = req.href.requirement()
        template = ''
        doc_type = self.doc_type

        if req.args['view'] is not None:
            add_link(req, 'up', req.href.requirements())

        if req.args['view'] == '1':
            mls = MostLeastCited( req, db, self.env )
            mls.get_info()
            template = mls.get_template()
        elif req.args['view'][0] == '2':
            tt = MostLeastTED( req, db, self.env )
            tt.get_info( req.args['view'] )
            template = tt.get_template()
        elif req.args['view'] == '3':
            mlc = MostLeastChanged( req, db, self.env )
            mlc.get_info()
            template = mlc.get_template()
        elif req.args['view'] == '4':
            msc = MilestoneChanges( req, db, self.env )
            msc.get_info()
            template = msc.get_template()
        elif req.args['view'] == '5':
            met = EntropyMetric( req, db, self.env )
            met.get_info(req.args.get('timestamp'))
            template = met.get_template()
            add_stylesheet(req, 'hw/css/entropy_metric.css')
        elif req.args['view'] == '6':
            met = PmiMetric( req, db, self.env )
            met.get_info(req.args.get('timestamp'))
            template = met.get_template()
            add_stylesheet(req, 'hw/css/pmi_metric.css')
        elif req.args['view'] == '7':
            timeline = TimeLineView( req, db, self.env )
            timeline.get_info()
            template = timeline.get_template()
            add_stylesheet(req, 'hw/css/req_timeline.css')
            add_script(req, 'hw/timeline/timeline-api.js')
        elif req.args['view'] == '7_data':
            timeline = TimeLineDataView( req, db, self.env )
            timeline.get_info(self.event_providers)
            template = timeline.get_template()
            doc_type = 'text/xml'

        elif req.args['view'] == '8':
            met = PerUserView( req, db, self.env )
            twiki = 1
            trequirement = 1
            tticket = 1
            user = "anonymous"
            
            if req.args.has_key('wiki'):
                twiki = 1
            if req.args.has_key('requirement'):
                trequirement = 1
            if req.args.has_key('ticket'):
                tticket = 1
            if req.args.has_key('username'):
                try:
                    user = (req.args.get('username'))
                except:
                    pass
            
            met.get_info (user, trequirement, twiki, tticket)
            template = met.get_template()
            
            add_stylesheet(req, 'common/css/timeline.css')
            add_stylesheet(req, 'htdocs/css/req_report.css')
            
        return template, doc_type

class RequirementView:
   
    """RequiementView is a more abstract class which will 
    contain all needed general utilities for handeling
    the gathering data and representating views.
    """

    def __init__(self, req, db, env):
        self.req = req
        self.db = db
        self.env = env
    
    #def _render_view(self, req, db):
    #    req.perm.assert_permission('REQUIREMENT_VIEW')
    #    return 'req_report.cs', None

    def get_info(self, view, args):
        cursor = self.db.cursor()
        cursor.execute("SELECT title,query,description from requirement_report "
                       "WHERE report=%s", ('view/' + view,))
        row = cursor.fetchone()
        if not row:
            raise TracError('View %s does not exist.' % view,
                            'Invalid View Number')
        title = row[0] or ''
        sql = row[1]
        description = row[2] or ''

    def requirement_tr( self, requirement ):
        m = re.search( r'<(\w+) (\w+) (\w+)>', requirement )
        return m.group(1) + '-' + m.group(2) + '-' + m.group(3)

    def get_template( self ):
        return self.template

    def no_results( self ):
        self.req.hdf['noresults'] = 1

class TimeLineView(RequirementView):

    template = 'timeline_activity.cs'

    def get_info(self):
        self.req.hdf['timeline_data_url'] = self.req.href.requirement() + 's/view/7_data'
        
        name, offset = self.get_local_tzoffset()
        self.req.hdf['current_time'] = time.strftime("%a %b %d %Y %H:%M:%S %Z")
        self.req.hdf['timezone'] = offset
        
    def get_local_tzoffset(self):
        """ Returns the timezone offset
            Python has no good built-in support for getting the timezone offset. This attempts to get around that.
        """
        name, dstname = time.tzname
        if time.daylight:
            if time.altzone != 0:
              return dstname, int(time.altzone / 3600)
            return dstname, 0
        else:
            if time.timezone != 0:
              return name, int(time.timezone / 3600)
            return name, 0
    
    def get_gmtstring(self):
        name, offset = self.get_local_tzoffset()
        if offset > 0:
            return 'GMT+' + str(offset) + '00'
        elif offset < 0:
            return 'GMT' + str(offset) + '00'
        return 'GMT'
        
class TimeLineDataView(TimeLineView):
    """
    We subclass TimeLineView so we can have the same helper methods
    """
    template = 'timeline_activity_data.cs'

    def get_info(self, event_providers):
        # TODO: There are supposed benefits to switching from a XML to JSON event source
        # http://simile.mit.edu/wiki/JSON_event_source:_use_js_Date%28%29_objects
    
        self.req.hdf['event_url'] = self.req.href.requirement() # TODO: This needs to be changed to a local source
        self.req.hdf['event_section'] = 'timeline' # TODO: This needs to be changed to a local source
        events = []
        
        start = 0
        stop = time.time()
        filters = ['milestone', 'ticket', 'changeset', 'wiki', 'requirement']
        for event_provider in event_providers:
            #try:
                for kind, href, title, date, author, message in event_provider.get_timeline_events(self.req, start, stop, filters):
                    # TODO: revisit this code... string escaping is still an issue
                    # Strip/escape HTML markup
                    #if isinstance(title, Markup):
                    #    title = title.plaintext(keeplinebreaks=False)
                    if not isinstance(title, Markup):
                        title = Markup(title)
                    title = title.plaintext(keeplinebreaks=False)
                    #title = title.stripentities()
                    message = to_unicode(message)
                    
                    events.append({
                      # Everything but data will be inserted as attributes into an event tag
                      # Data is provided to allow customization of the bubble content
                      # For more information about the XML format, see
                      # http://simile.mit.edu/wiki/How_to_Create_Event_Source_Files
                      'isDuration': 'false',
                      'start': time.strftime("%a %b %d %Y %H:%M:%S "+self.get_gmtstring(), time.gmtime(date)),
                      'title': title,
                      'data': {'kind': kind,
                               'title': title,
                               'href': href,
                               'author': author or 'anonymous',
                               'date': format_date(date),
                               'time': format_time(date, '%H:%M'),
                               'dateuid': int(date),
                               'message': message},
                      'debug': isinstance(title, Markup),
                    })
            #except Exception, e: # cope with a failure of that provider
            #    pass

        self.req.hdf['events'] = events

class PerUserView(RequirementView):
    """ Class produces list of dictionaries which are
    used to create per user activity report """

    template = 'user_activity.cs'

    def get_info(self, author, requirement, wiki, ticket):
        data = []
        id = 0
        self.req.hdf['username'] = author
        empty = 1
        
        if requirement:
            self.req.hdf['trequirement'] = 1
            data = self.get_user_data(author, 'requirement')
            if data:
                empty = 0
                for x in data:
                    event = {'kind': 'Requirement', 'title': x[2], 'href': "requirement/"+ x[2],
                        'author': x[1] or 'anonymous',
                        'date': x[0],
                        'time': x[0],
                        'message': x[4]}
                    self.req.hdf['requirements.view.8.events.%s' % id] = event
                    id += 1
            
        if wiki:
            self.req.hdf ['twiki'] = 1        
            data = self.get_user_data(author, 'wiki')
            if data:
                empty = 0
                for x in data:
                    event = {'kind': 'Wiki', 'title': x[2], 'href': "wiki/"+ x[2],
                        'author': x[1] or 'anonymous',
                        'date': x[0],
                        'time': x[0],
                        'message': x[4]}
                    self.req.hdf['requirements.view.8.events.%s' % id] = event
                    id += 1

        if ticket:
            self.req.hdf['tticket'] = 1        
            data = self.get_user_data(author, 'ticket')
            if data:
                empty = 0
                for x in data:
                    event = {'kind': 'Ticket', 'title': x[3], 'href': self.req.href.ticket(str(x[3])),
                        'author': x[1] or 'anonymous',
                        'date': x[0],
                        'time': x[0],
                        'message': x[4]}
                    self.req.hdf['requirements.view.8.events.%s' % id] = event
                    id += 1

        # hdf events need to be sorted via 'time' which is the 1st part of each tuple
        if empty:
          self.no_results()
          
    def get_user_data(self, user, afilter):
        cursor = self.db.cursor()
        events =[]

        if afilter == 'ticket':
	    cursor.execute("SELECT t.id, t.type, t.time, t.changetime, t.component, t.owner "
	                   "FROM ticket_change tc "
			   "INNER JOIN ticket t "
			   "ON tc.ticket = t.id "
			   "WHERE t.owner='%s' "
                           "GROUP BY t.id "
                           "UNION "
                           "SELECT t.id, t.type, t.time, t.changetime, t.component, t.owner "
                           "FROM ticket t "
                           "WHERE t.owner='%s' "
			   "ORDER BY t.time" % (user,user))
        elif afilter =='requirement':
	    cursor.execute("SELECT r.time, r.creator, r.component, r.fp, r.object "
	                   "FROM requirement_change rc "
			   "INNER JOIN requirement r "
			   "ON r.component = rc.component AND r.fp = rc.fp AND r.object = rc.object "
			   "WHERE r.creator='%s' "
                           "GROUP BY r.component, r.fp, r.object "
			   "UNION "
			   "SELECT r.time, r.creator, r.component, r.fp, r.object "
			   "FROM requirement r "
			   "WHERE r.creator='%s' "
			   "ORDER BY r.time" % (user,user))
        elif afilter =='wiki':
            cursor.execute("SELECT time, author, name, version, comment " +
                           "FROM wiki WHERE author=%s ORDER by time",
                           (user,))

        matches = cursor.fetchall()
        for r in matches:
            events.append ( (r[0], r[1], r[2], r[3], r[4]) )

        return events

class MostLeastCited(RequirementView):

    template = 'most_least_cited.cs'
    
    def get_info( self ):
        query = """
            SELECT '<' || comp || ' ' || f || ' ' || obj || '>', count(*) AS tsum
            FROM
            (
                SELECT DISTINCT rc.component AS comp, rc.fp AS f, rc.object AS obj, rc.wiki_name
                FROM requirement_wiki_cache rc LEFT JOIN (SELECT fp.name
                    as rfp, r.component as rcomp, o.name as robj from fp, requirement
                    r, object o WHERE fp.id = r.fp AND o.id = r.object)
                WHERE (
                           rc.component = rcomp AND
                           rc.fp = rfp AND
                           rc.object = robj
                      )
                UNION ALL
                SELECT rc.component AS comp, rc.fp AS f, rc.object AS obj, rc.ticket
                FROM requirement_ticket_cache rc LEFT JOIN (SELECT
                    fp.name as rfp, req.component as rcomp, o.name as robj FROM fp,
                    requirement req, object o WHERE fp.id = req.fp AND o.id = req.object) 
                WHERE (
                           rc.component = rcomp AND
                           rfp = rc.fp AND
                           rc.object = robj
                      )
            ) GROUP BY comp, f, obj ORDER BY tsum DESC;
        """

        cursor = self.db.cursor()
        cursor.execute( query )
       
        requirements = cursor.fetchall()
        if not requirements:
            self.no_results()
        else:
            out_requirements = []
            for r in requirements:
                out_requirements.append( ( r[0], r[1], self.requirement_tr( r[0] ) ) )
             
            self.req.hdf['requirements'] = out_requirements

class MostLeastTED(RequirementView):
    """Stands for: 
        Most/Least Tasks, Enhancements, Defects

       This class produces a view of which requiements are associated to 
       the most to least tasks, enhancements and defects.  A reaquierment
       can possibly ber associated to none or all of the differemt types 
       of tickets.
    """

    template = 'most_least_ted.cs'
    
    def get_info( self, url ):
        ( basic_url, ticket_type ) = url.rsplit( '_' )
       
        self.req.hdf['view_ted'] = self.req.href.requirements( 'view' ) + '/2_'
        self.req.hdf['ticket_type'] = ticket_type

        # Turns 'Enhancements' into 'enhancement'
        ticket_type = ticket_type[:-1].lower()

        query = """
        SELECT '<' || c || ' ' || f || ' ' || o || '>' as Requirement, count(*) as cnt
        FROM
        (
            SELECT rtc.component as c, rtc.fp as f, rtc.object as o
            FROM requirement_ticket_cache rtc
                LEFT JOIN ticket t LEFT JOIN requirement r, fp F, object obj 
            WHERE (
                      t.type = '%s' AND
                      rtc.ticket=t.id AND
                      rtc.component = r.component AND
                      rtc.fp = F.name AND
                      F.id = r.fp AND
                      rtc.object = obj.name AND
                      obj.id = r.object
                  )
        )
        GROUP BY Requirement ORDER BY cnt DESC;
        """ % ticket_type
        cursor = self.db.cursor()
        cursor.execute( query )
       
        requirements = cursor.fetchall()

        if not requirements:
            self.no_results()
        else:
            out_requirements = []
            for r in requirements:
                out_requirements.append( ( r[0], r[1], self.requirement_tr( r[0] ) ) )
             
            self.req.hdf['requirements'] = out_requirements
    
class MostLeastChanged(RequirementView):

    template = 'most_least_changes.cs'
    
    def get_info( self ):
        query = """
            SELECT '<' || component || ' ' || fp.name || ' ' || object.name || '>', count(*) AS csum
            FROM requirement_change rc, fp, object
            WHERE (oldvalue != '' OR newvalue != '') 
            AND rc.fp = fp.id
            AND rc.object = object.id
            GROUP BY component, fp.name, object.name ORDER BY csum DESC;
        """

        cursor = self.db.cursor()
        cursor.execute( query )
       
        requirements = cursor.fetchall()
        if not requirements:
            self.no_results()
        else:
            out_requirements = []
            for r in requirements:
                out_requirements.append( ( r[0], r[1], self.requirement_tr( r[0] ) ) )
             
            self.req.hdf['requirements'] = out_requirements
            
class MilestoneChanges(RequirementView):

    template = 'milestone_changes.cs'
    
    def get_info( self ):
        query = """SELECT name, due FROM milestone ORDER BY due ASC;"""

        cursor = self.db.cursor()
        cursor.execute( query )

        out_milestones = []
       
        milestones = cursor.fetchall()
        if not milestones:
            self.no_results()
        else:
            prev_milestone_timestamp = 0
            for ms in milestones:
                query = """
                    SELECT '<' || rc.component || ' ' || fp.name || ' ' || o.name || '>', count(*) AS csum
                    FROM requirement_change rc, fp, object o
                    WHERE rc.time > %d AND rc.time < %d 
                    AND (oldvalue != '' OR newvalue != '')
                    AND rc.fp = fp.id
                    AND o.id = rc.object
                    GROUP BY rc.component, fp.name, o.name ORDER BY csum DESC;
                """ % (prev_milestone_timestamp, ms[1])
                #query = """SELECT '<' || component || ' ' || fp || ' ' || object || '>', count(*) AS csum FROM requirement WHERE changetime < %d;""" % ms[1]
                cursor.execute(query)
                requirements = cursor.fetchall()
                out_requirements = []
                milestone_changes_count = 0
                if requirements:
                    for r in requirements:
                        milestone_changes_count = milestone_changes_count + r[1]
                        
                    for r in requirements:
                        out_requirements.append( ( r[0], r[1], self.requirement_tr( r[0] ), int((float(r[1])/float(milestone_changes_count)) * 100) ) )
                out_milestones.append( ((ms[0], ms[1], milestone_changes_count), out_requirements) )
                prev_milestone_timestamp = ms[1]
    
            self.req.hdf['milestones'] = out_milestones

class EntropyMetric(RequirementView):

    template = 'entropy_metric.cs'

    def get_info( self, timestamp=None ):
        model = Requirement(self.env)
        met = RequirementMetric(model)

        results = met.entropy(timestamp)
        if results is None:
            self.no_results()
        else:
            total_entropy = results[0]
            avg_entropy = results[1]
            components_entropies = results[2]
            req_entropies = results[3]
            fp_entropies = results[4]
            object_entropies = results[5]

            # Ease division below
            if total_entropy == 0:
                total_entropy = 1;

            reqs = []
            for req, entropy in req_entropies.iteritems():
                my_fp = Fp(self.env, id=req[1])['name']
                my_obj = Object(self.env, id=req[2])['name']
                reqs.append({'name': '<'+req[0]+' '+my_fp+' '+my_obj+'>',
                             'link': self.req.href.requirement(req[0]+
                                     '-'+my_fp+'-'+my_obj),
                             'entropy': '%.3f' % entropy})

            components = []
            for comp, entropy in components_entropies.iteritems():
                components.append({'name': comp,
                                   'percent': '%.1f' % (100 * entropy / total_entropy)})
            self.req.hdf['graph_path'] = self.req.href.requirements()+'/graph/'

            self.req.hdf['reqs'] = sorted(reqs, lambda x,y: cmp(float(y['entropy']), float(x['entropy'])))
            self.req.hdf['components'] = sorted(components, lambda x,y: cmp(x['name'], y['name']))

class PmiMetric(RequirementView):

    template = 'pmi_metric.cs'

    def get_info(self, timestamp=None):
        model = Requirement(self.env)
        met = RequirementMetric(model)

        predicate = None

        results = met.pmi(predicate, timestamp)

        if len(results) == 0:
            self.no_results()

        pmis = []
        for pairing in results.keys():
            cur_fp = Fp(self.env, id=pairing[0])['name']
            cur_obj = Object(self.env, id=pairing[1])['name']
            pmis.append((cur_fp, cur_obj, '%.3f' % results[pairing]))

        self.req.hdf['pmis'] = pmis
