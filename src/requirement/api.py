
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
import string
import time

from trac.config import *
from trac.core import *
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.Search import ISearchSource, search_to_sql, shorten_result
from trac.util.html import html, Markup
from trac.util.text import shorten_line
from trac.wiki import IWikiSyntaxProvider, Formatter

from trac.util.datefmt import format_date, format_time, http_date
from trac.util.text import to_unicode
from trac.web import IRequestHandler
from trac.web.chrome import add_link, add_stylesheet, INavigationContributor



class IRequirementChangeListener(Interface):
    """Extension point interface for components that require
    notification when requirements are created, modified, or deleted."""

    def requirement_created(requirement):
        """Called when a requirement is created."""

    def requirement_changed(requirement, comment, author, old_values):
        """Called when a requirement is modified.

        `old_values` is a dictionary containing the previous values of
        the fields that have changed.
        """

    def requirement_enabled(requirement, comment, author):
        """Called when a requirement is enabled."""

    def requirement_disabled(requirement, comment, author):
        """Called when a requirement is disabled."""

class RequirementSystem(Component):
    """API for Requirements system"""
    
    implements(IPermissionRequestor, IWikiSyntaxProvider, ISearchSource)

    change_listeners = ExtensionPoint(IRequirementChangeListener)

    # Public API

    def get_available_actions(self, requirment, perm_):
        return []

    def get_requirement_fields(self):
        fields = []
        
        fields.append({'name': 'component', 'type': 'component',
                       'label': 'Component'})
        fields.append({'name': 'fp', 'type': 'text',
                       'label': 'Functional Primitive'})
        fields.append({'name': 'object', 'type': 'text',
                       'label': 'Object'})
        fields.append({'name': 'creator', 'type': 'text',
                       'label': 'Creator'})
        fields.append({'name': 'description', 'type': 'textarea',
            'label': 'Description'})
        fields.append({'name': 'status', 'type': 'checkbox',
            'label': 'Status'})
        
        for field in self.get_custom_fields():
            if field['name'] in [f['name'] for f in fields]:
                self.log.warning('Duplicate field name "%s" (ignoring)',
                                 field['name'])
                continue
            if not re.match('^[a-zA-Z][a-zA-Z0-9_]+$', field['name']):
                self.log.warning('Invalid name for custom field: "%s" '
                                 '(ignoring)', field['name'])
                continue
            field['custom'] = True
            fields.append(field)
            
        return fields

    def get_custom_fields(self):
        fields = []
        config = self.config['requirement-custom']
        for name in [option for option, value in config.options()
                     if '.' not in option]:
            field = {
                'name': name,
                'type': config.get(name),
                'order': config.getint(name + '.order', 0),
                'label': config.get(name + '.label') or name.capitalize(),
                'value': config.get(name + '.value', '')
            }
            if field['type'] == 'select' or field['type'] == 'radio':
                field['options'] = config.getlist(name + '.options', sep='|')
                if '' in field['options']:
                    field['optional'] = True
                    field['options'].remove('')
            elif field['type'] == 'textarea':
                field['width'] = config.getint(name + '.cols')
                field['height'] = config.getint(name + '.rows')
            fields.append(field)

        fields.sort(lambda x, y: cmp(x['order'], y['order']))
        return fields

    # IPermissionRequestor methods

    def get_permission_actions(self):
        """
        append
        view
        disenable
        modify -> append
        create -> modify
        admin -> create, view, disenable
        """
        
        # Define the primitive permissions and a list containing them all.
        append_actions = ['REQUIREMENT_APPEND']
        view_actions = ['REQUIREMENT_VIEW']
        disenable_actions = ['REQUIREMENT_DISENABLE']
        primitive_actions = append_actions + view_actions + disenable_actions
        
        # Define meta permission names, the only purpose for these is
        # to reduce duplication so that they can be altered in one place
        # and have the effect take place through the function.
        modify_meta_action = 'REQUIREMENT_MODIFY'
        create_meta_action = 'REQUIREMENT_CREATE'
        admin_meta_action = 'REQUIREMENT_ADMIN'
        
        # Define the meta permission tuples.
        modify_meta_perm = [(modify_meta_action, append_actions)]
        create_meta_perm = [(create_meta_action, [modify_meta_action])]
        admin_meta_perm = [(admin_meta_action, [create_meta_action] + view_actions + disenable_actions)]
        
        return primitive_actions + modify_meta_perm + create_meta_perm + admin_meta_perm

    # IWikiSyntaxProvider methods

    def get_link_resolvers(self):
        return [('requirement', self._format_link),
                ('reqcomment', self._format_comment_link)]

    def get_wiki_syntax(self):
        """
        Syntax for referencing requirements.
        
        Examples:
        {{{
            requirement:component1-fp1-object1
            requirement:long_component_1-long_fp_1-long_object_1
            requirement:x-y-z
        }}}
        
        {{{
            &lt;component1 fp1 object1&gt;, &lt;long_component_1 long_fp_1 long_object_1&gt;, &lt;x y z&gt;
        }}}
        
        {{{
            <component1 fp1 object1>, <long_component_1 long_fp_1 long_object_1>, <x y z>
        }}}
        
        Escape (don't link):
        {{{
            !<component1 fp1 object1>,
            !<long_component_1 long_fp_1 long_object_1>,
            !<x y z>
        }}}
        
        InterTrac linking:
        {{{
            trac<component1 fp1 object1>
        }}}
        """
        # component_regex is all the components available in trac
        # organized to create a regular expression string.  
        component_regex = self._get_component_regex()
        yield (r"!?(?P<it_requirement>%s)(?P<req_bracket>(?:(?:&lt;)|<))"
               "(?P<component>%s) (?P<fp>\w+) (?P<object>\w+)"
               "(?(req_bracket)(?:(?:&gt;)|>))" % (Formatter.INTERTRAC_SCHEME, component_regex),
               lambda x, y, z: self._format_link(x, 'requirement', y, y, z))


    def _get_component_regex(self):
        """This method gets all the components
        from the component table and makes a 
        regular expression string out of them:

        cursor.execute("SELECT name FROM component"

        |component1|
        |component2|
        |component3|
        |component4|

        The output of this function is:

        (?:component1|component2|component3|component4)

        """
        from model import Requirement
        components = Requirement(self.env).get_components()
        component_regex = '(?:'
        component_regex += '|'.join( components )
        component_regex += ')'
        if component_regex == '(?:)':
            component_regex = 'nocomponent'
        return component_regex
    

    def _get_fp_regex(self):
        """This method gets all the fps
        from the fp table and makes a 
        regular expression string out of them:

        cursor.execute("SELECT name FROM component"

        |fp1|
        |fp2|
        |fp3|
        |fp4|

        The output of this function is:

        (?:fp1|fp2|fp3|fp4)

        """
        from model import Requirement
        fps = Requirement(self.env).get_fps()
        fp_regex = '(?:'
        fp_regex += '|'.join( fps )
        fp_regex += ')'
        if fp_regex == '(?:)':
            fp_regex = 'nofp'
        return fp_regex


    def _get_object_regex(self):
        """This method gets all the objects
        from the object table and makes a 
        regular expression string out of them:

        cursor.execute("SELECT name FROM object "

        |object1|
        |object2|
        |object3|
        |object4|

        The output of this function is:

        (?:object1|object2|object3|object4)

        """
        from model import Requirement
        objects = Object(self.env).get_objects()
        object_regex = '(?:'
        object_regex += '|'.join( objects )
        object_regex += ')'
        if object_regex == '(?:)':
            object_regex = 'nocomponent'
        return object_regex


    def _format_link(self, formatter, ns, target, label, fullmatch=None):
        label = re.sub('&lt;', '<', label)
        label = re.sub('&gt;', '>', label)
        
        intertrac = formatter.shorthand_intertrac_helper(ns, target, label, fullmatch)
        if intertrac:
            if hasattr(intertrac, 'attr'):
                intertrac.attr.update({'href': re.sub(r'/requirement/<(\w+) (\w+) (\w+)>', r'/requirement/\1-\2-\3', intertrac.attr['href'])})
                intertrac.attr.update({'title': re.sub(r'requirement:<(.*?)>', r'<\1>', intertrac.attr['title'])})
            return intertrac
        
        component = fp = object = None
        
        if fullmatch:
            (component, fp, object) = fullmatch.group('component', 'fp', 'object')
        else:
            try:
                matches = re.match(r'(?P<component>\w+)-(?P<fp>\w+)-(?P<object>\w+)', target)
                (component, fp, object) = (matches.group('component'),
                                           matches.group('fp'),
                                           matches.group('object'))
            except:
                pass
        
        try:
            cursor = formatter.db.cursor()
            cursor.execute("SELECT description FROM requirement "
                           "WHERE component=%s AND fp=%s AND object=%s",
                           (component,fp,object))
            row = cursor.fetchone()
            if row:
                return html.A(label, class_='existant requirement',
                              title=(shorten_line(row[0])),
                              href=formatter.href.requirement("%s-%s-%s" % (component, fp, object)))
        except ValueError:
            pass
        return html.A(label, class_='missing requirement', rel='nofollow',
                      href=formatter.href.requirement("%s-%s-%s" % (component, fp, object)))

    def _format_comment_link(self, formatter, ns, target, label):
        # Note that id is something like "x-y-z"
        type, id, cnum = 'requirement', None, 0
        href = None
        if ':' in target:
            elts = target.split(':')
            if len(elts) == 3:
                type, id, cnum = elts
                href = formatter.href(type, id)
        else:
            if formatter.req:
                path_info = formatter.req.path_info.strip('/').split('/', 2)
                if len(path_info) == 2:
                    type, id = path_info[:2]
                    href = formatter.href(type, id)
                    cnum = target
        if href:
            return html.A(label, href="%s#reqcomment:%s" % (href, cnum),
                          title="Comment %s for %s:%s" % (cnum, type, id))
        else:
            return label

    # ISearchSource methods

    def get_search_filters(self, req):
        if req.perm.has_permission('REQUIREMENT_VIEW'):
            yield ('requirement', 'Requirements', True)

    def get_search_results(self, req, terms, filters):
        """
        Search through requirements.
        
        The search term may be <x y z> or x-y-z; both are interpreted as
        component, fp, and object.
        """
        
        if not 'requirement' in filters:
            return
        
        if re.match(r'^([a-zA-Z_\d]+)-([a-zA-Z_\d]+)-([a-zA-Z_\d]+)$', terms[0]):
            terms = string.split(terms[0], '-')
            
        db = self.env.get_db_cnx()
        sql, args = search_to_sql(db, ['b.newvalue'], terms)
        sql2, args2 = search_to_sql(db, ['a.component', 'a.fp', 'a.object',
                                         'a.description', 'a.creator'], terms)
        
        cursor = db.cursor()
        cursor.execute("SELECT DISTINCT a.component, a.fp, a.object, "
                       "a.description, a.creator, a.time "
                       "FROM requirement a "
                       "LEFT JOIN requirement_change b "
                       "ON a.component = b.component AND a.fp = b.fp AND a.object = b.object "
                       "WHERE (b.field='comment' AND %s ) OR %s" % (sql, sql2),
                       args + args2)
        
        for component, fp, object, desc, creator, date in cursor:
            requirement = '<%s %s %s> ' % (component, fp, object)
            yield (req.href.requirement('%s-%s-%s' % (component, fp, object)),
                   requirement + shorten_line(desc),
                   date, creator, shorten_result(desc, terms))
        
        
