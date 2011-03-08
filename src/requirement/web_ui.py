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
import time
import pickle
import base64
from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import add_stylesheet, add_script, add_link
from trac.util.html import html
from trac.wiki.formatter import wiki_to_html
from trac.perm import IPermissionRequestor
from trac.util import get_reporter_id
from model import Requirement
from model import Fp
from model import Hyponym
from model import Object
from requirement import RequirementComponent
from api import RequirementSystem
from api import IFpChangeListener
from api import IObjectChangeListener
from trac.perm import IPermissionRequestor
from trac.util.datefmt import format_datetime, pretty_timedelta, http_date

class RequirementModule(Component):
    implements(IRequestHandler, IFpChangeListener, IObjectChangeListener)
       
    # IRequestHandler methods
    def match_request(self, req):
        if re.match(r'/requirement/\w+-\w+-\w+/?$', req.path_info) is not None:
            return True
        else:
            return False

 
    def process_request(self, req):
        template = 'requirement.cs';
        db = self.env.get_db_cnx()

        if req.method == 'POST' and 'creator' in req.args and \
                not req.perm.has_permission('REQUIREMENT_MODIFY'):
            del req.args['creator']
        
        if req.method == 'POST': 
            self._do_modify(req, db)
        else:
            (component, fp, object) = self._get_requirement_parts(req)
            fp = Fp(self.env, name=fp)
            object = Object(self.env, name=object)
            requirement = Requirement(self.env, component, fp['id'], 
                                     object['id'], db)
            req.hdf['components'] = requirement.get_components() 
            req.hdf['requirement'] = requirement.values
            req.hdf['fp'] = fp['name']
            req.hdf['object'] = object['name']
            req.hdf['requirement.created'] = format_datetime(requirement.time_created)
            req.hdf['requirement.created_delta'] = pretty_timedelta(requirement.time_created)
            if requirement.time_changed != requirement.time_created:
                req.hdf['requirement'] = {
                    'lastmod': format_datetime(requirement.time_changed),
                    'lastmod_delta': pretty_timedelta(requirement.time_changed)
                }

            for field in RequirementSystem(self.env).get_requirement_fields():
                if field['type'] in ('radio', 'select'):
                    value = requirement.values.get(field['name'])
                    options = field['options']
                    if value and not value in options:
                        options.append(value)
                    field['options'] = options
                name = field['name']
                del field['name']
                if name in ('component', 'fp', 'object', 'status', 'creator', 'description'):
                    field['skip'] = True
                req.hdf['requirement.fields.' + name] = field

            req.hdf['requirement.description.formatted'] = wiki_to_html(
                requirement['description'], self.env, req, db)

            replyto = req.args.get('replyto')
            req.hdf['requirement'] = {
                'href': req.href.requirement('%s-%s-%s' % (requirement.component,
                                                           fp['name'],
                                                           object['name'])),
                'replyto': replyto
            }
            def quote_original(author, original, link):
                if not 'comment' in req.args: # i.e. the comment was not yet edited
                    req.hdf['requirement.comment'] = '\n'.join(
                        ['Replying to [%s %s]:' % (link, author)] +
                        ['> %s' % line for line in original.splitlines()] + [''])

            if replyto == 'description':
                quote_original(requirement['creator'], requirement['description'],
                               'requirement:%s-%s-%s' % (requirement.component,
                                                         fp['name'],
                                                         object['name']))

            replies = {}
            changes = []
            cnum = 0
            description_lastmod = description_author = None
            for change in self.grouped_changelog_entries(requirement, db):
                changes.append(change)
                # wikify comment
                comment = ''
                if 'comment' in change:
                    comment = change['comment']
                    change['comment'] = wiki_to_html(comment, self.env, req, db)

                cnum = change['cnum']
                # keep track of replies threading
                if 'replyto' in change:
                    replies.setdefault(change['replyto'], []).append(cnum)
                # eventually cite the replied to comment
                if replyto == str(cnum):
                    quote_original(change['author'], comment,
                                   'reqcomment:%s' % replyto)

                if 'description' in change['fields']:
                    change['fields']['description'] = ''
                    description_lastmod = change['date']
                    description_author = change['author']

            req.hdf['requirement'] = {
                'changes': changes,
                'replies': replies,
                'cnum': cnum + 1
                }

            if description_lastmod:
                req.hdf['requirement.description'] = {'lastmod': description_lastmod,
                                                      'author': description_author}

        req.hdf['title'] = 'Requirements'
        req.hdf['graph_path'] = req.href.requirement() + '/graph/'

        actions = RequirementSystem(self.env).get_available_actions(requirement, req.perm)
        for action in actions:
            req.hdf['requirement.actions.' + action] = '1'

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'hw/css/requirement.css')
        return (template, None)
 
   
    def _do_modify(self, req, db):
        self._do_arg_checks(req)
        component = req.args.get('component')
        fp = Fp(self.env, name=req.args.get('fp'))
        object = Object(self.env, name=req.args.get('object'))

        requirement = Requirement(self.env, component, fp['id'], object['id'], 
                                 db)

        status = requirement['status']
        requirement.populate(req.args)
        requirement['fp'] = fp['id']
        requirement['object'] = object['id']
        requirement['status'] = status

        now = int(time.time())
        cnum = req.args.get('cnum')
        replyto = req.args.get('replyto')
        internal_cnum = cnum
        if cnum and replyto:
            internal_cnum = '%s.%s' % (replyto, cnum)
    
        if (status != 'disabled' and req.args.get('status') != 'on') \
            or \
           (status == 'disabled' and req.args.get('status') == 'on'):

            req.perm.assert_permission('REQUIREMENT_DISENABLE')
            
            if req.args.get('status') == 'on':
                requirement['status'] = 'enabled'
            else:
                requirement['status'] = 'disabled'
            
        if requirement.save_changes(get_reporter_id(req, 'author'),
                                    req.args.get('comment'), when=now, db=db,
                                    cnum=internal_cnum):
            db.commit()

            # Notify
            try:
                rn = RequirementNotifyEmail(self.env)
                rn.notify(requirement, newrequirement=False)
            except Exception, e:
                self.log.exception("Failure sending notification on creation "
                                   "of requirement <%s %s>: %s" % 
                                   (fp['name'], object['name'], e))

        fragment = cnum and '#comment:'+cnum or ''

        # Redirect the user to the newly created requirement
        req.redirect(req.href.requirement("%s-%s-%s" %
                    (requirement.component, fp['name'], object['name'])) 
                                          + fragment)


    def _list_requirements(self, req, db):
        return Requirement(self.env, db=db).get_requirements()

    def _get_requirement_parts(self, req):
        uri = req.path_info
        uri_list = uri.split('/')
        hyphenated_pk = uri_list.pop()
        return hyphenated_pk.split('-')

    def _do_arg_checks(self, req):
        if not req.args.get('component'):
            raise TracError('Requirements must contain a component.')
        
        if not req.args.get('fp'):
            raise TracError('Functional primitive cannot be removed.')
        
        if not req.args.get('object'):
            raise TracError('Object cannot be removed.')

    def grouped_changelog_entries(self, requirement, db, when=0):
        """Iterate on changelog entries, consolidating related changes
        in a `dict` object.
        """
        changelog = requirement.get_changelog(when=when, db=db)
        autonum = 0 # used for "root" numbers
        last_uid = current = None
        for date, author, field, old, new in changelog:
            uid = date, author
            if uid != last_uid:
                if current:
                    yield current
                last_uid = uid
                current = {
                    'http_date': http_date(date),
                    'date': format_datetime(date),
                    'author': author,
                    'fields': {}
                }
                if not when:
                    autonum += 1
                    current['cnum'] = autonum
            # some common processing for fields
            if field == 'comment':
                current['comment'] = new
                if old:
                    if '.' in old: # retrieve parent.child relationship
                        parent_num, this_num = old.split('.', 1)
                        current['replyto'] = parent_num
                    else:
                        this_num = old
                    current['cnum'] = int(this_num)
            else:
                current['fields'][field] = {'old': old, 'new': new}
        if current:
            yield current

    #IFpChangeListener interface's required methods.

    def fp_created(self, fp):
        pass

    def fp_changed(self, fp, comment, author, old_values):
        pass

    def fp_disabled(self, fp, comment, author):
        """Use functions in the model to set Req status as needed."""
        Requirement(fp.env).set_ood_by_fp(fp['id'], comment, author)

    def fp_enabled(self, fp, comment, author):
        """Use functions in the model to enable Reqs as needed."""
        Requirement(fp.env).enable_ood_by_fp(fp['id'], comment, author)

    #IObjectChangeListener interface's required methods.

    def object_created(self, object):
        pass

    def object_changed(self, object, comment, author, old_values):
        pass

    def object_disabled(self, object, comment, author):
        """Use functions in the model to set Req status as needed."""
        Requirement(object.env).set_ood_by_object(object['id'], comment, author)

    def object_enabled(self, object, comment, author):
        """Use functions in the model to enable Reqs as needed."""
        Requirement(object.env).enable_ood_by_object(object['id'], comment, \
                                                     author)


