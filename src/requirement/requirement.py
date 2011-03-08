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
from trac.core import *
from trac.config import BoolOption
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
    add_stylesheet
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.Timeline import ITimelineEventProvider
from trac.perm import IPermissionRequestor
from trac.mimeview.api import Mimeview, IContentConverter
from trac.util import escape, Markup
from trac.db import DatabaseManager
from cache import RequirementCacheSystem
from model import Requirement
from db_default import db_version, schema, get_data

class RequirementComponent(Component):
    implements(IEnvironmentSetupParticipant,
               ITimelineEventProvider,
               IContentConverter,
               ITemplateProvider)
    
    timeline_details = BoolOption('timeline', 'requirement_show_details', 'false',
        """Enable the display of all requirement changes in the timeline.""")
    
    def get_lifecyclemanager_version(self, db=None):
        """Return the current version of the lifecyclemanager database."""
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system "
                       "WHERE name='lifecyclemanager_version'")
        row = cursor.fetchone()
        if row is not None:
            return int(row[0])
        else:
            # This indicates the lifecyclemanager_version record
            # in the system table doesn't exist.
            #
            # There are two possibilities:
            # 1. The plugin is just being installed.
            # 2. The plugin is already installed and initial
            #    tables exist.
            #
            # The reason for these two possibilities is early versions
            # of the plugin didn't use the correct upgrade mechanism :)
            #
            # Thus, to see which case we have, check for the existence
            # of the 'requirement' table:
            dbver = 1
            try:
                cursor.execute("SELECT * FROM requirement LIMIT 1")
            except:
                dbver = 0
        
            # If necessary, build initial tables & data
            if dbver == 0:
                db_connector, _ = DatabaseManager(self.env)._get_connector()
                for table in schema:
                    for stmt in db_connector.to_sql(table):
                        cursor.execute(stmt)
                db.commit()
                for table, cols, vals in get_data(db):
                    cursor.executemany("INSERT INTO %s (%s) VALUES (%s)" \
                                       % (table, ','.join(cols),
                                          ','.join(['%s' for c in cols])), vals)
                db.commit()
                dbver = 1
            else:
                cursor.execute("INSERT INTO system "
                               "VALUES('lifecyclemanager_version', 1)")
                
            return dbver

    # IEnvironmentSetupParticipant methods
    
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        """Check if database needs upgrade"""
        dbver = self.get_lifecyclemanager_version(db)
        if dbver == db_version:
            return False
        elif dbver > db_version:
            raise TracError, 'Database newer than Lifecycle Manager version'
        return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        dbver = self.get_lifecyclemanager_version()
        for i in range(dbver + 1, db_version + 1):
            name  = 'db%i' % i
            try:
                upgrades = __import__('upgrades', globals(), locals(), [name])
                script = getattr(upgrades, name)
            except AttributeError:
                err = 'No upgrade module for lifecyclemanager version %i (%s.py)' \
                        % (i, name)
                raise TracError, err
            script.do_upgrade(self.env, i, cursor)
        cursor.execute("UPDATE system SET value=%s WHERE "
                       "name='lifecyclemanager_version'", (db_version,))
        req_cache_sys = RequirementCacheSystem(self.env)
        req_cache_sys.index_wikis(db=db)
        req_cache_sys.index_tickets(db=db)
        self.log.info('Upgraded lifecyclemanager version from %d to %d',
                      dbver, db_version)

    # ITemplateProvider methods
    
    def get_templates_dirs(self):
        """Return a list of directories containing the provided
        ClearSilver templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as
        style sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing
        the resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]
    
    # IContentConverter methods
    
    def get_supported_conversions(self):
        yield ('csv', 'Comma-delimited Text', 'csv',
               'trac.requirement.Requirement', 'text/csv', 8)
        yield ('tab', 'Tab-delimited Text', 'tsv',
               'trac.requirement.Requirement', 'text/tab-separated-values', 8)
        yield ('rss', 'RSS Feed', 'xml',
               'trac.requirement.Requirement', 'application/rss+xml', 8)
        
    def convert_content(self, req, mimetype, requirement, key):
        if key == 'csv':
            return self.export_csv(requirement, mimetype='text/csv')
        elif key == 'tab':
            return self.export_csv(requirement, sep='\t',
                                   mimetype='text/tab-separated-values')
        elif key == 'rss':
            return self.export_rss(req, requirement)
        
    def get_timeline_filters(self, req):
        if req.perm.has_permission('REQUIREMENT_VIEW'):
            yield ('requirement', 'Requirement changes')
            if self.timeline_details:
                yield ('requirement_details', 'Requirement details', False)

    def get_timeline_events(self, req, start, stop, filters):
        format = req.args.get('format')

        status_map = {'new': ('newrequirement', 'created'),
                      'edit': ('editedrequirement', 'updated'),
                      'enable': ('enabledrequirement', 'enabled'),
                      'disable': ('disabledrequirement', 'disabled')}

        href = format == 'rss' and req.abs_href or req.href

        def produce((component, fp, object, t, author, description), status, fields,
                    comment, cid):
            if status == 'edit':
                if 'requirement_details' in filters:
                    info = ''
                    if len(fields) > 0:
                        info = ', '.join(['<i>%s</i>' % f for f in \
                                          fields.keys()]) + ' changed<br />'
                else:
                    return None

            elif 'requirement' in filters:
                if status == 'enable':
                    if not comment:
                        info = 'Requirement is now enabled.'
                    else:
                        info = ''
                elif status == 'disable':
                    if not comment:
                        info = 'Requirement is now disabled.'
                    else:
                        info = ''
                else:
                    info = ''
            else:
                return None

            kind, verb = status_map[status]

            if format == 'rss':
                title = '<%s %s %s> %s by %s' % \
                        (component, fp, object, verb, author)
            else:
                title = Markup('<em>&lt;%s %s %s&gt;</em> %s by %s',
                               component, fp, object, verb, author)

            requirement_href = href.requirement('%s-%s-%s' % (component, fp, object))
            if cid:
                requirement_href += '#comment:' + cid

            if status == 'new':
                message = wiki_to_oneliner(description, self.env, db, shorten=True)
            else:
                message = Markup(info)
                if comment:
                    if format == 'rss':
                        message += wiki_to_html(comment, self.env, req, db, absurls=True)
                    else:
                        message += wiki_to_oneliner(comment, self.env, db, shorten=True)

            return kind, requirement_href, title, t, author, message

        # Requirement changes
        if 'requirement' in filters or 'requirement_details' in filters:
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            cursor.execute("SELECT r.component,r.fp,r.object,rc.time,rc.author,r.description, "
                           "       rc.field,rc.oldvalue,rc.newvalue "
                           "  FROM requirement_change rc "
                           "    INNER JOIN requirement r "
                           "      ON r.component = rc.component AND r.fp = rc.fp AND r.object = rc.object "
                           "      AND rc.time>=%s AND rc.time<=%s "
                           "ORDER BY rc.time"
                           % (start, stop))
            previous_update = None
            for component,fp,object,t,author,description,field,oldvalue,newvalue in cursor:
                if not previous_update or (component,fp,object,t,author) != previous_update[:5]:
                    if previous_update:
                        ev = produce(previous_update, status, fields,
                                     comment, cid)
                        if ev:
                            yield ev
                    
                    if field == 'status':
                        if newvalue == 'enabled':
                            status = 'enable'
                        else:
                            status = 'disable'
                    else:
                        status = 'edit'
                    
                    fields, comment, cid = {}, '', None
                    previous_update = (component, fp, object, t, author, description)
                if field == 'comment':
                    comment = newvalue
                    cid = oldvalue and oldvalue.split('.')[-1]
                else:
                    fields[field] = newvalue
            if previous_update:
                if fields.has_key('status'):
                    if fields['status'] == 'enabled':
                        ev = produce(previous_update, 'enable', fields, comment, cid)
                    else:
                        ev = produce(previous_update, 'disable', fields, comment, cid)
                else:
                    ev = produce(previous_update, 'edit', fields, comment, cid)

                if ev:
                    yield ev
            
            # New requirements
            if 'requirement' in filters:
                cursor.execute("SELECT component,fp,object,time,creator,description"
                               "  FROM requirement WHERE time>=%s AND time<=%s",
                               (start, stop))
                for row in cursor:
                    yield produce(row, 'new', {}, None, None)

    # Internal methods

    def export_csv(self, requirement, sep=',', mimetype='text/plain'):
        content = StringIO()
        content.write(sep.join(['component', 'fp', 'object'] +
                               [f['name'] for f in requirement.fields])
                      + CRLF)
        content.write(sep.join([unicode(requirement.component),
                              unicode(Fp(self.env,name=requirement.fp)['name']),
                              unicode(Object(self.env, 
                                            name=requirement.object)['name'])] +
                               [requirement.values.get(f['name'], '')
                                .replace(sep, '_').replace('\\', '\\\\')
                                .replace('\n', '\\n').replace('\r', '\\r')
                                for f in requirement.fields]) +
                      CRLF)
        return (content.getvalue(), '%s;charset=utf-8' % mimetype)
    
    def export_rss(self, req, requirement):
        db = self.env.get_db_cnx()
        model = Requirement(self)
        changes = []
        change_summary = {}

        description = wiki_to_html(requirement['description'], self.env, req, db)
        req.hdf['requirement.description.formatted'] = unicode(description)

        for change in model.grouped_changelog_entries(requirement, db):
            changes.append(change)
            # compute a change summary
            change_summary = {}
            # wikify comment
            if 'comment' in change:
                comment = change['comment']
                change['comment'] = unicode(wiki_to_html(
                        comment, self.env, req, db, absurls=True))
                change_summary['added'] = ['comment']
            for field, values in change['fields'].iteritems():
                if field == 'description':
                    change_summary.setdefault('changed', []).append(field)
                else:
                    chg = 'changed'
                    if not values['old']:
                        chg = 'set'
                    elif not values['new']:
                        chg = 'deleted'
                    change_summary.setdefault(chg, []).append(field)
            change['title'] = '; '.join(['%s %s' % (', '.join(v), k) for k, v \
                                             in change_summary.iteritems()])
        req.hdf['requirement.changes'] = changes
        return (req.hdf.render('requirement_rss.cs'), 'application/rss+xml')
    
    def _do_save(self, req, db, requirement):
        pass
    
    def _insert_requirement_data(self, req, db, requirement, reporter_id):
        pass
    

    