class IObjectChangeListener(Interface):
    """Extension point interface for components that require
    notification when objects are created, modified, or deleted."""

    def object_created(object):
        """Called when an object is created."""

    def object_changed(object, comment, author, old_values):
        """Called when an object is modified.

        `old_values` is a dictionary containing the previous values of
        the fields that have changed.
        """

    def object_enabled(object, comment, author):
        """Called when an object is enabled."""

    def object_disabled(object, comment, author):
        """Called when an object is disabled."""

class ObjectSystem(Component):
    """API for Object system"""
   
    implements(IPermissionRequestor)

    change_listeners = ExtensionPoint(IObjectChangeListener)
 
    def get_available_actions(self, object, perm_):
        """Returns the actions that can be performed on the object."""

        return []

    def get_object_fields(self):
        fields = []

        fields.append({'name': 'name', 'type': 'text', 'label': 'Name'})
        fields.append({'name': 'description', 'type': 'textarea',
                     'label': 'Description'})
        fields.append({'name': 'status', 'type': 'checkbox', 'label': 'Status'})
        
        #make sure that the names are valid 
        for field in self.get_custom_fields():
            if field['name'] in [f['name'] for f in fields]:
                self.log.warning('Duplicate field name "%s" (ignoring)',
                                 field['name'])
                continue
            if not re.match('^[a-zA-Z][a-zA-Z0-9_]+$', field['name']):
                self.log.warning('Invalid name for custom field: "%s" '
                                 '(ignoring)', field['name'])
                continue
            field['custom'] = True
            fields.append(field)

        return fields        

    def get_custom_fields(self):
        """Get custom fields from config file"""

        fields = []
        config = self.config['object-custom']
        for name in [option for option, value in config.options()
                     if '.' not in option]:
            field = {
                'name': name,
                'type': config.get(name),
                'order': config.getint(name + '.order', 0),
                'label': config.get(name + '.label') or name.capitalize(),
                'value': config.get(name + '.value', '')
            }
            if field['type'] == 'select' or field['type'] == 'radio':
                field['options'] = config.getlist(name + '.options', sep='|')
                if '' in field['options']:
                    field['optional'] = True
                    field['options'].remove('')
            elif field['type'] == 'textarea':
                field['width'] = config.getint(name + '.cols')
                field['height'] = config.getint(name + '.rows')
            fields.append(field)

        fields.sort(lambda x, y: cmp(x['order'], y['order']))
 
        return fields

    def get_permission_actions(self):
        """These are exactly the same as the requirement permissions.

        append
        view
        disable
        modify -> append
        create -> modify
        admin -> create, view, disable
        """
        # Define the primitive permissions and a list containing them all.
        append_actions = ['OBJECT_APPEND']
        view_actions = ['OBJECT_VIEW']
        disable_actions = ['OBJECT_DISABLE']
        primitive_actions = append_actions + view_actions + disable_actions

        # Define meta permission names, the only purpose for these is
        # to reduce duplication so that they can be altered in one place
        # and have the effect take place through the function.
        modify_meta_action = 'OBJECT_MODIFY'
        create_meta_action = 'OBJECT_CREATE'
        admin_meta_action = 'OBJECT_ADMIN'

        # Define the meta permission tuples.
        modify_meta_perm = [(modify_meta_action, append_actions)]
        create_meta_perm = [(create_meta_action, [modify_meta_action])]
        admin_meta_perm = [(admin_meta_action, [create_meta_action] + \
                          view_actions + disable_actions)]

        return primitive_actions + modify_meta_perm + create_meta_perm + \
               admin_meta_perm