class NewrequirementModule(Component):
    implements(IRequestHandler)
        
        
    def match_request(self, req):
        return re.match(r'/newrequirement/?$', req.path_info) is not None
    
    def process_request(self, req):
        req.perm.assert_permission('REQUIREMENT_CREATE')
        template = 'newrequirement.cs';
        
        # No need to preview a tiny form like this
        if req.method == 'POST' and not req.args.has_key('preview'):
            self._do_create(req)
            
        requirement = Requirement(self.env)
        req.hdf['components'] = requirement.get_components() 
        req.hdf['trac.href.newrequirement'] = req.href.newrequirement()
        req.hdf['trac.href.auto_complete'] = req.href.newrequirement('ajax')

            
        req.hdf['title'] = 'New Requirement'

        # Provide FORM_TOKEN for Ajax POST request
        req.hdf['form_token'] = req.form_token
        

        add_stylesheet(req, 'hw/css/requirement.css')
        add_script(req, 'hw/javascript/prototype.js')
        add_script(req, 'hw/javascript/scriptaculous.js')
        return (template, None)
    
    def _do_create(self, req, db=None):
        if not req.args.get('component'):
            raise TracError('Requirements must contain a component.')
        
        if not req.args.get('fp'):
            raise TracError('Requirements must contain a functional primitive.')
        
        if not req.args.get('object'):
            raise TracError('Requirements must contain an object.')

        requirement = Requirement(self.env, db=db)
        requirement.populate(req.args)
        try:
            # if a known hyponym was used, get corresponding fp.
            temp_hyp = Hyponym(self.env, name=req.args.get('fp'), db=db)
            temp_fp = Fp(self.env, id=temp_hyp['fp'], db=db)
        except TracError:
            try:
                #or, if a known fp was used, get instance of Fp
                temp_fp = Fp(self.env, name=req.args.get('fp'), db=db)
            except TracError:
                #run check funtion for enabled adding fp
                #if unknown fp used, insert it into the database
                if(Fp(self.env).check_on_fly_fp() == "enabled"):
                    temp_fp = Fp(self.env, db=db)
                    temp_fp['name'] = req.args.get('fp')
                    temp_fp.insert(db=db)
                else:
                    raise TracError("On the fly creation of Fps disabled")
        requirement.values['fp'] = temp_fp['id']
        try:
            temp_object = Object(self.env, name=req.args.get('object'), db=db)
        except TracError:
        #run check for function enabling obj
            if(Object(self.env).check_on_fly_obj() == "enabled"): 
                temp_object = Object(self.env, db=db)
                temp_object['name'] = req.args.get('object')
                temp_object.insert(db=db)
            else:
                raise TracError("On the fly creation of objects disabled")
        requirement.values['object'] = temp_object['id']
        requirement.values['creator'] = get_reporter_id(req, 'creator')
        requirement.insert(db=db)

        # Notify
        try:
            rn = RequirementNotifyEmail(self.env)
            rn.notify(requirement, newrequirement=True)
        except Exception, e:
            self.log.exception("Failure sending notification on creation of "
                               "requirement <%s %s>: %s" % 
                               (temp_fp['name'], temp_object['name'], e))

        # Redirect the user to the newly created requirement
        req.redirect(req.href.requirement("%s-%s-%s" % 
                                          (requirement.component, 
                                           temp_fp['name'], 
                                           temp_object['name'])))
        req.redirect(req.href.requirements())


