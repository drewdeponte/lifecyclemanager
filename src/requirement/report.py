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

# Adapted from Trac's /ticket/report.py

import re
from cStringIO import StringIO

from trac import util
from trac.core import *
from trac.db import get_column_names
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.util import sorted
from trac.util.datefmt import format_date, format_time, format_datetime, \
                               http_date
from trac.util.html import html
from trac.util.text import unicode_urlencode
from trac.web import IRequestHandler
from trac.web.chrome import add_link, add_stylesheet, INavigationContributor, ITemplateProvider
from trac.wiki import wiki_to_html, Formatter
from model import Requirement

class ReportModule(Component):

    implements(INavigationContributor,
               IRequestHandler)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'requirements'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('REQUIREMENT_VIEW'):
            return
        yield ('mainnav', 'requirements',
               html.A('Requirements', href=req.href.requirements()))

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/requirements/report/?(\d+)?', req.path_info)
        if match:
            if match.group(1):
                req.args['report'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.assert_permission('REQUIREMENT_VIEW')
        
        if req.perm.has_permission('REQUIREMENT_CREATE'):
            req.hdf['report.add_requirement_href'] = req.href.newrequirement()

        req.hdf['report.edit_fphyp_href'] = req.href('editdict', 'fp')

        db = self.env.get_db_cnx()

        report = req.args.get('report', '')

        # only for use in reports showing (nearly) all requirements
        if (report == '1' or report == '2' or report == '3'):
            # flag the report to use the validation button
            req.hdf['report.is_all_reqs_report'] = 1

            myreq = Requirement(self.env)
            req.hdf['report.currently_validated'] = \
                myreq.get_current_reqs_validated()
            validation_time = myreq.get_most_recent_validation()
            if validation_time is not None:
                req.hdf['report.latest_validation'] = \
                    format_datetime(validation_time)
            else:
                req.hdf['report.latest_validation'] = '(None)'

            # get the value from the validation button if it exists:
            if req.method == 'POST':
                validate = req.args.get('ValidateSubmit', '')
                if validate == 'Validate':
                    # set this flag...
                    # ... and validate the current set of requirements:
                    if myreq.validate_requirements():
                        req.hdf['report.validate'] = 2
                        req.hdf['report.latest_validation'] = format_datetime()
                    else:
                        req.hdf['report.validate'] = 1
                        
                    
        if report is not '':
            add_link(req, 'up', req.href('requirements', 'report'))

        resp = self._render_view(req, db, report)
        if not resp:
           return None
        template, content_type = resp
        if content_type:
           return resp

        add_stylesheet(req, 'hw/css/req_report.css')
        return 'req_report.cs', None

    # Internal methods

    def _render_view(self, req, db, report):
        req.perm.assert_permission('REQUIREMENT_VIEW')

        try:
            args = self.get_var_args(req)
        except ValueError,e:
            raise TracError, 'Report failed: %s' % e

        title, description, sql = self.get_info(db, report, args)

        format = req.args.get('format')
        if format == 'sql':
            self._render_sql(req, report, title, description, sql)
            return

        req.hdf['report.mode'] = 'list'
        if report != '':
            title = '{%s} %s' % (report, title)
        req.hdf['title'] = title
        req.hdf['report.title'] = title
        req.hdf['report.report'] = report
        req.hdf['report.description'] = wiki_to_html(description, self.env, req)
        self.add_alternate_links(req, args)

        try:
            cols, rows = self.execute_report(req, db, report, sql, args)
        except Exception, e:
            req.hdf['report.message'] = 'Report execution failed: %s' % e
            return 'req_report.cs', None

        # Convert the header info to HDF-format
        idx = 0
        for col in cols:
            title=col.capitalize()
            prefix = 'report.headers.%d' % idx
            req.hdf['%s.real' % prefix] = col
            if title.startswith('__') and title.endswith('__'):
                continue
            elif title[0] == '_' and title[-1] == '_':
                title = title[1:-1].capitalize()
                req.hdf[prefix + '.fullrow'] = 1
            elif title[0] == '_':
                continue
            elif title[-1] == '_':
                title = title[:-1]
                req.hdf[prefix + '.breakrow'] = 1
            req.hdf[prefix] = title
            idx = idx + 1

        if req.args.has_key('sort'):
            sortCol = req.args.get('sort')
            colIndex = None
            hiddenCols = 0
            for x in range(len(cols)):
                colName = cols[x]
                if colName == sortCol:
                    colIndex = x
                if colName.startswith('__') and colName.endswith('__'):
                    hiddenCols += 1
            if colIndex != None:
                k = 'report.headers.%d.asc' % (colIndex - hiddenCols)
                asc = req.args.get('asc', None)
                if asc:
                    asc = int(asc) # string '0' or '1' to int/boolean
                else:
                    asc = 1
                req.hdf[k] = asc
                def sortkey(row):
                    val = row[colIndex]
                    if isinstance(val, basestring):
                        val = val.lower()
                    return val
                rows = sorted(rows, key=sortkey, reverse=(not asc))

        # Get the email addresses of all known users
        email_map = {}
        for username, name, email in self.env.get_known_users():
            if email:
                email_map[username] = email

        # Convert the rows and cells to HDF-format
        row_idx = 0
        for row in rows:
            col_idx = 0
            numrows = len(row)
            for cell in row:
                cell = unicode(cell)
                column = cols[col_idx]
                value = {}
                group_value = None
                # Special columns begin and end with '__'
                if column.startswith('__') and column.endswith('__'):
                    value['hidden'] = 1
                elif (column[0] == '_' and column[-1] == '_'):
                    value['fullrow'] = 1
                    column = column[1:-1]
                    req.hdf[prefix + '.breakrow'] = 1
                elif column[-1] == '_':
                    value['breakrow'] = 1
                    value['breakafter'] = 1
                    column = column[:-1]
                elif column[0] == '_':
                    value['hidehtml'] = 1
                    column = column[1:]
                if column == '__group__' and report == '5':
                    group_value = req.href.requirement(
                        re.sub( r'<(\w+ ?\w+) (\w+) (\w+)>',
                                '\g<1>-\g<2>-\g<3>', row[0] ))
                if column == 'Requirement':
                    # parse out the angle-brakets and place it in the proper
                    #  filename format:
                    value['requirement_href'] = req.href.requirement( 
                        re.sub( r'<(\w+ ?\w+) (\w+) (\w+)>', 
                                '\g<1>-\g<2>-\g<3>', row[1] ))
                # for any of the following possibilities...
                elif column == 'Wiki':
                    value['wiki_href'] = req.href.wiki(row[1])
                elif column in ('ticket', 'id', '_id', '#', 'summary'):
                    # grab the ticket number from the associated column...
                    id_cols = [idx for idx, col in enumerate(cols)
                               if col in ('ticket', 'id', '_id')]
                    # ...and use it in the url:
                    if id_cols:
                        # (don't forget to parse out the pound sign)
                        id_val = re.sub(r'#(\d+)', '\g<1>', row[id_cols[0]])
                        value['ticket_href'] = req.href.ticket(id_val)
                elif column == 'Description':
                    desc = wiki_to_html(cell, self.env, req, db,
                                        absurls=(format == 'rss'))
                    value['parsed'] = format == 'rss' and unicode(desc) or desc
                elif column == 'Creator':
                    if cell.find('@') != -1:
                        value['rss'] = cell
                    elif cell in email_map:
                        value['rss'] = email_map[cell]
                # for any of the following possibilities...
                elif column in ('report', 'title'):
                    # grab the report number from the associated column...
                    id_cols = [idx for idx, col in enumerate(cols)
                               if col == 'report']
                    # ...and use it in the url:
                    if id_cols:
                        id_val = unicode(row[id_cols[0]])
                        value['report_href'] = req.href.requirements(id_val)

                elif column in ('time', 'date','changetime', 'created', 'modified'):
                    if cell == 'None':
                        value['date'] = value['time'] = cell
                        value['datetime'] = value['gmt'] = cell
                    else:
                        value['date'] = format_date(cell)
                        value['time'] = format_time(cell)
                        value['datetime'] = format_datetime(cell)
                        value['gmt'] = http_date(cell)
                prefix = 'report.items.%d.%s' % (row_idx, unicode(column))
                group_prefix = 'report.items.%d' % (row_idx)
                req.hdf[prefix] = unicode(cell)
                if group_value:
                    req.hdf[group_prefix + '.' + '__link__'] = unicode(group_value)
                    req.hdf[group_prefix + '.' + '__link__.hidden'] = 1
                else:
                    for key in value.keys():
                        req.hdf[prefix + '.' + key] = value[key]

                col_idx += 1
            row_idx += 1
        req.hdf['report.numrows'] = row_idx

        if format == 'rss':
            return 'report_rss.cs', 'application/rss+xml'
        elif format == 'csv':
            filename = id and 'report_%s.csv' % id or 'report.csv'
            self._render_csv(req, cols, rows, mimetype='text/csv',
                             filename=filename)
            return None
        elif format == 'tab':
            filename = id and 'report_%s.tsv' % id or 'report.tsv'
            self._render_csv(req, cols, rows, '\t',
                             mimetype='text/tab-separated-values',
                             filename=filename)
            return None
        elif format == 'latex':
            filename = id and 'report_%s.tex' % id or 'report.tex'
            self._render_latex(req, cols, rows, mimetype='application-x/latex',
                               filename=filename)
            return None

        return 'req_report.cs', None

    def add_alternate_links(self, req, args):
        params = args
        if req.args.has_key('sort'):
            params['sort'] = req.args['sort']
        if req.args.has_key('asc'):
            params['asc'] = req.args['asc']
        href = ''
        if params:
            href = '&' + unicode_urlencode(params)
        add_link(req, 'alternate', '?format=rss' + href, 'RSS Feed',
                 'application/rss+xml', 'rss')
        add_link(req, 'alternate', '?format=csv' + href,
                 'Comma-delimited Text', 'text/plain')
        add_link(req, 'alternate', '?format=tab' + href,
                 'Tab-delimited Text', 'text/plain')
        add_link(req, 'alternate', '?format=latex' + href,
                 'LaTeX', 'application-x/latex')
        if req.perm.has_permission('REPORT_SQL_VIEW'):
            add_link(req, 'alternate', '?format=sql', 'SQL Query',
                     'text/plain')

    def execute_report(self, req, db, report, sql, args):
        sql, args = self.sql_sub_vars(req, sql, args, db)
        if not sql:
            raise TracError('Report %s has no SQL query.' % report)
        if sql.find('__group__') == -1:
            req.hdf['report.sorting.enabled'] = 1

        self.log.debug('Executing report with SQL "%s" (%s)', sql, args)

        cursor = db.cursor()
        cursor.execute(sql, args)

        # FIXME: fetchall should probably not be used.
        info = cursor.fetchall() or []
        cols = get_column_names(cursor)

        db.rollback()

        return cols, info

    def get_info(self, db, report, args):
        if report == '':
            # If no particular report was requested, display
            # a list of available reports instead
            title = 'Available Reports'
            sql = 'SELECT report, title FROM requirement_report ORDER BY key'
            description = 'This is a list of reports available.'
        else:
            cursor = db.cursor()
            cursor.execute("SELECT title,query,description from requirement_report "
                           "WHERE report=%s", ('report/' + report,))
            row = cursor.fetchone()
            if not row:
                raise TracError('Report %s does not exist.' % report,
                                'Invalid Report Number')
            title = row[0] or ''
            sql = row[1]
            description = row[2] or ''

        return [title, description, sql]

    def get_var_args(self, req):
        report_args = {}
        for arg in req.args.keys():
            if not arg.isupper():
                continue
            report_args[arg] = req.args.get(arg)

        # Set some default dynamic variables
        if not report_args.has_key('USER'):
            report_args['USER'] = req.authname

        return report_args

    def sql_sub_vars(self, req, sql, args, db=None):
        if db is None:
            db = self.env.get_db_cnx()
        values = []
        def add_value(aname):
            try:
                arg = args[aname]
            except KeyError:
                raise TracError("Dynamic variable '$%s' not defined." \
                                % aname)
            req.hdf['report.var.' + aname] = arg
            values.append(arg)

        var_re = re.compile("[$]([A-Z]+)")

        # simple parameter substitution outside literal
        def repl(match):
            add_value(match.group(1))
            return '%s'

        # inside a literal break it and concatenate with the parameter
        def repl_literal(expr):
            parts = var_re.split(expr[1:-1])
            if len(parts) == 1:
                return expr
            params = parts[1::2]
            parts = ["'%s'" % p for p in parts]
            parts[1::2] = ['%s'] * len(params)
            for param in params:
                add_value(param)
            return db.concat(*parts)

        sql_io = StringIO()

        # break SQL into literals and non-literals to handle replacing
        # variables within them with query parameters
        for expr in re.split("('(?:[^']|(?:''))*')", sql):
            if expr.startswith("'"):
                sql_io.write(repl_literal(expr))
            else:
                sql_io.write(var_re.sub(repl, expr))
        return sql_io.getvalue(), values

    def _render_csv(self, req, cols, rows, sep=',', mimetype='text/plain',
                    filename=None):
        req.send_response(200)
        req.send_header('Content-Type', mimetype + ';charset=utf-8')
        if filename:
            req.send_header('Content-Disposition', 'filename=' + filename)
        req.end_headers()

        req.write(sep.join(cols) + '\r\n')
        for row in rows:
            req.write(sep.join(
                [unicode(c).replace(sep,"_")
                 .replace('\n',' ').replace('\r',' ') for c in row]) + '\r\n')

    def _render_latex(self, req, cols, rows, mimetype='application-x/latex',
                      filename=None):
        req.send_response(200)
        req.send_header('Content-Type', mimetype + ';charset=utf-8')
        if filename:
            req.send_header('Content-Disposition', 'filename=' + filename)
        req.end_headers()

        for row in rows:
            match = re.match(r'<(\w+) (\w+) (\w+)>', row[1])
            if match:
                if match.group(1) and match.group(2) and match.group(3):
                    component = match.group(1)
                    fp = match.group(2)
                    object = match.group(3)

                    description = row[2]

                    component = re.sub('_', '\\_', component)
                    fp = re.sub('_', '\\_', fp)
                    object = re.sub('_', '\\_', object)

                    req.write('\\item \\nreq{'+component+'}{'+fp+'}{'+object+'}{'+description+'}{}')