class IFpChangeListener(Interface):
    """Extension point interface for components that require
    notification when fp's are created, modified, or deleted."""

    def fp_created(fp):
        """Called when a fp is created."""

    def fp_changed(fp, comment, author, old_values):
        """Called when a fp is modified.

        `old_values` is a dictionary containing the previous values of
        the fields that have changed.
        """

    def fp_enabled(fp, comment, author):
        """Called when a fp is enabled."""

    def fp_disabled(fp, comment, author):
        """Called when a fp is disabled."""

class FpSystem(Component):    
    """API for fp system"""
 
    change_listeners = ExtensionPoint(IFpChangeListener)

    def get_available_actions(self, fp, perm_):
        return []

    def get_fp_fields(self):
        fields = []

        fields.append({'name':'name','type':'text','label':'Name'})
        fields.append({'name':'description','type':'textarea',
                        'label':'Description'})
        fields.append({'name':'status','type':'checkbox','label':'Status'})

        return fields

    def get_custom_fields(self):
        return []

    def get_permission_actions(self):
        """These are exactly the same as the requirement permissions.

        append
        view
        disenable
        modify -> append
        create -> modify
        admin -> create, view, disable
        """
        # Define the primitive permissions and a list containing them all.
        append_actions = ['FP_APPEND']
        view_actions = ['FP_VIEW']
        disable_actions = ['FP_DISENABLE']
        primitive_actions = append_actions + view_actions + disable_actions

        # Define meta permission names, the only purpose for these is
        # to reduce duplication so that they can be altered in one place
        # and have the effect take place through the function.
        modify_meta_action = 'FP_MODIFY'
        create_meta_action = 'FP_CREATE'
        admin_meta_action = 'FP_ADMIN'

        # Define the meta permission tuples.
        modify_meta_perm = [(modify_meta_action, append_actions)]
        create_meta_perm = [(create_meta_action, [modify_meta_action])]
        admin_meta_perm = [(admin_meta_action, [create_meta_action] + \
                          view_actions + disable_actions)]

        return primitive_actions + modify_meta_perm + \
               create_meta_perm + admin_meta_perm