class NewrequirementAjaxModule(Component):
    implements(IRequestHandler)

    def match_request(self, req):
        return re.match(r'/newrequirement/ajax/\w+$', req.path_info) is not None

    def process_request(self, req):
        m = re.match(r'/newrequirement/ajax/(\w+)$', req.path_info)
        action = m.group(1)
        
        template = ''

        if(action == 'fp'):
            template = 'ajax_list.cs'
            req.hdf['items'] = Fp(self.env).get_enabled_fps_prefix(req.args.get('fp'))

        elif(action == 'object'):
            template = 'ajax_list.cs'
            req.hdf['items'] = Object(self.env).get_enabled_objects_prefix(req.args.get('object'))

        add_stylesheet(req, 'hw/css/requirement.css')

        return (template, None)
            
class ViewEditDictionaryModule(Component):
    implements(IRequestHandler)


    def match_request(self, req):
        return re.match(r'/editdict/\w+/?$', req.path_info) is not None

    def process_request(self, req):
        m = re.match(r'/editdict/(\w+)/?$', req.path_info)
        action = m.group(1)
        template = "view_edit_dictionary.cs"        

        #decides which page should be displayed based on the uri that
        #was matched by re.match() above.
        if action == "fp":
            self._fphyp_view(req)                
        if action == "admin":
            self._admin_view(req)
        if action == "object":
            self._obj_view(req)

        #exposing the variables that will be needed by all views,
        #regardless of which one was picked for display
        add_stylesheet(req, 'hw/css/dictionary.css')
        req.hdf['editdict.href_admin'] = req.href('editdict', 'admin')
        req.hdf['editdict.href_object'] = req.href('editdict', 'object')
        req.hdf['editdict.href_fp'] = req.href('editdict', 'fp')
        req.hdf['requirement.add_requirement_href'] = req.href.newrequirement()
        req.hdf['trac.href.editdict'] = req.href('editdict', 'fp')
        add_link(req, 'top', req.href('requirements', 'report'))
        return (template, None)

    def _do_create_obj(self, req):
        """Adds an object and its description into the database from the
            data passed from the web user interface.

        Status is enabled by default on an object's creation.
        """
        if req.args.get('newobjname') != '':
            obj = Object(self.env)
            obj['name'] = req.args.get('newobjname')
            obj['description'] = req.args.get('newobjdesc')
            obj.insert()

    def _do_modify_obj(self, req):
        """Modifies an object, its description, and or its status and updates it         database from the data passed from the web user interface.

        """

        obj_dict_str = base64.b64decode(req.args['obj_state_dict'])
        obj_dict = pickle.loads(obj_dict_str)

        checked_obj_names = [name[7:] for name in req.args.keys() if name[:7] ==
"status_"]

        for obj in obj_dict:
            if obj['name'] in checked_obj_names:
                #It was was checked
                if obj['status'] != "enabled":
                    tmp = Object(self.env, name = obj['name'])
                    tmp['status'] = "enabled"
                    tmp.save_changes(req.authname, "Object enabled")
            else:
                #It wasn't checked 
                if obj['status'] == "enabled":
                    tmp = Object(self.env, name = obj['name'])
                    tmp['status'] = "disabled"
                    tmp.save_changes(req.authname, "Object disabled")
                    
    def _do_modify_obj(self, req):
        """Modifies an object, its description, and or its status and updates it         database from the data passed from the web user interface.

        """

        obj_dict_str = base64.b64decode(req.args['obj_state_dict'])
        obj_dict = pickle.loads(obj_dict_str)
        checked_obj_names = [name[7:] for name in req.args.keys() if name[:7] ==
"status_"]
        changed_obj_names = [name[11:] for name in req.args.keys() if name[:11]
=="change_obj_"]
        changed_desc = [name[12:] for name in req.args.keys() if name[:12] == "change_desc_"]
    
        for obj in obj_dict:
            tmp = Object(self.env, name = obj['name'])
            changed = False
            if obj['name'] in checked_obj_names:
                #It was was checked
                if obj['status'] != "enabled":
                    tmp['status'] = "enabled"
                    changed = True
            else:
                #It wasn't checked 
                if obj['status'] == "enabled":
                    tmp['status'] = "disabled"
                    changed = True

            if obj['name'] in changed_desc:
                tmp_desc = req.args['change_desc_' + obj['name']] 
                if tmp_desc != obj['description']:
                    tmp['description'] = \
                    req.args['change_desc_' + obj['name']]
                    changed = True
 
            if obj['name'] in changed_obj_names:
                if req.args['change_obj_' + obj['name']] != "":
                    tmp['name'] = req.args['change_obj_' + obj['name']]
                    changed = True
            if changed:
                tmp.save_changes(req.authname, "Object modified.")

    def _do_modify_fp(self, req):
        """Modifies an object, its description, and or its status and updates it         database from the data passed from the web user interface.

        """

        fp_dict_str = base64.b64decode(req.args['fp_state_dict'])
        fp_list = pickle.loads(fp_dict_str)

        changed_desc = [name[12:] for name in req.args.keys() \
                                  if name[:12] == "change_desc_"]
        changed_hyp_names = [name[11:] for name in req.args.keys() \
                                       if name[:11] == "change_hyp_"]
        changed_fp_names = [name[10:] for name in req.args.keys() \
                                      if name[:10] == "change_fp_"]
        checked_fp_names = [name[10:] for name in req.args.keys() \
                                      if name[:10] =="status_fp_"]
        checked_hyp_names = [name[11:] for name in req.args.keys() \
                                       if name[:11] =="status_hyp_"]
        new_hyp_fps = [name[8:] for name in req.args.keys() \
                                if name[:8] =="new_hyp_"]
        swap_hyp_fps = [name[5:] for name in req.args.keys() \
                                 if name[:5]=="swap_"]

        #Updating Fps that were modified
        for item in fp_list:
            fp_name, status = item['fp']
            tmp = Fp(self.env, name = fp_name)
            changed = False

            if fp_name in changed_desc:
                tmp_desc = req.args['change_desc_' + fp_name] 
                if tmp_desc != item['description']:
                    tmp['description'] = \
                    req.args['change_desc_' + fp_name]
                    changed = True
        
            if fp_name in changed_fp_names \
            and req.args['change_fp_' + fp_name]!= "":
                tmp['name'] = req.args['change_fp_' + fp_name]
                changed = True

            if fp_name in checked_fp_names:
                #Checkbox was was checked
                if status != "enabled":
                    tmp['status'] = "enabled"
                    changed = True
            else:
                #Checkbox wasn't checked
                if status == "enabled":
                    tmp['status'] = "disabled"
                    changed = True

            if changed:
                tmp.save_changes(req.authname, "Fp modified")

        #Updating hyponyms that were modified
        for item in fp_list:
            for hyp_name, status in item['hyponyms']:
                tmp = Hyponym(self.env, name = hyp_name)
                changed = False

                if hyp_name in checked_hyp_names:
                    #Checkbox was was checked
                    if status != "enabled":
                        tmp['status'] = "enabled"
                        changed = True
                else:
                    #Checkbox wasn't checked
                    if status == "enabled":
                        tmp['status'] = "disabled"
                        changed = True

                if req.args['change_hyp_' + hyp_name] != "":
                    if hyp_name in changed_hyp_names: 
                        tmp['name'] = req.args['change_hyp_' + hyp_name]
                        changed = True 
                if changed:
                    tmp.save_changes(req.authname, "Hyponym Modified")

        for fp_name in new_hyp_fps: 
            hyps = req.args.get('new_hyp_' + fp_name).split(',')
            for hyponym in hyps:
                if hyponym != "":
                    try:
                        # If the point of this try statement confuses you,
                        # scroll down to see the next fatty comment block,
                        # or search this file for the word 'duplicate'
                        newhyp = Hyponym(self.env)
                        newhyp['name'] = str(hyponym)
                        newhyp.values['fp'] = Fp(self.env, name=fp_name)['id']
                        newhyp.insert()
                    except TracError:
                        pass

        for item in swap_hyp_fps:
            if req.args['swap_' + item] != 'hyponym':
                temp = Hyponym(self.env, name=req.args['swap_' + item])
                temp.swap_with_fp(req.authname, "Swapped Fp with Hyponym")

    def _do_create_fp(self, req):
        """Adds a fp, its description, and hyponyms into the database.

        """
        if req.args.get('newfp') != '':
            fp = Fp(self.env)
            fp['name'] = req.args.get('newfp')
            fp['description'] = req.args.get('newfpdesc')
            fp.insert()
           
         
            hyps = req.args.get('newfphyps').split(',')
            for hyponym in hyps:
                if hyponym != "":
                    try:
                        # The only reason that inserting a hyponym
                        # would fail here is if one already existed in the db.
                        # By putting it in a try block and doing nothing 
                        # when we catch an error, we basically ignore any
                        # duplicate hyponyms the user enters. This is good
                        # because it makes sure all the non-duplicaties are
                        # added, quietly ignoring the duplicates (instead of
                        # erroring out on a duplicate and failing to add the
                        # rest of the hyponyms after the error).

                        newhyp = Hyponym(self.env)
                        newhyp['name'] = str(hyponym)
                        newhyp.values['fp'] = fp['id']
                        newhyp.insert()
                    except TracError:
                
                        pass

    def _fphyp_view(self, req):
        """Gathers and exposes the necessary variables to view the 
        fps and hyponyms.
        """
        
        if req.method == 'POST' and 'submit_new_fp' in req.args:
            self._do_create_fp(req)
        if req.method == 'POST' and 'submit_mod_fphyp' in req.args:
            self._do_modify_fp(req)
        
        fp_dict = Fp(self.env).get_fp_hyp_info()
        if fp_dict != []:
            req.hdf['editdict.empty'] = 1
        fp_dict_str = pickle.dumps(fp_dict)
        fp_dict_str = base64.b64encode(fp_dict_str)

        req.hdf['editdict.values'] = fp_dict
        req.hdf['editdict.show'] = "fphyps"
        req.hdf['fp_dict.encoded'] = fp_dict_str

    def _admin_view(self, req):

        req.hdf['editdict.show'] = "admin"

        fp_enabled =  Fp(self.env).check_on_fly_fp()
        object_enabled = Object(self.env).check_on_fly_obj()

        if req.method == 'POST':
            if 'fp_on_fly_enable' in req.args:
                Fp(self.env).set_on_fly_fp('enabled')
            else:
                Fp(self.env).set_on_fly_fp('disabled')
            if 'object_on_fly_enable' in req.args:
                Object(self.env).set_on_fly_obj('enabled')
            else:
                Object(self.env).set_on_fly_obj('disabled')

        req.hdf['fp_enabled'] = Fp(self.env).check_on_fly_fp()
        req.hdf['object_enabled'] = Object(self.env).check_on_fly_obj()

    def _obj_view(self, req):
        
        if req.method == 'POST' and 'submit_new_obj' in req.args:
            self._do_create_obj(req)
        if req.method == 'POST' and 'submit_mod_obj' in req.args:
            self._do_modify_obj(req)
        
        obj_dict = Object(self.env).get_obj_info()
        if obj_dict != []: req.hdf['editdict.empty'] = 1
        obj_dict_str = pickle.dumps(obj_dict)
        obj_dict_str = base64.b64encode(obj_dict_str)

        req.hdf['editdict.show'] = "object" 
        req.hdf['editdict.values'] = obj_dict
        req.hdf['obj_dict.encoded'] = obj_dict_str


