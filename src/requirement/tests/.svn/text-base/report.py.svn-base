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
from trac.db.mysql_backend import MySQLConnection
from trac.requirement.report import ReportModule
from trac.requirement.model import Requirement
from trac.test import EnvironmentStub, Mock
from trac.perm import PermissionCache
from trac.web.href import Href

import unittest
import sys
import re

class MockMySQLConnection(MySQLConnection):
    def __init__(self):
        pass

class StoreStream:
    text = ''
    def write(self, text):
        self.text += text

class ReportTestCase(unittest.TestCase):

    def my_write(self, text):
        print text

    def setUp(self):
        self.env = EnvironmentStub()
        self.report_module = ReportModule(self.env)
        self.requirement = Requirement(self.env)
        self.req = Mock(hdf=dict(), args=dict())

        self.req.send_response = lambda x: None
        self.req.send_header = lambda x, y: None
        self.req.end_headers = lambda: None
        self.req.write = self.my_write
        self.req.href = Href('/trac')
        self.req.base_path = 'http://lm'
        self.req.authname = 'joe'
        self.env.get_known_users = lambda: [('joe','Joe','joe@joe.com')];

        cursor = self.env.db.cursor()
        cursor.execute("INSERT INTO permission VALUES ('joe', 'TRAC_ADMIN')")
        
        from trac.db.sqlite_backend import _to_sql
        from trac.requirement.db_default import schema
        for table in schema:
            for stmt in _to_sql(table):
                cursor.execute(stmt)

        for component in ['comp1', 'comp2', 'comp3','comp_comp']:
            cursor.execute("INSERT INTO component (name) VALUES(%s)", (component,))
            
        for fp in ['fp1','fp2','fp3','fp4','fp_fp']:
            cursor.execute("INSERT INTO fp (name) VALUES(%s)", (fp,))
            
        for object in ['obj1','obj2','obj3','obj4','obj_obj']:
            cursor.execute("INSERT INTO object (name) VALUES(%s)", (object,))
        
        # A healthy list of requirements
        for component, fp, object in [('comp1', 'fp1', 'obj1'),
                                      ('comp1', 'fp1', 'obj2'),
                                      ('comp1', 'fp1', 'obj3'),
                                      ('comp1', 'fp2', 'obj1'),
                                      ('comp1', 'fp3', 'obj2'),
                                      ('comp2', 'fp1', 'obj3'),
                                      ('comp2', 'fp2', 'obj1'),
                                      ('comp3', 'fp4', 'obj4'),
                                      ('comp3', 'fp3', 'obj2'),
                                      ('comp3', 'fp3', 'obj1'),
                                      ('comp3', 'fp1', 'obj4'),
                                      ('comp_comp', 'fp_fp', 'obj_obj')]:
            cursor.execute("INSERT INTO requirement (component,fp,object,status,description) "
                           "VALUES (%s,%s,%s,'enabled','A description')",
                           (component, fp, object))

        sql = """
        INSERT INTO requirement_report 
        VALUES('report/1','Requirements by Component',
            "SELECT component AS __group__,
                 '<' || component || ' ' || fp || ' ' ||
                     object || '>' as 'Requirement',
                 description AS 'Description',
                 creator AS 'Creator'
             FROM requirement
             WHERE status = 'enabled' 
             ORDER BY component, fp, object",
            'Show all requirements, grouped by component',1)
        """
        cursor.execute(sql)
        
        sql = """
        INSERT INTO requirement_report
        VALUES('report/2','Requirements by Object',
            "SELECT object AS __group__,
                 '<' || component || ' ' || fp || ' ' || 
                     object || '>' AS 'Requirement',
                 description AS 'Description',
                 creator AS 'Creator'
             FROM requirement 
             WHERE status = 'enabled'
             ORDER BY object, component, fp",
            'Show all requirements, grouped by object',2)
        """
        cursor.execute(sql)
        
        sql = """
        INSERT INTO requirement_report
        VALUES('report/3','Requirements by Functional Primitive',
            "SELECT fp AS __group__,
                 '<' || component || ' ' || fp || ' ' || 
                     object || '>' AS 'Requirement',
                 description AS 'Description',
                 creator AS 'Creator'
             FROM requirement 
             WHERE status = 'enabled' 
             ORDER BY fp, component, object",
            'Show all requirements, grouped by functional primitive',3)
        """
        cursor.execute(sql)
       
        sql = """
        INSERT INTO requirement_report
        VALUES('report/4','Requirements with Associated Tickets',
            "SELECT ('<' || r.component || ' ' || r.fp || ' ' || 
                      r.object || '>') AS __group__,
                 '#' || rtc.ticket AS 'ticket',
                 t.summary AS 'summary'
             FROM requirement r LEFT JOIN requirement_ticket_cache rtc 
                 LEFT JOIN ticket t
             WHERE (r.status = 'enabled')
                 AND (
                         r.component = rtc.component AND
                         r.fp = rtc.fp AND
                         r.object = rtc.object
                     )
                 AND (
                         t.id = rtc.ticket
                     )
             ORDER BY r.component, r.fp, r.object, rtc.ticket",
            'Show all requirements with associated tickets',4)
        """
        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report 
        VALUES('report/5','Requirements Changed during Milestone (changetime < due)',
            "SELECT m.name AS __group__,
                '<' || r.component || ' ' || r.fp || ' ' ||
                    r.object || '>' as 'Requirement',
                r.description AS 'Description',
                r.creator AS 'Creator'
             FROM requirement r LEFT JOIN milestone m
             WHERE (r.status = 'enabled' ) 
                AND (r.changetime < m.due)
             ORDER BY m.name, r.component, r.fp, r.object",
            'Show all requirements, grouped by milestone, where requirement.changetime < milestone.due',5)
        """
        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report 
        VALUES('report/6','Requirements by Milestone (via ticket)',
            "SELECT m.name AS __group__,
                '<' || r.component || ' ' || r.fp || ' ' ||
                    r.object || '>' as 'Requirement',
                r.description AS 'Description',
                r.creator AS 'Creator'
             FROM milestone m
                INNER JOIN
                    (SELECT r.component AS component,
                            r.fp AS fp,
                            r.object AS object,
                            r.description AS description,
                            r.creator AS creator,
                            t.milestone AS milestone
                         FROM requirement r LEFT JOIN requirement_ticket_cache rtc 
                             LEFT JOIN ticket t
                         WHERE (r.status = 'enabled') 
                             AND (
                                 r.component = rtc.component AND
                                 r.fp = rtc.fp AND
                                 r.object = rtc.object
                             ) 
                             AND (t.id = rtc.ticket) 
                         GROUP BY t.milestone, r.component, r.fp, r.object
                         ORDER BY r.component, r.fp, r.object
                    ) r
                    ON r.milestone = m.name
                    ORDER BY r.milestone",
            'Show all requirements, grouped by milestone (via ticket)',6)
        """
        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report 
        VALUES('report/7','Disabled Requirements by Component',
            "SELECT component AS __group__,
                '<' || component || ' ' || fp || ' ' ||
                    object || '>' as 'Requirement',
                description AS 'Description',
                creator AS 'Creator'
             FROM requirement
             WHERE status = 'disabled'
             ORDER BY component, fp, object",
            'Show all disabled requirements, grouped by component',7)
        """

        cursor.execute(sql)


        sql = """
        INSERT INTO requirement_report 
        VALUES('report/8','Requirements with Wikis (a.k.a. Wikis by Requirement)',
            "SELECT '<' || r.component || ' ' || r.fp || ' ' || 
                r.object || '>' AS __group__,
                w.name as 'Wiki',
                w.comment as 'Comment',
                w.version as 'Version',
                w.author AS 'Creator'
             FROM requirement r LEFT JOIN requirement_wiki_cache rwc
                 LEFT JOIN wiki w
             WHERE (r.status = 'enabled')
                 AND (
                         r.component = rwc.component AND
                         r.fp = rwc.fp AND
                         r.object = rwc.object
                     ) 
                 AND (
                         w.name = rwc.wiki_name AND
                         w.version = rwc.wiki_version
                     )
             ORDER BY r.component, r.fp, r.object",
            'Show all requirements with wikis',8)
        """
        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report 
        VALUES('report/9','Requirements by Wiki',
            "SELECT w.name AS __group__,
                 '<' || r.component || ' ' || r.fp || ' ' || 
                     r.object || '>' as Requirement,
                 r.description as 'Description',
                 r.creator as 'Creator'
             FROM requirement r LEFT JOIN requirement_wiki_cache rwc 
                 LEFT JOIN wiki w
             WHERE (r.status = 'enabled')
                 AND (
                          r.component = rwc.component AND
                          r.fp = rwc.fp AND
                          r.object = rwc.object
                     ) 
                 AND (
                          w.name = rwc.wiki_name AND
                          w.version = rwc.wiki_version AND
                          w.version = (SELECT MAX(version) 
                                       FROM wiki 
                                       WHERE name = rwc.wiki_name)
                     )
             ORDER BY w.name, r.component, r.fp, r.object",
            'Show all requirements with wikis',9)
        """
        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report 
        VALUES('view/1','Most/Least Cited Requirements',
             "NO SQL",
             'Show most cited/least cited requirements',10)
        """

        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report 
        VALUES('view/2_Tasks','Most/Least requirements associated to Tasks, Enhancements or Defects',
             "NO SQL",
             'Show most/least requirements associated to Tasks, Enhancements or Defects',11)
        """

        cursor.execute(sql)
        
        sql = """
        INSERT INTO requirement_report
        VALUES('view/3','Most/Least Changed Requirements',
             "NO SQL",
             'Show most changed/least changed requirements',12)
        """

        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report
        VALUES('view/4','Most/Least Changed Milestones (via Requirement Changes)',
             "NO SQL",
             'Show most changed/least changed milestones based on associated requirement changes',13)
        """

        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report
        VALUES('view/5','Entropy metric',
             "NO SQL",
             'Calculate information entropy of requirements',14)
        """

        cursor.execute(sql)

        sql = """
        INSERT INTO requirement_report
        VALUES('view/6','Pointwise Mutual Information metric',
             "NO SQL",
             'Calculate the Pmi of each functional primitive, object pair',15)
        """

        cursor.execute(sql)

        #sql = """
        #INSERT INTO requirement_report
        #VALUES('report/4', 'Requirements by User',
        #       "SELECT r.creator AS __group__, "
        #       "'<' || r.component || ' ' || fp.name || ' ' || "
        #       "o.name || '>' AS 'Requirement', "
        #       "r.description AS 'Description', "
        #       "r.creator AS 'Creator' "
        #       "FROM requirement r, fp, object o "
        #       "WHERE r.status = 'enabled' "
        #       "AND r.fp = fp.id "
        #       "AND o.id = r.object "
         #      "ORDER BY r.component, fp.name, o.name",
         #      'Show all requirements, grouped by author', 4)
         #"""
        #cursor.execute(sql)


        self.env.db.commit()

        self.req.perm = PermissionCache(self.env, self.req.authname)

    def test_sub_var_no_quotes(self):
        sql, args = self.report_module.sql_sub_vars(self.req, "$VAR",
                                                    {'VAR': 'value'})
        self.assertEqual("%s", sql)
        self.assertEqual(['value'], args)

    def test_sub_var_quotes(self):
        sql, args = self.report_module.sql_sub_vars(self.req, "'$VAR'",
                                                    {'VAR': 'value'})
        self.assertEqual("''||%s||''", sql)
        self.assertEqual(['value'], args)

    def test_latex_report_1(self):
        self.req.method = 'GET'
        self.req.args = {'report': '1', 'format': 'latex'}
        old_stdout = sys.stdout
        store_stream = StoreStream()
        sys.stdout = store_stream
        self.report_module.process_request(self.req)
        sys.stdout = old_stdout

        latex = "\\item \\nreq{comp1}{fp1}{obj1}{A description}{}\n\\item \\nreq{comp1}{fp1}{obj2}{A description}{}\n\\item \\nreq{comp1}{fp1}{obj3}{A description}{}\n\\item \\nreq{comp1}{fp2}{obj1}{A description}{}\n\\item \\nreq{comp1}{fp3}{obj2}{A description}{}\n\\item \\nreq{comp2}{fp1}{obj3}{A description}{}\n\\item \\nreq{comp2}{fp2}{obj1}{A description}{}\n\\item \\nreq{comp3}{fp1}{obj4}{A description}{}\n\\item \\nreq{comp3}{fp3}{obj1}{A description}{}\n\\item \\nreq{comp3}{fp3}{obj2}{A description}{}\n\\item \\nreq{comp3}{fp4}{obj4}{A description}{}\n\\item \\nreq{comp\\_comp}{fp\\_fp}{obj\\_obj}{A description}{}\n"
        self.assertEqual(store_stream.text, latex)
        return True

    def test_regression_208(self):
        """Regression test for ticket #208

        Note: doesn't test views, due to future refactoring: #213
        """
        self.req.method = 'GET'
        self.req.path_info = '/requirements'
        self.report_module.process_request(self.req)
        self.assertRaises(KeyError, lambda: self.req.hdf['chrome.links.up.0']['href'] == '/trac/requirements')

        for i in range(1,9):
            self.req.path_info = '/requirements/report/%s' % i
            self.req.args = {'report': '%s' % i}
            self.report_module.process_request(self.req)
            try:
                self.req.hdf['chrome.links.up.0']['href'] == '/trac/requirements'
            except Exception:
                self.fail('Exception: report/%s' %i)


def suite():
    return unittest.makeSuite(ReportTestCase, 'test')

if __name__ == '__main__':
    unittest.main()