class IHyponymChangeListener(Interface):
    """Extension point interface for components that require
    notification when hyponym's are created, modified, or deleted."""

    def hyponym_created(hyponym):
        """Called when a hyponym is created."""

    def hyponym_changed(hyponym, comment, author, old_values):
        """Called when a hyponym is modified.

        `old_values` is a dictionary containing the previous values of
        the fields that have changed.
        """

    def hyponym_enabled(hyponym, comment, author):
        """Called when a hyponym is enabled."""

    def hyponym_disabled(hyponym, comment, author):
        """Called when a hyponym is disabled."""

class HyponymSystem(Component):
    """API for Hyponym system"""
   
    implements(IPermissionRequestor)

    change_listeners = ExtensionPoint(IHyponymChangeListener)
 
    def get_available_actions(self, hyponym, perm_):
        """Returns the actions that can be performed on the hyponym."""

        return []

    def get_hyponym_fields(self):
        fields = []

        fields.append({'name': 'name', 'type': 'text', 'label': 'Name'})
        fields.append({'name': 'fp', 'type': 'text',
                     'label': 'Functional Primative'})
        fields.append({'name': 'status', 'type': 'checkbox', 'label': 'Status'})
        
        #make sure that the names are valid 
        for field in self.get_custom_fields():
            if field['name'] in [f['name'] for f in fields]:
                self.log.warning('Duplicate field name "%s" (ignoring)',
                                 field['name'])
                continue
            if not re.match('^[a-zA-Z][a-zA-Z0-9_]+$', field['name']):
                self.log.warning('Invalid name for custom field: "%s" '
                                 '(ignoring)', field['name'])
                continue
            field['custom'] = True
            fields.append(field)

        return fields        

    def get_custom_fields(self):
        """Get custom fields from config file"""

        fields = []
        config = self.config['hyponym-custom']
        for name in [option for option, value in config.options()
                     if '.' not in option]:
            field = {
                'name': name,
                'type': config.get(name),
                'order': config.getint(name + '.order', 0),
                'label': config.get(name + '.label') or name.capitalize(),
                'value': config.get(name + '.value', '')
            }
            if field['type'] == 'select' or field['type'] == 'radio':
                field['options'] = config.getlist(name + '.options', sep='|')
                if '' in field['options']:
                    field['optional'] = True
                    field['options'].remove('')
            elif field['type'] == 'textarea':
                field['width'] = config.getint(name + '.cols')
                field['height'] = config.getint(name + '.rows')
            fields.append(field)

        fields.sort(lambda x, y: cmp(x['order'], y['order']))
 
        return fields

    def get_permission_actions(self):
        """These are exactly the same as the requirement permissions.

        append
        view
        disable
        modify -> append
        create -> modify
        admin -> create, view, disable
        """

        # Define the primitive permissions and a list containing them all.
        append_actions = ['HYPONYM_APPEND']
        view_actions = ['HYPONYM_VIEW']
        disable_actions = ['HYPONYM_DISABLE']
        primitive_actions = append_actions + view_actions + disable_actions

        # Define meta permission names, the only purpose for these is
        # to reduce duplication so that they can be altered in one place
        # and have the effect take place through the function.
        modify_meta_action = 'HYPONYM_MODIFY'
        create_meta_action = 'HYPONYM_CREATE'
        admin_meta_action = 'HYPONYM_ADMIN'

        # Define the meta permission tuples.
        modify_meta_perm = [(modify_meta_action, append_actions)]
        create_meta_perm = [(create_meta_action, [modify_meta_action])]
        admin_meta_perm = [(admin_meta_action, [create_meta_action] + \
                          view_actions + disable_actions)]

        return primitive_actions + modify_meta_perm + create_meta_perm + \
               admin_meta_perm