class DashboardModule(Component):
    implements(IRequestHandler)

    def match_request(self, req):
        return re.match(r'/requirements/?$', req.path_info) is not None
    
    def process_request(self, req):
        template = 'dashboard.cs'
        add_stylesheet(req, 'hw/css/dashboard.css')

        reports = [('Requirements by Component', 'report/1'), 
                       ('Requirements with Associated Tickets', 'report/5'),
                       ('Most/least Changed Requirements','view/3' ),
                       ('Requirements by Milestone', 'report/7'),
                       ('Disabled Requirements by Component', 'report/8')]

        req.hdf['report_href'] = req.href('requirements', 'report')
        req.hdf['rlist'] = reports
        req.hdf['requirement_href'] = req.href.requirements()

        #Valdation Dashboard Module Data
        tmpreq = Requirement(self.env)
        val_time = tmpreq.get_most_recent_validation()
        if val_time != None:
            req.hdf['recent_val_date'] = format_datetime(val_time)
        else:
            req.hdf['recent_val_date'] = 1
        req.hdf['current_val'] = tmpreq.get_current_reqs_validated()
        req.hdf['show_val_report'] = tmpreq.get_changed_reqs_since_validation()
        req.hdf['req_ood_href'] = req.href('requirements', 'report', '11')
        req.hdf['req_changed_href'] = req.href.requirements('report', '12')
    
        #dashboard header links
        req.hdf['editdict.href_fp'] = req.href('editdict', 'fp')
        req.hdf['requirement.add_requirement_href'] = req.href.newrequirement()
        req.hdf['trac.href.editdict'] = req.href('editdict', 'fp')

        #dashboard graph links
        req.hdf['graph_path'] = req.href.requirements() + '/graph'

        add_link(req, 'top', req.href('requirements', 'report'))
        return (template, None)

