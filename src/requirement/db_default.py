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

from trac.db import Table, Column, Index

db_version = 11

schema = [
          Table('fp', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('description'),
            Column('status'),
            Column('time', type='int'),
            Column('changetime', type='int')],
          Table('fp_custom', key=('id', 'name'))[
            Column('id'),
            Column('name'),
            Column('value')],
          Table('hyponym', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('fp', type='int'),
            Column('status'),
            Column('changetime', type='int'),
            Column('time', type='int')],
          Table('hyponym_custom', key=('id','name'))[
            Column('id', type='int'),
            Column('name'),
            Column('value')],
          Table('object', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('status'),
            Column('description'),
            Column('changetime', type='int'),
            Column('time', type='int')],
          Table('object_custom', key=('id','name'))[
            Column('id', type='int'),
            Column('name'),
            Column('value')],
          Table('on_the_fly', key=('name'))[
            Column('name'),
            Column('status')],
          Table('requirement', key=('component','fp','object'))[
            Column('component'),
            Column('fp', type='int'),
            Column('object', type='int'),
            Column('time', type='int'),
            Column('changetime', type='int'),
            Column('creator'),
            Column('status'),
            Column('description')],
          Table('requirement_change', key=('component','fp','object','time','field'))[
            Column('component'),
            Column('fp', type='int'),
            Column('object', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
          Table('requirement_custom', key=('component','fp','object','name'))[
            Column('component'),
            Column('fp', type='int'),
            Column('object', type='int'),
            Column('name'),
            Column('value')],
          Table('requirement_ticket_cache', key=('component','fp','object','ticket'))[
            Column('component'),
            Column('fp'),
            Column('object'),
            Column('ticket', type='int')],
          Table('requirement_wiki_cache', key=('component','fp','object','wiki_name','wiki_version'))[
            Column('component'),
            Column('fp'),
            Column('object'),
            Column('wiki_name'),
            Column('wiki_version')],
          Table('requirement_report', key=('report'))[
            Column('report'),
            Column('title'),
            Column('query'),
            Column('description'),
            Column('key', type='int')],
          Table('requirement_validation', key='date')[
            Column('date', type='int'),
            Column('uid')],
          Table('fp_change', key=('id','time','field'))[
            Column('id', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
          Table('hyponym_change', key=('id', 'time', 'field'))[
            Column('id', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
          Table('object_change', key=('id', 'time', 'field'))[
            Column('id', type='int'),
            Column('time', type='int'),
            Column('author'),
            Column('field'),
            Column('oldvalue'),
            Column('newvalue')],
          Table('requirement_data_cache', key=('component','fp','object','name'))[
            Column('component'),
            Column('fp'),
            Column('object'),
            Column('name'),
            Column('data', type='blob')],
]

##
## Default database values
##

# (table, (column1, column2), ((row1col1, row1col2), (row2col1, row2col2)))
def get_data(db):
    return (('system',
             ('name', 'value'),
             (('lifecyclemanager_version', str(db_version)),)),
            ('on_the_fly',
             ('name','status'),
             (('fp','enabled'),
             ('object','enabled'))),
            ('requirement_report',
             ('report', 'title', 'query', 'description', 'key'),
             (('report/1', 'Requirements by Component',
               "SELECT r.component AS __group__, "
               "'<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' as 'Requirement', "
               "r.description AS 'Description', "
               "r.creator AS 'Creator' "
               "FROM requirement r, fp, object o "
               "WHERE r.status <> 'disabled' " 
               "AND r.fp = fp.id "
               "AND o.id = r.object "
               "ORDER BY r.component, fp.name, o.name",
               'Show all requirements, grouped by component', '1'),
              ('report/2', 'Requirements by Object',
               "SELECT o.name AS __group__, "
               "'<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' AS 'Requirement', "
               "r.description AS 'Description', "
               "r.creator AS 'Creator' "
               "FROM requirement r, fp, object o "
               "WHERE r.status <> 'disabled' "
               "AND r.fp = fp.id "
               "AND o.id = r.object "
               "ORDER BY o.name, r.component, fp.name",
               'Show all requirements, grouped by object', '2'),
              ('report/3', 'Requirements by Functional Primitive',
               "SELECT fp.name AS __group__, "
               "'<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' AS 'Requirement', "
               "r.description AS 'Description', "
               "r.creator AS 'Creator' "
               "FROM requirement r, fp, object o "
               "WHERE r.status <> 'disabled' "
               "AND r.fp = fp.id "
               "AND o.id = r.object "
               "ORDER BY fp.name, r.component, o.name",
               'Show all requirements, grouped by functional primitive', '3'),
              ('report/4', 'Requirements by User',
               "SELECT r.creator AS __group__, "
               "'<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' AS 'Requirement', "
               "r.description AS 'Description' "
               "FROM requirement r, fp, object o "
               "WHERE r.status <> 'disabled' "
               "AND r.fp = fp.id "
               "AND o.id = r.object "
               "ORDER BY r.creator, r.component, fp.name, o.name",
               'Show all requirements, grouped by author', '4'), 
              ('report/5', 'Requirements with Associated Tickets',
               "SELECT ('<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>') AS __group__, "
               "'#' || rtc.ticket AS 'ticket', "
               "t.summary AS 'summary' "
               "FROM object o INNER JOIN fp INNER JOIN requirement r "
               "LEFT JOIN requirement_ticket_cache rtc "
               "LEFT JOIN ticket t "
               "WHERE (o.id = r.object) AND (fp.id = r.fp) "
               "AND (r.status <> 'disabled') "
               "AND (r.component = rtc.component AND "
               "fp.name = rtc.fp AND "
               "o.name = rtc.object "
               ") AND ("
               "t.id = rtc.ticket"
               ") "
               "ORDER BY r.component, fp.name, o.name, rtc.ticket",
               'Show all requirements with associated tickets', '5'),
              ('report/6', 'Requirements Changed during Milestone (changetime < due)',
               "SELECT m.name AS __group__, "
               "'<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' as 'Requirement', "
               "r.description AS 'Description', "
               "r.creator AS 'Creator' "
               "FROM object o INNER JOIN fp INNER JOIN requirement r "
               "LEFT JOIN milestone m "
               "WHERE (o.id = r.object) AND (fp.id = r.fp) "
               "AND (r.status <> 'disabled') "
               "AND (r.changetime < m.due) "
               "ORDER BY m.name, r.component, fp.name, o.name",
               'Show all requirements, grouped by milestone, where requirement.changetime < milestone.due', '6'),
              ('report/7', 'Requirements by Milestone (via ticket)',
               "SELECT m.name AS __group__, "
               "'<' || r.component || ' ' || r.fp || ' ' || "
               "r.object || '>' as 'Requirement', "
               "r.description AS 'Description', "
               "r.creator AS 'Creator' "
               "FROM milestone m "
               "INNER JOIN "
               "(SELECT r.component AS component, "
               "fp.name AS fp, "
               "o.name AS object, "
               "r.description AS description, "
               "r.creator AS creator, "
               "t.milestone AS milestone "
               "FROM object o INNER JOIN fp INNER JOIN requirement r "
               "LEFT JOIN requirement_ticket_cache rtc  "
               "LEFT JOIN ticket t "
               "WHERE (o.id = r.object) AND (fp.id = r.fp) "
               "AND (r.status <> 'disabled') "
               "AND (r.component = rtc.component AND "
               "fp.name = rtc.fp AND "
               "o.name = rtc.object "
               ") AND ("
               "t.id = rtc.ticket"
               ")"
               "GROUP BY t.milestone, r.component, fp.name, o.name "
               "ORDER BY r.component, fp.name, o.name "
               ") r "
               "ON r.milestone = m.name "
               "ORDER BY r.milestone",
               'Show all requirements, grouped by milestone (via ticket)', '7'),
              ('report/8', 'Disabled Requirements by Component',
               "SELECT r.component AS __group__, "
               "'<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' as 'Requirement', "
               "r.description AS 'Description', "
               "r.creator AS 'Creator' "
               "FROM requirement r, fp, object o "
               "WHERE r.status = 'disabled' "
               "AND fp.id = r.fp "
               "AND o.id = r.object "
               "ORDER BY r.component, fp.name, o.name",
               'Show all disabled requirements, grouped by component', '8'),
              ('report/9', 'Requirements with Wikis (a.k.a. Wikis by Requirement)',
               "SELECT '<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' AS __group__, "
               "w.name as 'Wiki', "
               "w.comment as 'Comment', "
               "w.version as 'Version', "
               "w.author AS 'Creator' "
               "FROM object o INNER JOIN fp INNER JOIN requirement r "
               "LEFT JOIN requirement_wiki_cache rwc "
               "LEFT JOIN wiki w "
               "WHERE (o.id = r.object) AND (fp.id = r.fp) "
               "AND (r.status <> 'disabled') "
               "AND ("
               "r.component = rwc.component AND "
               "fp.name = rwc.fp AND "
               "o.name = rwc.object "
               ") AND ("
               "w.name = rwc.wiki_name AND "
               "w.version = rwc.wiki_version "
               ") "
               "ORDER BY r.component, fp.name, o.name",
               'Show all requirements with wikis', '9'),
              ('report/10', 'Requirements by Wiki',
               "SELECT w.name AS __group__, "
               "'<' || r.component || ' ' || fp.name || ' ' || "
               "o.name || '>' as Requirement, "
               "r.description as 'Description', "
               "r.creator as 'Creator' "
               "FROM object o INNER JOIN fp INNER JOIN requirement r "
               "LEFT JOIN requirement_wiki_cache rwc "
               "LEFT JOIN wiki w "
               "WHERE (o.id = r.object) AND (fp.id = r.fp) "
               "AND (r.status <> 'disabled') "
               "AND ("
               "r.component = rwc.component AND "
               "fp.name = rwc.fp AND "
               "o.name = rwc.object "
               ") AND ("
               "w.name = rwc.wiki_name AND "
               "w.version = rwc.wiki_version AND "
               "w.version = (SELECT MAX(version) "
               "FROM wiki "
               "WHERE name = rwc.wiki_name)"
               ") "
               "ORDER BY w.name, r.component, fp.name, o.name",
               'Show all requirements with wikis', '10'),
              ('report/11', 'Requirements by Out-Of-Date Status',
               "SELECT r.status AS __group__,'<' || r.component "
               "|| ' ' || fp.name || ' ' || "
               "o.name || '>' AS 'Requirement' "
               "FROM requirement r, fp, object o "
               "WHERE r.status = 'out-of-date' "
               "AND r.fp = fp.id "
               "AND o.id = r.object "
               "ORDER BY r.component, fp.name, o.name",
               'Show all out-of-date requirements', '11'),
              ('report/12', 'Requirements Changed Since Last Validation',
               "SELECT r.component AS __group__, '<' || r.component "
               "|| ' ' || fp.name || ' ' || "
               "o.name || '>' AS 'Requirement' "
               "FROM requirement r, fp, object o "
               "WHERE r.changetime > (SELECT max(date) "
                                     "FROM requirement_validation) "
               "AND r.fp = fp.id "
               "AND r.object = o.id "
               "ORDER BY r.component, fp.name, o.name",
               'Show all requirements changed since last validation', '12'),
              ('view/1', 'Most/Least Cited Requirements',
               'NO SQL', 'Show most cited/least cited requirements', '13'),
              ('view/2_Tasks', 'Most/Least requirements associated to Tasks, Enhancements or Defects',
               'NO SQL', 'Show most/least requirements associated to Tasks, Enhancements or Defects', '14'),
              ('view/3', 'Most/Least Changed Requirements',
               'NO SQL', 'Show most changed/least changed requirements', '15'),
              ('view/4', 'Most/Least Changed Milestones (via Requirement Changes)',
               'NO SQL', 'Show most changed/least changed milestones based on associated requirement changes', '16'),
              ('view/5', 'Entropy metric',
               'NO SQL', 'Calculate information entropy of requirements', '17'),
              ('view/6', 'Pointwise Mutual Information metric',
               'NO SQL', 'Calculate the Pmi of each functional primitive, object pair', '18'),
              ('view/7', 'Timeline of changes report',
               'NO SQL', 'Timeline of changes per stage', '19'),
              ('view/8', 'History Activity report',
               'NO SQL', 'Per-user history of activity report', '20'))))
