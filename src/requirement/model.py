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

import time
from api import RequirementSystem 
from api import ObjectSystem
from api import FpSystem
from api import HyponymSystem
from trac.core import TracError

class ReqBase(object):
    """Class representing the base requirement plugin model functionality.

    The purpose of this class it to act as a base model for the
    models in the requirement plugin.
    """

    def __init__(self, env, db=None):
        self.env = env
        self.db = db

    def _get_db_for_write(self, db=None):
        if db:
            return (db, False)
        else:
            return (self.env.get_db_cnx(), True)

    def _get_db(self, db=None):
        return db or self.env.get_db_cnx()

class Requirement(ReqBase):

    def __init__(self, env, component=None, fp=None, object=None, db=None):
        """Initialize a requirement.

        Component is passed as a string, while fp and object are
        id numbers for entries in their respective tables. For
        creation of new requirements component,fp,and object should
        NOT be passed, allowing an empty requirement instance to be
        created, populated with appropriate values, and inserted into
        the data base. To view/edit an existing requirement, then
        component,fp, and object MUST be passed, so the appropriate
        requirement can be found in the database.

        """
        ReqBase.__init__(self, env, db)
        self.cache = DataCache(env, db)
        
        # Fill the fields member variable with a list of dictionaries that
        # describe each of the fields and initialize the values member
        # dictionary to an empty state.
        self.fields = RequirementSystem(self.env).get_requirement_fields()
        self.values = {}
        
        if component is not None and fp is not None and object is not None:
            # If I was given a component, fp, and object then I have a
            # triplet that uniquely identifies a Requirement and I want to
            # initialize this object to the values from the database
            # associated with that unique triplet. Note: The
            # _fetch_requirement() function also sets self.component,
            # self.fp, self.object, self.time_created, and the
            # self.time_changed member variables based on the data in the
            # database. These member variables are solely used as a quick
            # reference to their matching self.values entries.
            self._fetch_requirement(component, fp, object, db)
            
        else:
            # If I was NOT given the component, fp, and object triplet then
            # I initialize the object to the proper default values.
            self._init_defaults(db)
            
            # Note: I initially thought that trac's reasoning for having
            # these variables which duplicate the self.values entries was
            # to maintain copies of the initial table values, or possibly to
            # contain only the db commited values. However, after great
            # analysis both these thoughts were debunked and I came to the
            # conclusion that these member variables are used solely as a
            # mechanism for quick reference rather than having to use the
            # self.values['foo'] mechanism. This does require duplicate
            # modifications in some places, however I decided that it was
            # best to follow trac's conventions and implement the Requirement
            # model in the same fashion as trac's Ticket model.
            self.component = None
            self.fp = None
            self.object = None
            self.time_created = None
            self.time_changed = None
        
        self._old = {}
        
    exists = property(fget=lambda self: \
                      self.component is not None \
                      and self.fp is not None \
                      and self.object is not None)

    def _init_defaults(self, db=None):
        for field in self.fields:
            default = None
            
            # If field is NOT a custom field then check the config file
            # for any default values for the specific field.
            if not field.get('custom'):
                default = self.env.config.get('requirement',
                                              'default_' + field['name'])
            # If field IS a custom field then set the default values and
            # options appropriately.
            else:
                default = field.get('value')
                options = field.get('options')
                if default and options and default not in options:
                    try:
                        default = options[int(default)]
                    except (ValueError, IndexError):
                        self.env.log.warning('Invalid default value "%s" '
                                             'for custom field "%s"'
                                             % (default, field['name']))
            if default:
                self.values.setdefault(field['name'], default)

    def _fetch_requirement(self, component, fp, object, db=None):
        db = self._get_db(db)

        std_fields = [f['name'] for f in self.fields if not f.get('custom')]
        cursor = db.cursor()
        cursor.execute("SELECT %s,time,changetime FROM requirement "
                       "WHERE component = %%s AND fp = %%s AND object = %%s"
                       % ','.join(std_fields), 
                        (component, fp, object))
        row = cursor.fetchone()
        if not row:
            raise TracError('Requirement <%s %s %s>  does not exist.'
                            % (component, Fp(self.env,id=fp)['name'], 
                            Object(self.env, id=object)['name']), 
                            'Invalid Requirement')
        
        self.component = component
        self.fp = fp
        self.object = object
        
        for i in range(len(std_fields)):
            self.values[std_fields[i]] = row[i] or ''
        self.time_created = row[len(std_fields)]
        self.time_changed = row[len(std_fields) + 1]
        
        # Fetch custom fields if available
        custom_fields = [f['name'] for f in self.fields if f.get('custom')]
        cursor.execute("SELECT name,value FROM requirement_custom "
                       "WHERE component = %s AND fp = %s AND object = %s",
                       (component, fp, object))
        for name, value in cursor:
            if name in custom_fields:
                self.values[name] = value
                
    
    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):
        """Log requirement modifications so the table requirement_change can be updated"""
        if self.values.has_key(name) and self.values[name] == value:
            return
            
        if not self._old.has_key(name): # Changed field
            self._old[name] = self.values.get(name)
        elif self._old[name] == value: # Change of field reverted
            del self._old[name]
            
        if value:
            # The below is equiv to the following:
            # tmp = []
            # for field in self.fields:
            #     if field['name'] == name:
            #         tmp.append(field)
            # field = tmp
            field = [field for field in self.fields if field['name'] == name]                    
            
            if field and field[0].get('type') != 'textarea':
                if field[0].get('name') != 'fp' and \
                   field[0].get('name') != 'object':
                    value = value.strip()
                
        self.values[name] = value
        
    def populate(self, values):
        """Populate the requirement with 'suitable' values from a dictionary"""
        field_names = [f['name'] for f in self.fields]
        for name in [name for name in values.keys() if name in field_names]:
            self[name] = values.get(name, '')

        # We have to do an extra trick to catch unchecked checkboxes
        for name in [name for name in values.keys() if name[9:] in field_names
                     and name.startswith('checkbox_')]:
            if not values.has_key(name[9:]):
                self[name[9:]] = '0'

    def insert(self, when=0, db=None):
        """Add requirement to database"""
        assert not self.exists, 'Cannot insert an existing requirement'
        db, handle_ra = self._get_db_for_write(db)
        
        # Add a timestamp
        if not when:
            when = time.time()
        when = int(when)
        self.time_created = self.time_changed = when

        cursor = db.cursor()
        
        cursor.execute("SELECT 'a' FROM requirement " 
                       "WHERE component=%s AND fp=%s AND object=%s", 
                       (self.values['component'], self.values['fp'], 
                        self.values['object']))
        row = cursor.fetchone()
        if row: 
            self._fetch_requirement(self.values['component'], self.values['fp'], self.values['object'])
            raise TracError('Requirement <%s %s %s> already exists.' 
                            % (self.component, Fp(self.env,id=self.fp)['name'],
                              Object(self.env, id=self.object)['name']), 
                               'Existant Requirement')
       
        self['status'] = 'enabled'
        self._check_ok_to_enable()

        # Insert requirement record
        std_fields = [f['name'] for f in self.fields if not f.get('custom')
                      and self.values.has_key(f['name'])]
        cursor.execute("INSERT INTO requirement (%s,time,changetime) VALUES (%s)"
                       % (','.join(std_fields),
                          ','.join(['%s'] * (len(std_fields) + 2))),
                          [self[name] for name in std_fields] +
                          [self.time_created, self.time_changed])
        
        self.component = self['component']
        self.fp = self['fp']
        self.object = self['object']
        
        # Insert custom fields
        custom_fields = [f['name'] for f in self.fields if f.get('custom')
                         and self.values.has_key(f['name'])]
        if custom_fields:
            cursor.executemany("INSERT INTO requirement_custom (component,fp,object,name,value) "
                               "VALUES (%s,%s,%s,%s,%s)",
                               [(self.component, self.fp, self.object, name, self[name])
                                for name in custom_fields])
            
        if handle_ra:
            db.commit()
            
        self._old = {}

        # clear cached data affected by this
        self.cache.clean_data(self.component, self.fp, self.object)
        
        for listener in RequirementSystem(self.env).change_listeners:
            listener.requirement_created(self)
            
        if self.component is not None and self.fp is not None and self.object is not None:
            return True
        else:
            return False

    def save_changes(self, author, comment, when=0, db=None, cnum=''):
        """
        Store requirement changes in the database. The requirement must 
        already exist in the database. Returns False if there were no 
        changes to save, True otherwise.
        """
        
        assert self.exists, 'Cannot update a new requirement'
       
        if not self._old and not comment:
            return False # Not modified
        
        db, handle_ra = self._get_db_for_write(db)
        cursor = db.cursor()
        when = int(when or time.time())
        
        # Fix up cc list separators and remove duplicates 
        if self.values.has_key('cc'):
            cclist = []
            for cc in re.split(r'[;,\s]+', self.values['cc']):
                if cc not in cclist:
                    cclist.append(cc)
            self.values['cc'] = ', '.join(cclist)

        self._check_ok_to_enable()

        custom_fields = [f['name'] for f in self.fields if f.get('custom')]
        for name in self._old.keys():
            if name in custom_fields:
                cursor.execute("SELECT * FROM requirement_custom " 
                               "WHERE component=%s AND fp=%s AND object=%s AND name=%s",
                               (self.component, self.fp, self.object, name))
                if cursor.fetchone():
                    cursor.execute("UPDATE requirement_custom SET value=%s "
                                   "WHERE component=%s AND fp=%s AND object=%s AND name=%s",
                                   (self[name], self.component, self.fp, self.object, name))
                else:
                    cursor.execute("INSERT INTO requirement_custom (component,fp,object,name,"
                                   "value) VALUES(%s,%s,%s,%s,%s)",
                                   (self.component, self.fp, self.object, name, self[name]))
            else:
                cursor.execute("UPDATE requirement SET %s=%%s "
                               "WHERE component=%%s AND fp=%%s AND object=%%s" % name,
                                (self[name], self.component, self.fp, self.object))
            cursor.execute("INSERT INTO requirement_change "
                           "(component,fp,object,time,author,field,oldvalue,newvalue) "
                           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (self.component, self.fp, self.object, when, author, name, self._old[name],
                            self[name]))
        # always save comment, even if empty (numbering support for timeline)
        cursor.execute("INSERT INTO requirement_change "
                       "(component,fp,object,time,author,field,oldvalue,newvalue) "
                       "VALUES (%s,%s,%s,%s,%s,'comment',%s,%s)",
                       (self.component, self.fp, self.object, when, author, cnum, comment))

        cursor.execute("UPDATE requirement SET changetime=%s "
                       "WHERE component=%s AND fp=%s AND object=%s",
                       (when, self.component, self.fp, self.object))
        
        if handle_ra:
            db.commit()

        # clear cached data affected by this
        self.cache.clean_data(self.component, self.fp, self.object)

        if self._old.has_key('status') and self._old['status'] == 'disabled' and self['status'] == 'enabled':
            for listener in RequirementSystem(self.env).change_listeners:
                listener.requirement_enabled(self, comment, author)

        elif self._old.has_key('status') and self._old['status'] == 'enabled' and self['status'] == 'disabled':
            for listener in RequirementSystem(self.env).change_listeners:
                listener.requirement_disabled(self, comment, author)

        else:
            for listener in RequirementSystem(self.env).change_listeners:
                listener.requirement_changed(self, comment, author, self._old)

        self._old = {}
        self.time_changed = when

        return True

    def _check_ok_to_enable(self):
        """Make sure that it is ok to enable a requirement.

        Anytime that a requirement changes its status to enabled
        we check to make sure that it has a valid fp and object 
        before enabling. If it doesn't, we set it to out-of-date.
        """
        cursor = self._get_db().cursor()
        cursor.execute("SELECT fp.status, o.status "
                       "FROM fp, object o " 
                       "WHERE fp.id = %s AND o.id = %s",
                       (self['fp'], self['object']))
        row = cursor.fetchone()
        if not row:
             return
        
        if (self.values.has_key('status') and self['status'] == 'enabled'
            and (row[0] == 'disabled' or row[1] =='disabled')):
                self['status'] = 'out-of-date'
                #del self._old['status']

    def get_changelog(self, when=0, db=None):
        """Return the changelog as a list of tuples of the form
        (time, author, field, oldvalue, newvalue, permanent).
        """
        
        when = int(when)
        db = self._get_db(db)
        cursor = db.cursor()
        if when:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM requirement_change "
                           "WHERE component=%s AND fp=%s AND object=%s AND time=%s "
                           (self.component, self.fp, self.object, when))
        else:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM requirement_change "
                           "WHERE component=%s AND fp=%s AND object=%s "
                           "ORDER BY time", (self.component, self.fp, self.object))
        log = []
        for t, author, field, oldvalue, newvalue in cursor:
            log.append((int(t), author, field, oldvalue or '', newvalue or ''))

        return log
        
    def get_components(self, db=None):
        """Return a list of components
        Return a list of current components from the database
        """

        db = self._get_db(db)
        cursor = db.cursor()
        components = []
        cursor.execute("SELECT name FROM component ORDER BY name")
        for com in cursor:
            components.append(com[0])
        return components
       
    def get_fps(self, db=None, timestamp=None, dict=False):
        """Return a list of fps

        If dict == False (default), then returns a list of fp ids that 
        were in an enabled stated during the timestamp given. 

        If dict == True, then returns a dictionary like {'id':'name'}
        that includes all of the ids as keys, and has their name at the
        time given as the value. It's a little hacky, but useful.
        """

        if timestamp:
            when = timestamp
        else:
            when = time.time()
        
        db = self._get_db(db)
        cursor1 = db.cursor()
        cursor2 = db.cursor()
        fps = []
        fp_dict = {}    
        cursor1.execute("SELECT id, name, changetime, status FROM fp WHERE time<=%s ORDER BY name", (when,))
        for fp in cursor1:
            # if timestamp is given and it comes before the last changetime
            if timestamp and (timestamp < fp[2]):
                # unroll changes from latest to oldest
                cursor2.execute("SELECT field, oldvalue FROM fp_change WHERE id=%s AND time>%s ORDER BY time DESC", (fp[0], timestamp))
                for change in cursor2:
                    # at this point we only care about name and status changes
                    if change[0]=='name':
                        fp[1] = change[1]
                    elif change[0]=='status':
                        fp[3] = change[1]
            
            # only return if enabled
            #if fp[3]=='enabled':
            fps.append(fp[0])
            fp_dict[fp[0]] = fp[1]
        if dict == True:
            return fp_dict
        else:
            return fps

    def get_fps_prefix(self, prefix='', db=None):
        """

        """

        db = self._get_db(db)
        cursor = db.cursor()
        items = []

        cursor.execute("SELECT name FROM fp "
                       "WHERE name LIKE '%s%%' ORDER BY name" % (prefix,))
        for fp in cursor:
            items.append((fp[0],'(FP)'))

        cursor.execute("SELECT h.name,fp.name FROM hyponym h, fp "
                       "WHERE h.name LIKE '%s%%' AND h.fp = fp.id "
                       "ORDER BY fp.name" % (prefix,))
        for hyp in cursor:
            items.append((hyp[1],'(H: '+hyp[0]+')'))

        return items
    
 
    def get_milestones(self, db=None):
        """Obtain a list all milestones.
        
        Obtain a list of milestones represented as tuples in the form
        (name, due) where name is the name of the milestone and due is the
        due date in seconds since epoch. Note: The due date is set to a value
        0 if the due date is not set for a given milestone.
        """
        db = self._get_db(db)
        cursor = db.cursor()
        
        milestones = []
        
        cursor.execute("SELECT name, due FROM milestone ORDER BY due")
        for milestone in cursor:
            milestones.append((milestone[0], milestone[1]))
            
        return milestones
            
    def get_components_metrics(self, db=None, timestamp=None):
        """Get stats on components
        This function returns a tuple of lists containing
        the names of the components which have requirements
        associated to them.  It also returns the number of 
        requirements associated to each component.
        """

        if not timestamp:
            timestamp = time.time()
        
        db = self._get_db(db)
        cursor = db.cursor()
        
        components = []
        component_counts = {}
        
        cursor.execute("SELECT name, COUNT(requirement.component) "
                       "FROM component, requirement "
                       "WHERE requirement.component=component.name "
                       "AND requirement.time <= %s "
                       "GROUP BY name", (timestamp,))
        for component, count in cursor:
            components.append(component)
            component_counts[component] = count
            
        return components, component_counts


    def get_fp_metrics(self, db=None, timestamp=None):
        """Get stats on functional primatives
        This function returns a tuple of lists containing
        the names of functional primatives, objects and
        the number of objects associated to them.
        """

        if not timestamp:
            timestamp = time.time()
        
        db = self._get_db(db)
        cursor = db.cursor()
        
        fps = []
        fp_objects = {}
        fp_counts = {}
        
        cursor.execute("SELECT r.fp, r.object, COUNT(r.object) "
                       "FROM requirement r, fp, object "
                       "WHERE r.fp = fp.id "
                       "AND r.object = object.id "
                       "AND r.time <= %s "
                       "GROUP BY r.fp, r.object "
                       "ORDER BY fp.name, object.name", (timestamp,))
        for fp, object, count in cursor:
            if fp not in fps:
                fps.append(fp)
            if fp not in fp_objects:
                fp_objects[fp] = {}
            fp_objects[fp][object] = count
            if fp not in fp_counts:
                fp_counts[fp] = 0
            fp_counts[fp] += count

        return fps, fp_objects, fp_counts

    def get_objects_prefix(self, prefix='', db=None):
        """Return a list of objects matching the prefix"""

        db = self._get_db(db)
        cursor = db.cursor()
        objects = []
        cursor.execute("SELECT name FROM object "
                       "WHERE name LIKE '%s%%' ORDER BY name" % (prefix,))
        for obj in cursor:
            objects.append((obj[0],''))
        return objects
    
    
    def get_object_metrics(self, db=None, timestamp=None):
        if not timestamp:
            timestamp = time.time()

        db = self._get_db(db)
        cursor = db.cursor()

        objects = []
        object_fps = {}
        object_counts = {}
        
        cursor.execute("SELECT r.object, r.fp, COUNT(fp) "
                       "FROM object, fp, requirement r "
                       "WHERE r.object=object.id "
                       "AND r.fp = fp.id "
                       "AND r.time <= %s "
                       "GROUP BY r.object, r.fp "
                       "ORDER BY object.name", (timestamp,))
        for object, fp, count in cursor:
            if object not in objects:
                objects.append(object)
            if object not in object_fps:
                object_fps[object] = {}
            object_fps[object][fp] = count
            if object not in object_counts:
                object_counts[object] = 0
            object_counts[object] += count

        return objects, object_fps, object_counts

    def get_changes_metrics(self, db=None):
        """Get metrics on changes to the requirement.
        
        This function obtains the creation time of requirement and all the
        timestamps of when then the requirement has been modified. This info
        is returned as a tuple of the form (time_created, times_changed)
        where times_changed is a ordered list of times that the requirement
        was changed/modified.
        """
        if not db:
            db = self._get_db(db)
        
        cursor = db.cursor()
        
        time = None
        cursor.execute("SELECT time FROM requirement WHERE component=%s AND fp=%s AND object=%s", (self.component, self.fp, self.object))
        for requirement in cursor:
            time = requirement[0]
        
        change_times = []
        cursor.execute("SELECT time FROM requirement_change WHERE component=%s AND fp=%s AND object=%s ORDER BY time ASC", (self.component, self.fp, self.object))
        for requirement_change in cursor:
            change_times.append(requirement_change[0])
            
        return (time, change_times)

    def get_tickets_over_time_metrics(self, when, db=None):
        """Get metrics on tickets to the requirement.
        
        This function obtains the number of active ticket types
        associated with the requirement preceding a given date and returns a 
        list of types and the count of each type.
        The information is returned as a list of tuples of the form
        (type, count).
        """
        db = self._get_db(db)

        cursor1 = db.cursor()
        cursor2 = db.cursor()

        ticket_info = []

        # retrieve the current set of ticket types being used:
        cursor1.execute("SELECT name "
                        "FROM enum "
                        "WHERE type = 'ticket_type' "
                        "ORDER BY name DESC")
        for ticket_type in cursor1:
            type = ticket_type[0]

            # note that the following query incluedes tickets that are now
            #  closed but were open still at the time of question or were 
            #  closed but later re-opened for additional work
            cursor2.execute("SELECT r.component, fp.name, o.name, count(*) "
                            "FROM fp, object o, requirement r " 
                            "LEFT JOIN requirement_ticket_cache rtc "
                            "LEFT JOIN ticket t "
                            "WHERE ( fp.id = r.fp) "
                            "AND (o.id = r.object)"
                            "AND ( "
                                  "r.component = rtc.component AND "
                                  "fp.name = rtc.fp AND "
                                  "o.name = rtc.object "
                                ") "
                            "AND (t.id = rtc.ticket) "
                            "AND (t.type=%s) "
                            "AND (t.time < %s) "
                            "AND ((t.status NOT IN ('closed')) "
                            "OR (t.id = (SELECT DISTINCT tkt.id "
                                         "FROM ticket tkt, "
                                         "ticket_change tkt_c "
                                         "WHERE (t.id = tkt.id) "
                                         "AND (tkt.id = tkt_c.ticket) "
                                         "AND (tkt_c.field = 'status') "
                                         "AND (tkt_c.newvalue = 'closed') "
                                         "AND (tkt_c.time > %s ) "
                                       ") "
                               ") " # closed but open at time=when
                             ") "
                            "AND ( "
                                  "r.component=%s AND "
                                  "r.fp=%s AND "
                                  "r.object=%s "
                                ")", 
                            (type, when, when, self.component, self.fp, \
                                self.object))

            for field in cursor2:
                count = field[3]
            ticket_info.append((type, count))

        return ticket_info

    def get_requirements(self, db=None, timestamp=None):
        # TODO: switch to use ID's once req is updated to ID's 
        if not timestamp:
            timestamp = time.time()
        db = self._get_db(db)
        cursor = db.cursor()
        cursor.execute("SELECT component, fp, object FROM requirement WHERE status='enabled' AND time <= %s ORDER BY component", (timestamp, ))
        cur_component = ''
        component_groups = []
        for requirement in cursor:
            component = requirement[0]
            if cur_component != component:
                cur_component = component
                component_groups.append( [ component, [] ] )
            component_groups[ len( component_groups ) - 1 ][1].append( [ requirement[1], requirement[2] ] )
        return component_groups

    def get_num_changes(self, start, stop):
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT('a') "
                       "  FROM requirement_change rc "
                       "    INNER JOIN requirement r "
                       "      ON r.component = rc.component AND r.fp = rc.fp AND r.object = rc.object "
                       "      AND rc.time>=%s AND rc.time<=%s "
                       "ORDER BY rc.time"
                       % (start, stop))
        row=cursor.fetchone()
        return row[0]

    def get_num_req(self, timestamp):
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("SELECT sum(a) FROM "
                       "(SELECT count(*) AS 'a' FROM requirement "
                       " WHERE time < %s "
                       " UNION ALL " 
                       " SELECT -count(*) AS 'a' FROM "
                       "        (SELECT newvalue AS 'stat', max(time) "
                       "         FROM requirement_change "
                       "         WHERE field='status' AND time<%s "
                       "         GROUP BY component, fp, object) "
                       " WHERE stat='disabled')",(timestamp,timestamp))
        row=cursor.fetchone()
        return row[0]

    def get_val_times(self):
        """
        Returns all the times validation of requirments occurs
        as a list
        """
        db = self._get_db()
        cursor = db.cursor()
        valTimes = []
        cursor.execute("SELECT date "
                       "FROM requirement_validation " 
                       "ORDER BY date ASC")

        for aggregate_result in cursor:
            valTimes.append(aggregate_result[0])
    
        return valTimes

    def get_requirements_matrix(self, predicate=None, db=None, timestamp=None):
        matrix = {}

        db = self._get_db(db)
        cursor = db.cursor()

        # For each fp (rows)
        for fp in self.get_fps(None, timestamp):
            matrix[fp] = {}

            # For each obj (cols)
            for obj in Object(self.env).get_objects(None, timestamp):
                cursor.execute("SELECT COUNT(*) FROM requirement "
                               "WHERE fp=%s AND object=%s", (fp, obj))

                for count in cursor:
                    matrix[fp][obj] = count[0]

        return matrix

    def get_requirements_matrix_rowsum(self, matrix, fp):
        sum = 0
        for obj in matrix[fp]:
            sum += matrix[fp][obj]

        return sum

    def get_requirements_matrix_colsum(self, matrix, obj):
        sum = 0
        for fp in matrix:
            sum += matrix[fp][obj]

        return sum

    def get_requirements_count(self, matrix, db=None):
        sum = 0
        for fp in matrix:
            for obj in matrix[fp]:
                sum += matrix[fp][obj]

        return sum

    def get_pairings(self, predicate=None, db=None, timestamp=None):
        if not timestamp:
            timestamp = time.time()
        pairings = []
        db = self._get_db(db)
        cursor = db.cursor()
        cursor.execute("SELECT DISTINCT r.fp, r.object " 
                       "FROM requirement r, fp, object "
                       "WHERE r.time <= %s "
                       "AND fp.id = r.fp "
                       "AND object.id = r.object "
                       "ORDER BY fp.name, object.name", (timestamp,))
        for pair in cursor:
            pairings.append(pair)

        return pairings

    
 
    def validate_requirements(self, db=None):
        """ Validate the current set of existing requirements
        
        This function validates the current set of enabled requirements.
        This is only if there are no out of date requirements.
 
        The function must be called to validate all the requirements in
        the set if any of them have been altered since the previous
        validation.  Any change to a requirement after the date of
        validation will cause the entire set of requirements to become
        invalid.  The function returns True for a successful commit and
        False if there were difficulties.
        """ 
        out_of_date_status,_ = self.get_changed_reqs_since_validation()
        if out_of_date_status == 0:
            db, handle_ra = self._get_db_for_write(db)
            cursor = db.cursor()
            when = now = int(time.time())

            # Here we only save the date; any change to a requirement after this
            #  date will cause the entire set of current requirements to become
            #  invalid.  To validate them all again, call this routine.
            #   NOTE TO DEVELOPERS: THE SECOND FIELD IS USELESS AND CAN BE REMOVED.
            #    PLEASE SEE TICKET #125
            cursor.execute("INSERT INTO requirement_validation "
                           "(date, uid) "
                           "VALUES (%s,'santa')", (when,))

            if handle_ra:
                db.commit()
                return True
            else:
                return False
        else:
            return False
    def get_current_reqs_validated(self, db=None):
        """ Determines whether the current set of enabled requirements
        have been validated or not.

        Returns a 0 value if the current set is out of date and a 1
        value if it is current and validated.
        """

        db = self._get_db(db)

        cursor = db.cursor()

        cursor.execute("SELECT max(time) "
                       "FROM requirement ")

        for aggregate_result in cursor:
            most_recent_creation = aggregate_result[0]

        cursor.execute("SELECT max(changetime) "
                       "FROM requirement ")

        for aggregate_result in cursor:
            most_recent_change = aggregate_result[0]

        cursor.execute("SELECT max(date) "
                       "FROM requirement_validation")

        for aggregate_result in cursor:
            most_recent_validation = aggregate_result[0]

        if (most_recent_validation == None):
            return 0

        if (most_recent_creation < most_recent_validation):
            if (most_recent_change < most_recent_validation):
                return 1
        return 0

    def get_changed_reqs_since_validation(self, db=None):
        """This function returns a tuple. The first element is 0 if 
        there are no requirements with a status 'out-of-date', 1 if there
        are. The second element is 0 if there were no requirements changed
        since last validation, 1 if there were.
        """
        
        db = self._get_db(db)
        cursor = db.cursor()

        cursor.execute("SELECT r.component, fp.name, o.name "
        "FROM requirement r, fp, object o "
        "WHERE r.status = 'out-of-date' "
        "AND r.fp = fp.id "
        "AND o.id = r.object ")
        
        if not cursor.fetchone():
            #No requirements currently have a status of out-of-date
            ood_empty = 0
        else:
            #there are requirements with a status of out-of-date
            ood_empty = 1

        cursor.execute("SELECT r.changetime "
               "FROM requirement r "
               "WHERE r.changetime > (SELECT max(date) "
                                     "FROM requirement_validation) ")

        if not cursor.fetchone():
            #No requirements have been changed since the last validation
            changed = 0
        else: 
            #There are requirements that have changed since validation
            changed = 1 

        return (ood_empty, changed)
        
    def get_most_recent_validation(self, db=None):
        """ Returns the latest validation date.
        """

        db = self._get_db(db)

        cursor = db.cursor()

        cursor.execute("SELECT max(date) "
                       "FROM requirement_validation")

        for aggregate_result in cursor:
            most_recent_validation = aggregate_result[0]

        return most_recent_validation

    def get_timestamp_first_entity( self, db=None ):
        """This function looks for the smallest
        number in ticket.time, wiki.time, revision.time
        and requirement.time and then looks for the 
        smallest out of those to gauge when the project
        was created by finding the oldest timestamp 
        in the system.  Such is useful for graphs based
        on time used throught the requirement system.
        """

        db = self._get_db(db)
        query = """
        SELECT MIN( timestamp )
        FROM
        (
            SELECT MIN( time ) AS timestamp
                FROM ticket
            UNION
            SELECT MIN( time ) AS timestamp
                FROM wiki
            UNION
            SELECT MIN( time ) AS timestamp
                FROM requirement
            UNION
            SELECT MIN( time ) AS timestamp
                FROM revision
        )
        """

        cursor = db.cursor()
        cursor.execute( query )

        return cursor.fetchone()[0]

    def get_timestamp_latest_req_reqchange_milestone( self, db=None ):
        """This function looks for the largest
        number in milestone.due, requirement.time
        and requirement_change.time and then looks for the 
        largest out of those to determine the most recently created
        or modified for use in graphs.
        """

        db = self._get_db(db)
        query = """
        SELECT MAX( timestamp )
        FROM
        (
            SELECT MAX( due ) AS timestamp
                FROM milestone
            UNION
            SELECT MAX( time ) AS timestamp
                FROM requirement
            UNION
            SELECT MAX( time ) AS timestamp
                FROM requirement_change
        )
        """

        cursor = db.cursor()
        cursor.execute( query )

        return cursor.fetchone()[0]        

    def get_component_req_count(self, db=None):
        """Get the number of requirements each component has.

        This function counts the number of requirements associated
        with each component. It also formats the name of the components
        into labels of the same size. 

        Returns a list of tuples. Each tuple has a component's label,
        followed by the number of associated requirements. If no 
        requirements associated returns label and number 0. If no 
        components, returns empty list [].
        """

        db = self._get_db(db)
        cursor = db.cursor()
        comp_name = []
        req_count = []
        

        cursor.execute("SELECT c.name, count(r.component) "
                       "FROM component c LEFT JOIN requirement r "
                       "ON c.name = r.component GROUP BY c.name "
                       "ORDER BY c.name")

        for row in cursor:
                comp_name.append(row[0])
                req_count.append(row[1])

        label_size = len(max(comp_name)) + 1
        for i in range(len(comp_name)):
            spaces = " "*(label_size - len(comp_name[i])) 
            comp_name[i] = spaces + comp_name[i]

        return [(comp_name[i], req_count[i]) for i in range(len(comp_name))]
        
    def get_type_req_tickets(self, db=None):
        """
        This function gets the number or requirements that have tickets open,
        the number of requirements that have all tickets closed, and
        the number of requirements that have no tickets associated with them.

        Returns a list of integers described in the above order.
        """

        db = self._get_db(db)
        cursor = db.cursor()
        
        cursor.execute("SELECT count(req) FROM "
            "(SELECT distinct r.component || fp.name || o.name AS 'req',"
            " rtc.component || rtc.fp || rtc.object AS 'ticketreq' "
            "FROM requirement r, fp, object o, requirement_ticket_cache rtc, "
            "ticket WHERE rtc.ticket=ticket.id AND ticket.status <> 'closed' "
	    "AND r.fp = fp.id AND r.object = o.id AND r.component = rtc.component "
	    "AND r.status <> 'disabled') "
            "WHERE req = ticketreq")

        tick_open = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(a) FROM "
            "(SELECT COUNT(*) AS 'a' FROM (SELECT DISTINCT r.component "
            "|| fp.name || o.name AS 'req' FROM requirement r, fp, object o "
            "WHERE r.fp = fp.id AND r.object = o.id AND r.status <> 'disabled') "
	    "UNION ALL "
            "SELECT -count(*) AS 'a' FROM (SELECT DISTINCT rtc.component "
            "|| rtc.fp || rtc.object FROM requirement_ticket_cache rtc))")
        
        tick_none = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM requirement where status <> 'disabled'")
        
        tick_closed = cursor.fetchone()[0] - tick_none - tick_open
        
        return [tick_open, tick_closed, tick_none]

    #These functions are to update the requirments appropriately
    #in the event that an fp or object is modified.

    def set_ood_by_fp(self, fp_id, comment, author):
        """Set any enabled requirements using this fp_id to out-of-date

        This should only be called when an fp is disabled, and will
        change any enabled requirements to out-of-date that depend
        on that fp. This does not change the status of disabled 
        requirements, because they are not used by convention.         
        """

        #First we find all of the requirements that need to be updated
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("SELECT component, object "
                       "FROM requirement "
                       "WHERE status = 'enabled' "
                       "AND fp = %s" ,(fp_id,))
        #Then we update them with the out-of-date status
        for component, object in cursor:
            Req = Requirement(self.env, component, fp_id, object)
            Req['status'] = 'out-of-date'
            Req.save_changes(author,comment, db=db)
        db.commit()

    def enable_ood_by_fp(self, fp_id, comment, author):
        """Re-enable out-of-date requirements that use the given fp.

        When a disabled fp gets re-enabled, any requirement that 
        depend on that fp may be changed from out-of-date to enabled 
        so long as they do not have a disabled object. 
        """
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("SELECT r.component, r.object "
                       "FROM requirement r, object o "
                       "WHERE r.object = o.id "
                       "AND r.status = 'out-of-date' "
                       "AND o.status <> 'disabled' "
                       "AND r.fp = %s", (fp_id,))

        for component, object in cursor:
            Req = Requirement(self.env, component, fp_id, object)
            Req['status'] = 'enabled'
            Req.save_changes(author,comment, db=db)
        db.commit()

    def set_ood_by_object(self, id, comment, author):
        """Set any enabled requirements using this (object) id to out-of-date.

        This should only be called when an object is disabled, and will
        change any enabled requirements to out-of-date that depend
        on that objece. This does not change the status of disabled 
        requirements, because they are not used by convention.         
        """
        #First we find all of the requirements that need to be updated
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("SELECT component, fp "
                       "FROM requirement "
                       "WHERE status = 'enabled' "
                       "AND object = %s" ,(id,))
        #Then we update them with the out-of-date status
        for component, fp in cursor:
            Req = Requirement(self.env, component, fp, id)
            Req['status'] = 'out-of-date'
            Req.save_changes(author,comment, db=db)
        db.commit()

    def enable_ood_by_object(self, id, comment, author):
        """Re-enable out-of-date requirements that use the given object.

        When a disabled object gets re-enabled, any requirement that 
        depends on that object may be changed from out-of-date to enabled 
        so long as they do not have a disabled fp. 
        """
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("SELECT r.component, r.fp "
                       "FROM requirement r, fp "
                       "WHERE r.fp = fp.id "
                       "AND r.status = 'out-of-date' "
                       "AND fp.status <> 'disabled' "
                       "AND r.object = %s", (id,))

        for component, fp in cursor:
            Req = Requirement(self.env, component, fp, id)
            Req['status'] = 'enabled'
            Req.save_changes(author,comment, db=db)
        db.commit()

class RequirementWikiCache(ReqBase):
    """Class representing a relationship between a wiki and requirement.
    
    The purpose of this class it to act as model for the
    requirement_wiki_cache database table and allow the user to create,
    remove, or update entries in the requirement_wiki_chache table in
    a trivial fashion.
    """
    
    def __init__(self, env, component=None, fp=None, object=None, wiki_name=None, wiki_version=None, db=None):
        """Construct the RequirementWikiCache instance.
        
        Construct the RequirementWikiCache instance with appropriate
        defaults if all the appropriate values were not passed. If all
        the approriate values were passed then build an instance to
        represent the relationship between the wiki and the requirement
        so that it may be inserted, deleted, or updated as needed by
        the user.
        """
        
        ReqBase.__init__(self, env, db)
        
        # Check to make sure that I was given all the values needed
        # to match/create a relationship between a requirement and a
        # wiki.
        if ((component is not None) and (fp is not None) and
            (object is not None) and (wiki_name is not None) and
            (wiki_version is not None)):
            
            # Check if a database was given as a parameter. If one was
            # was not then grab it from the environment.
            db = self._get_db(db)
                
            # Check if the given relationship already exists in the
            # database table. If so then intialize the object
            # identifying such. If NOT then initialize the object
            # identifying that it is not already in the datbase table.
            cursor = db.cursor()
            cursor.execute("SELECT component,fp,object,wiki_name,wiki_version FROM requirement_wiki_cache "
                           "WHERE component=%s and fp=%s and object=%s and wiki_name=%s and wiki_version=%s",
                           (component, fp, object, wiki_name, wiki_version))
            row = cursor.fetchone()
            if row:
                self.component = self._old_component = component
                self.fp = self._old_fp = fp
                self.object = self._old_object = object
                self.wiki_name = self._old_wiki_name = wiki_name
                self.wiki_version = self._old_wiki_version = wiki_version
            else:
                self.component = component
                self.fp = fp
                self.object = object
                self.wiki_name = wiki_name
                self.wiki_version = wiki_version
                self._old_component = self._old_fp = None
                self._old_object = self._old_wiki_name = self._old_wiki_version = None

    # Create the exists attribute of the object such that it is equal
    # to the lambda function which checks to make sure that all the
    # _old_* attributes exist and are not None. Hence, if this is
    # True it states that the relationship already exists in the
    # database table. The purpose of doing this as an attribute using
    # a lambda function is to allow for simple assertion calls like the
    # following:
    #
    # assert self.exists, 'Assertion failed message.'
    #
    exists = property(
      fget=lambda self: (
         (self._old_component is not None) and 
         (self._old_fp is not None) and 
         (self._old_object is not None) and 
         (self._old_wiki_name is not None) and 
         (self._old_wiki_version is not None)
      )
    )

    def delete(self, db=None):
        """Delete the requirement to wiki relationship.
        
        Delete the entry in the requirement_wiki_cache database table
        that the instance of this class represents.
        """
        
        assert self.exists, 'Cannot delete non-existent requirement_wiki_cache'
        db, handle_ta = self._get_db_for_write(db)

        cursor = db.cursor()
        self.env.log.info(
           'Deleting requirement_wiki_cache (%s,%s,%s,%s,%s)' 
           % (self.component, self.fp, self.object, self.wiki_name, self.wiki_version)
        )
        cursor.execute("DELETE FROM requirement_wiki_cache WHERE component=%s "
           "and fp=%s and object=%s and wiki_name=%s and wiki_version=%s", 
           (self.component,self.fp,self.object,self.wiki_name,self.wiki_version))

        self.component = self._old_component = None
        self.fp = self._old_fp = None
        self.object = self._old_object = None
        self.wiki_name = self._old_wiki_name = None
        self.wiki_version = self._old_wiki_version = None

        if handle_ta:
            db.commit()
            
    def delete_by_page(self, db=None):
        """Delete the requirement to wiki relationship.
        
        Delete the entries in the requirement_wiki_cache database table
        that the instance of this class represents, neglecting the
        wiki_version. This is used to dissassociate requirements from
        all versions of a specific wiki page.
        """
        
        assert self.exists, 'Cannot delete non-existent requirement_wiki_cache'
        db, handle_ta = self._get_db_for_write(db)

        cursor = db.cursor()
        self.env.log.info(
           'Deleting requirement_wiki_cache (%s,%s,%s,%s,*)' 
           % (self.component, self.fp, self.object, self.wiki_name))
        
        cursor.execute("DELETE FROM requirement_wiki_cache WHERE "
           "component=%s and fp=%s and object=%s and wiki_name=%s", 
           (self.component, self.fp, self.object, self.wiki_name))

        self.component = self._old_component = None
        self.fp = self._old_fp = None
        self.object = self._old_object = None
        self.wiki_name = self._old_wiki_name = None
        self.wiki_version = self._old_wiki_version = None

        if handle_ta:
            db.commit()        

    def insert(self, db=None):
        """Insert the requirement to wiki relationship.
        
        Insert the entry in the requirement_wiki_cache database table
        that the instance of this class represents.
        """
        
        assert not self.exists, 'Cannot insert existing requirement_wiki_cache'
        assert self.component, 'Cannot create requirement_wiki_cache with no component'
        assert self.fp, 'Cannot create requirement_wiki_cache with no fp'
        assert self.object, 'Cannot create requirement_wiki_cache with no object'
        assert self.wiki_name, 'Cannot create requirement_wiki_cache with no wiki_name'
        assert self.wiki_version, 'Cannot create requirement_wiki_cache with no wiki_version'
        
        self.component = self.component.strip()
        self.object = self.object.strip()
        self.wiki_name = self.wiki_name.strip()
        
        db, handle_ta = self._get_db_for_write(db)

        cursor = db.cursor()
        self.env.log.debug(
           "Creating new requirement_wiki_cache (%s,%s,%s,%s,%s)" 
           % (self.component, self.fp, self.object, self.wiki_name, self.wiki_version)
        )
        cursor.execute("INSERT INTO requirement_wiki_cache "
           "(component,fp,object,wiki_name,wiki_version) "
           "VALUES('%s','%s','%s','%s','%s')" 
           % (self.component, self.fp, self.object, self.wiki_name, self.wiki_version))

        if handle_ta:
            db.commit()
            
    def update(self, db=None):
        """Update the requirement to wiki relationship.
        
        Update the entry in the requirement_wiki_cache database table
        that the instance of this class represents.
        """
        
        assert self.exists, 'Cannot update non-existing requirement_wiki_cache'
        assert self.component, 'Cannot update requirement_wiki_cache with no component'
        assert self.fp, 'Cannot update requirement_wiki_cache with no fp'
        assert self.object, 'Cannot update requirement_wiki_cache with no object'
        assert self.wiki_name, 'Cannot update requirement_wiki_cache with no wiki_name'
        assert self.wiki_version, 'Cannot update requirement_wiki_cache with no wiki_version'
        
        self.component = self.component.strip()
        self.object = self.object.strip()
        self.wiki_name = self.wiki_name.strip()

        db, handle_ta = self._get_db_for_write(db)

        cursor = db.cursor()
        self.env.log.info(
           'Updating requirement_wiki_cache (%s,%s,%s,%s,%s)' 
           % (self.component, self.fp, self.object, self.wiki_name, self.wiki_version)
        )
        cursor.execute("UPDATE requirement_wiki_cache SET component=%s,fp=%s,object=%s,wiki_name=%s,wiki_version=%s "
                       "WHERE component=%s and fp=%s and object=%s and wiki_name=%s and wiki_version=%s",
                       (self.component, self.fp, self.object, self.wiki_name, self.wiki_version,
                        self._old_component, self._old_fp, self._old_object, self._old_wiki_name, self._old_wiki_version))

        if handle_ta:
            db.commit()

class RequirementTicketCache(ReqBase):
    """A class representing a RequirementTicketCache object.
    
    The purpose of this class it to act as model for the
    requirement_ticket_cache database table.
    """
    
    def __init__(self, env, ticket_id=None, component=None, fp=None, 
                 object=None, db=None):
        """Construct the RequirementTicketCache instance.
        
        Construct the RequirementTicketCache instance with appropriate
        defaults if the appropriate values were not passed.
        """
       
        ReqBase.__init__(self, env, db)
      
        # check to make sure we at least have a ticket number: 
        if ticket_id:
            db = self._get_db(db)
            cursor = db.cursor()
            cursor.execute("SELECT component,fp,object,ticket "
                           "FROM requirement_ticket_cache "
                           "WHERE ticket=%s", (ticket_id,))
            row = cursor.fetchone()
            if row:
                self.ticket_id = self._old_ticket_id = ticket_id
                # ticket_in_table used to find out if this ticket number
                #  has any entries in the requirement_ticket_cache table at all
                self.ticket_in_table = True
            else:
                self.ticket_id = ticket_id
                self.ticket_in_table = False
                self._old_ticket_id = None

            # Check to make sure that I was given the rest of the values needed
            # to match/create a relationship between a requirement and a
            # ticket.    
            if ((component is not None) and (fp is not None) and
                (object is not None)):    
                    cursor.execute("SELECT component,fp,object,ticket "
                                   "FROM requirement_ticket_cache "
                                   "WHERE component=%s and fp=%s and object=%s"
                                   " and ticket=%s",
                                   (component, fp, object, ticket_id))
                    row = cursor.fetchone()
                    if row:
                        self.component = self._old_component = component
                        self.fp = self._old_fp = fp
                        self.object = self._old_object = object
                        self.ticket_id = self._old_ticket_id = ticket_id
                    else:
                        self.component = component
                        self.fp = fp
                        self.object = object
                        self.ticket_id = ticket_id
                        self._old_component = self._old_fp = \
                                              self._old_object = \
                                              self._old_ticket_id = None
                                          
    exists = property(fget=lambda self: ((self._old_component is not None) \
                      and (self._old_fp is not None) and \
                      (self._old_object is not None) and \
                      (self._old_ticket_id is not None)))

    def delete(self, db=None):
        """Delete requirement_ticket_cache entries.
        
        Delete entries in the requirement_ticket_cache database table
        that the instance of this class represents. Only deletes those
        entries that are associated with the given ticket.
        """
        
        assert self.ticket_in_table, \
            'Cannot delete non-existent requirement_ticket_cache'
        db, handle_ta = self._get_db_for_write(db)

        cursor = db.cursor()
        self.env.log.info(
            'Deleting requirement_ticket_cache for ticket (%s)' % \
            (self.ticket_id))
        cursor.execute("DELETE FROM requirement_ticket_cache "
                       "WHERE ticket=%s", (self.ticket_id,))

        if handle_ta:
            db.commit()
            self.component = self._old_component = None
            self.fp = self._old_fp = None
            self.object = self._old_object = None
            self.ticket_id = self._old_ticket_id = None            
            cursor.execute("SELECT ticket "
                           "FROM requirement_ticket_cache "
                           "WHERE ticket=%s",
                           (self.ticket_id,))
            if (None == cursor.fetchone()):
                self.ticket_in_table = False

    def insert(self, db=None):
        """Insert the requirement_ticket_cache entry.
        
        Insert the requirement_ticket_cache entry this object represents
        into the requirement_ticket_cache database table.
        """
        
        assert not self.exists, \
            'Cannot insert existing requirement_ticket_cache'
        assert self.component, \
            'Cannot create requirement_ticket_cache with no component'
        assert self.fp, 'Cannot create requirement_ticket_cache with no fp'
        assert self.object, \
            'Cannot create requirement_ticket_cache with no object'
        assert self.ticket_id, \
            'Cannot create requirement_ticket_cache with no ticket'
        
        self.component = self.component.strip()
        
        db, handle_ta = self._get_db_for_write(db)

        cursor = db.cursor()
        self.env.log.debug(
            "Creating new requirement_ticket_cache (%s,%s,%s,%s)" % (
            self.component, self.fp, self.object, self.ticket_id))
        cursor.execute("INSERT INTO requirement_ticket_cache "
                       "(component,fp,object,ticket) "
                       "VALUES (%s,%s,%s,%s)",
                       (self.component, self.fp, self.object, self.ticket_id))

        if handle_ta:
            db.commit()
            self.ticket_in_table = True
            self._old_component = self.component
            self._old_fp = self.fp
            self._old_object = self.object
            self._old_ticket_id = self.ticket_id

class Fp(ReqBase):
    """Class representing the functional primitive (fp) in the 
    <component fp object> triplet.

    This class acts as a model for the fp data base table, and 
    oversees the manipulation of data between the programmer,
    database, and the end-user. It allows for creation, editing,
    enabling/disabling and updating entries in the fp table.
    """

    def __init__(self, env, name=None, id=None, db=None):
        """Initializes an instance of a functional primitive.

        The three optional parameters each have special uses:
        The 'name' parameter is used if the fp exists but you
        don't know it's id number.

        The 'id' parameter is used when a fp has already been
        created, but a new instance of it has to be made to access/
        change/view the data for it.

        The 'db' parameter is only used when a database outside of 
        the one specified in the environment ('env') is to be used.
        As this means that we cannot be sure of ownership of the 
        database, including a specified db will prevent any of the
        Fp functions from committing in the database (but will still
        insert and update).
        
        by passing neither the name nor id, an empty fp instance is
        created, which can then have values assigned to it (i.e.
        my_fp['name' = 'squish') and then call my_fp.insert() to 
        save a new fp to the database. Note that insert() will raise
        an exception if a fp with the same name already exists.

        Generally, either the id is passed OR the name is passed OR
        neither is passed. We handle the case where id AND name are
        passed, but there is really no reason to pass both.
        """
        ReqBase.__init__(self, env, db)
        self.cache = DataCache(env, db)

        self.fields = FpSystem(self.env).get_fp_fields()
        self.values = {}

        if id is not None:
            if name is not None:
                # If I was given both the name and the id parameters
                # I need to make sure that they are both in the same
                # record in the database, otherwise I was given wrong
                # or outdated information.
                if not self._verify_id_name_map(name, id, db):
                    raise TracError('Fp Name and id given did not'
                                    'match the database record.')
            # if I was given an id number and there is not a
            # conflicting name, I grab the existing fp information
            # from the database.
            self._fetch_fp_by_id(id, db)
        else:
            if name is not None:
                # If I was given just the name, I grab the 
                # existing fp information from the database.
                self._fetch_fp_by_name(name,db)
            else:
                # If i was not given a name or id, I create an
                # empty default instance of an fp.
                self._init_defaults(db)
                self.fp_id = None
                self.time_created = None
                self.time_changed = None

        self._old = {}
    

    exists = property(fget=lambda self: self.fp_id is not None)

    def _verify_id_name_map(self, name, fp_id, db):
        """Verify that the name/id combo given exists in the database"""

        db = self._get_db(db)

        cursor = db.cursor()
        cursor.execute("SELECT name FROM fp WHERE id =" + str(fp_id))
        row = cursor.fetchone()
        if not row:
            raise TracError('Fp does not exist')
        if row[0] == name:
            # the given id and name map correctly.
            return True
        else:
            # the name is outdated or wrong.
            return False

    def _init_defaults(self, db=None):
        """Initialize an instance of fp with its proper fields"""
        for field in self.fields:
            default = None

            # If field is NOT a custom field then check the config file
            # for any default values for the specific field.
            if not field.get('custom'):
                default = self.env.config.get('fp',
                                             'default_' +field['name'])
            # if field IS a custom field then set the default values
            # and options appropriately.
            else:
                default = field.get('value')
                options = field.get('options')
                if default and options and default not in options:
                    try:
                        default = options[int(default)]
                    except (ValueError, IndexError):
                        self.env.log.warning('Invalid default value "%s'
                                             '" for custom field "%s"'
                                             % (default, field['name']))
            if default:
                self.values.setdefault(field['name'],default)

    def _fetch_fp_by_name(self, name, db=None):
        """Get a fp from the database using the given name."""

        db = self._get_db(db)
        
        # get the standard fp fields
        std_fields = [f['name'] for f in self.fields if not f.get('custom')]
        cursor = db.cursor()
        cursor.execute("SELECT %s,time,changetime,id FROM fp "
                       "WHERE name='%s'" 
                       % (','.join(std_fields),str(name)))
        row = cursor.fetchone()
        if not row:
            raise TracError('fp %s does not exist.' % name)

        for i in range(len(std_fields)):
            self.values[std_fields[i]] = row[i] or ''
        self.time_created = row[len(std_fields)]
        self.time_changed = row[len(std_fields) + 1]
        self.fp_id = row[len(std_fields) + 2]
        self.values['id'] = self.fp_id
        self._fetch_fp_custom(self.fp_id, db)

    def _fetch_fp_by_id(self, fp_id, db=None):
        """Get an fp from the database using the given id"""

        db = self._get_db(db)

        #getting the standard object fields
        std_fields = [f['name'] for f in self.fields if not f.get('custom')]
        cursor = db.cursor()
        cursor.execute("SELECT %s,time,changetime FROM fp "
                       "WHERE id='%s'"
                        % (','.join(std_fields), str(fp_id)))
        row = cursor.fetchone()
        if not row:
            raise TracError('fp does not exist.')

        for i in range(len(std_fields)):
            self.values[std_fields[i]] = row[i] or ''
        self.time_created = row[len(std_fields)]
        self.time_changed = row[len(std_fields) + 1]
        self.values['id'] = fp_id
        self.fp_id = fp_id
        self._fetch_fp_custom(fp_id, db)

    def _fetch_fp_custom(self, fp_id, db=None):
        """Get the custom fields of a fp from the database"""

        db = self._get_db(db)
        cursor = db.cursor()

        custom_fields = [f['name'] for f in self.fields if f.get('custom')]
        cursor.execute("SELECT name,value FROM fp_custom "
                       "WHERE id = %s" % str(fp_id))
        for name, value in cursor:
            if name in custom_fields:
                self.values[name] = value

    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):
        """Log fp modifications so the table fp_change can be updated"""

        if self.values.has_key(name) and self.values[name] == value:
            return

        if not self._old.has_key(name):
            self._old[name] = self.values.get(name)
        elif self._old[name] == value:
            del self._old[name]

        if value:
            field = [field for field in self.fields if field['name'] == name]    
            if field and field[0].get('type') != 'textarea':
                value = value.strip()

        self.values[name] = value

    def populate(self, values):
        """Populate the fp with 'suitable' values from a dictionary"""
        field_names = [f['name'] for f in self.fields]
        for name in [name for name in values.keys() 
                     if name in field_names]:
            self[name] = values.get(name, '')

        # We have to do an extra trick to catch unchecked checkboxes
        for name in [name for name in values.keys() 
                     if name[9:] in field_names
                     and name.startswith('checkbox_')]:
            if not values.has_key(name[9:]):
                self[name[9:]] = '0'

    def insert(self, when=0, db=None):
        """Add fp to database. The fp cannot already exist in the
        database. Returns True if the object is added, False otherwise
        """

        assert not self.exists, 'Cannot insert an existing fp'
        db, handle_ra = self._get_db_for_write(db)

        # Add a timestamp
        if not when:
            when = time.time()
        when = int(when)
        self.time_created = self.time_changed = when

        cursor = db.cursor()

        cursor.execute("SELECT 'a' FROM fp WHERE name='"+
                       self.values['name']+"'")
        row = cursor.fetchone()
        if row:
            raise TracError('Fp %s already exists.' %
                            (self.values['name']))

        self['status'] = 'enabled'

         # Insert object record
        std_fields = [f['name'] for f in self.fields 
                      if not f.get('custom')
                      and self.values.has_key(f['name'])]

        cursor.execute("INSERT INTO fp (%s,time,changetime) VALUES(%s)"
                       % (','.join(std_fields),
                          ','.join(['%s'] * (len(std_fields) + 2))),
                          [self[name] for name in std_fields] +
                          [self.time_created, self.time_changed])

        cursor.execute("SELECT id FROM fp WHERE name ='"+
                       self.values['name']+"'")
        row = cursor.fetchone()
        if row:
            self['id'] = row[0]
            self.fp_id = self['id']
        else:
            raise TracError('Failed to insert; could not find object '
                            'with given name')

        # Insert custom fields
        custom_fields = [f['name'] for f in self.fields 
                         if f.get('custom')
                         and self.values.has_key(f['name'])]
        if custom_fields:
            cursor.executemany("INSERT INTO fp_custom (id,name,value)"
                               " VALUES (%s,%s,%s)",
                               [(self.fp_id, name, self[name])
                                for name in custom_fields])
        if handle_ra:
            db.commit()

        self._old = {}

        # clear cached data affected by this
        self.cache.clean_data(None, self.fp_id, None)

        for listener in FpSystem(self.env).change_listeners:
            listener.fp_created(self)

        if self.fp_id is not None:
            return True
        else:
            return False

    def save_changes(self, author, comment, when=0, db=None, cnum=''):
        """Store fp changes in the database. The fp must already exist 
        in the database. Returns False if there were no changes to save,
        True otherwise.
        """

        assert self.exists, 'Cannot update a new fp'

        if not self._old and not comment:
            return False # Not modified

        db, handle_ra = self._get_db_for_write(db)
        cursor = db.cursor()
        when = int(when or time.time())

        # Fix up cc list separators and remove duplicates 
        if self.values.has_key('cc'):
            cclist = []
            for cc in re.split(r'[;,\s]+', self.values['cc']):
                if cc not in cclist:
                    cclist.append(cc)
            self.values['cc'] = ', '.join(cclist)

        custom_fields = [f['name'] for f in self.fields 
                         if f.get('custom')]
        for name in self._old.keys():
            if name in custom_fields:
                cursor.execute("SELECT * FROM fp_custom "
                               "WHERE id=%s AND name =%s", 
                               (self.values['id'], name))
                if cursor.fetchone():
                    cursor.execute("UPDATE fp_custom SET value=%s "
                                   "WHERE id=%s AND name=%s",
                            (self.values[name],self.values['id'],name))
                else:
                    cursor.execute("INSERT INTO fp_custom "
                                   "(id,name,value) VALUES(%s,%s,%s",
                            (self.values['id'],name,self.values[name]))
            else:
                cursor.execute("UPDATE fp SET %s=%%s WHERE id =%%s"
                               % name,
                               (self.values[name],self.values['id']))
            cursor.execute("INSERT INTO fp_change "
                           "(id,time,author,field,oldvalue,newvalue) "
                           "VALUES (%s, %s, %s, %s, %s, %s)",
                           (self.values['id'], when, author, name,
                            self._old[name], self[name]))  
        # always save comment, even if empty (numbering support for
        # timeline)
        cursor.execute("INSERT INTO fp_change "
                       "(id,time,author,field,oldvalue,newvalue) "
                       "VALUES (%s,%s,%s,'comment',%s,%s)",
                       (self.values['id'], when, author, cnum, comment))

        cursor.execute("UPDATE fp SET changetime=%s "
                       "WHERE id=%s", (when, self.values['id']))

        if handle_ra:
            db.commit()

        # clear cached data affected by this
        self.cache.clean_data(None, self.values['id'], None)

        if self._old.has_key('status') and \
            self._old['status'] =='disabled' and \
            self['status'] == 'enabled':
            for listener in FpSystem(self.env).change_listeners:
                listener.fp_enabled(self, comment, author)

        elif self._old.has_key('status') and \
             self._old['status'] == 'enabled' and \
             self['status'] == 'disabled':
            for listener in FpSystem(self.env).change_listeners:
                listener.fp_disabled(self, comment, author)

        else:
            for listener in FpSystem(self.env).change_listeners:
                listener.fp_changed(self, comment, author,self._old)

        self._old = {}
        self.time_changed = when

        return True

    def get_changelog(self, when=0, db=None):
        """Return the changelog as a list of tuples of the form
        (time, author, field, oldvalue, newvalue).
        """

        when = int(when)
        db = self._get_db(db)
        cursor = db.cursor()
        if when:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM fp_change WHERE time=%s AND id=%%s"
                           % when, (self.values['id'],))
        else:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM fp_change "
                           "WHERE id=%s "
                           "ORDER BY time", (self.values['id'],))
        log = []
        for t, author, field, oldvalue, newvalue in cursor:
            log.append((int(t), author, field, oldvalue or '', 
                        newvalue or ''))
        return log

    def get_fp_hyp_info(self, db=None):
        """Get names and descriptions of all fps and their hyponyms.
        
        This function returns all of the information on fp's and their
        hyponyms. It does this by returning a list of dictionaries. 
        Each dictionary in this list has the keys 'fp', 'hyponyms', 
        and 'description'. 

        The 'fp' key's associated value is a tuple of the form (name, status). 

        The 'hyponyms' key's associated value is a list of tuples of the 
        form (name,status).

        The 'description' key's associated value is a string.
        """
        db = self._get_db(db)
        cursor = db.cursor()
        info_list = []
        temp_dict = {}
        temp_list = []
        cursor.execute("SELECT fp.name, fp.status, h.name, h.status, "
                              "fp.description "
                       "FROM fp LEFT JOIN hyponym AS h "
                       "ON fp.id = h.fp "
                       "ORDER BY fp.name, h.name")

        for row in cursor:
            if 'fp' not in temp_dict:
                temp_dict['fp'] = (str(row[0]), str(row[1]))
                if row[4] != None:
                    temp_dict['description'] = str(row[4])
                else:
                    temp_dict['description'] = ''
                if row[2] != None:
                    temp_list.append( (str(row[2]), str(row[3])) )
            elif temp_dict['fp'] != (str(row[0]),str(row[1])):
                temp_dict['hyponyms'] = temp_list
                temp_list = []
                info_list.append(temp_dict)
                temp_dict = {'fp':(str(row[0]),str(row[1]))} 
                if row[4] != None:
                    temp_dict['description'] = str(row[4])
                else:
                    temp_dict['description'] = ''
                if row[2] != None:
                    temp_list.append( (str(row[2]), str(row[3])) )
            else:
                temp_list.append( (str(row[2]), str(row[3])) )

        if temp_dict != {}:
            temp_dict['hyponyms'] = temp_list
            info_list.append(temp_dict)

        return info_list

    def get_fps(self, db=None, timestamp=None):
        # Function commented out because another function 
        # written in Requirements class replaces this one
        # use get_fps in Requirements class
        # this function is left in case future reference
        # is needed. 
        """
        # Return a list of fps
        # Returns a list of fps at a given time. 

        db = self._get_db(db)
        cursor = db.cursor()
        fps = []
    
        if timestamp:
            # Aquire a list of all the fps that have never been changed and
            # where created before our time of interest
            #
            # Union with 
            #
            # Aquire a list of all the fps that have previously been
            # disabled and are enabled at the time of interest
            query = "(SELECT a.id, a.name FROM fp as a WHERE a.time = a.changetime AND a.time < " + str(timestamp) + " UNION " 
            query += "SELECT b.id, b.name FROM fp_change as b WHERE b.field = 'status' AND b.newvalue = 'enabled' AND b.time = (SELECT MAX(c.time) FROM fp_change as c WHERE c.id = b.id AND c.time < " + str(timestamp) + ")) ORDER BY NAME"
            cursor.execute(query)
        else:
            cursor.execute("SELECT fp.id, fp.name "
                           "FROM fp WHERE fp.status == 'enabled' "
                           "ORDER BY fp.name")
    
        fps = cursor.fetchall()
        return fps
        """

    def get_enabled_fps_prefix(self, prefix='', db=None):
        """

        """

        db = self._get_db(db)
        cursor = db.cursor()
        items = []

        cursor.execute("SELECT name FROM fp "
                       "WHERE name LIKE '%s%%' AND "
                       "status = 'enabled' ORDER BY name" % (prefix,))
        for fp in cursor:
            items.append((fp[0],'(FP)'))

        cursor.execute("SELECT h.name,fp.name FROM hyponym h, fp "
                       "WHERE h.name LIKE '%s%%' AND h.fp = fp.id AND "
                       "fp.status = 'enabled' AND h.status = 'enabled'"
                       "ORDER BY fp.name" % (prefix,))
        for hyp in cursor:
            items.append((hyp[1],'(H: '+hyp[0]+')'))

        return items

    def set_on_fly_fp(self, disenabled):
        db, handle_ra = self._get_db_for_write()
        cursor = db.cursor() 
        cursor.execute("UPDATE on_the_fly "
                       "SET status=%s "
                       "WHERE name='fp'", (disenabled,))
        db.commit()
 
    def check_on_fly_fp(self):
        db = self._get_db()
        cursor = db.cursor() 
        cursor.execute("SELECT status "
                       "FROM on_the_fly "
                       "WHERE name='fp'")
        row = cursor.fetchone()
        if(row != None):
            if row[0] == "enabled":
                return "enabled"
        return "disabled"

class Object(ReqBase):
    """Class representing the object in the <component fp object> triplet.

    The purpose of this class it to act as model for the
    object database table and allow the user to create,
    enable/disable, or update entries in the object table.
    """

    def __init__(self, env, name=None, id=None, db=None):
        ReqBase.__init__(self, env, db)
        self.cache = DataCache(env, db)

        self.fields = ObjectSystem(self.env).get_object_fields()
        self.values = {}

        if id is not None:
            if name is not None:
                #If I was given an object id and a name, I need to check
                #that they are actually associated with each other in
                #the database.
                if not self._verify_id_name_map(name, id, db):
                    raise TracError('Name and id given did not match the database record.')
            #Grab the object by its id number whether or not name was given
            self._fetch_object_by_id(id, db)
    
        else:
            if name is not None:
                #If we were given a name and not the id, grab the object
                #from the database by name.
                self._fetch_object_by_name(name, db)
            else:
                #If we were given neither a name nor an object, create a
                #default instance.
                self._init_defaults(db)
                self.obj_id = None
                self.time_created = None
                self.time_changed = None

        self._old = {}

    exists = property(fget=lambda self: self.obj_id is not None)

    def _verify_id_name_map(self, name, obj_id, db):
        """Verify that the name/id combo given exists in the database."""

        db = self._get_db(db)

        cursor = db.cursor()
        cursor.execute("SELECT name FROM object WHERE id = " + str(obj_id))
        row = cursor.fetchone()
        if not row:
            raise TracError('Object does not exist')
        if row[0] == name:
            return True
        else:
            return False
            
    def _init_defaults(self, db=None):
        for field in self.fields:
            default = None
        
            # If field is NOT a custom field then check the config file
            # for any default values for the specific field.
            if not field.get('custom'):
                default = self.env.config.get('object',
                                          'default_' + field['name'])
            # If field IS a custom field then set the default values and
            # options appropriately.
            else:
                default = field.get('value')
                options = field.get('options')
                if default and options and default not in options:
                    try:
                        default = options[int(default)]
                    except (ValueError, IndexError):
                        self.env.log.warning('Invalid default value "%s" '
                                             'for custom field "%s"'
                                             % (default, field['name']))
            if default:
                self.values.setdefault(field['name'], default) 

    def _fetch_object_by_name(self, name, db=None):
        """Get an object from the database using the given name."""

        db = self._get_db(db)

        #getting the standard object fields
        std_fields = [f['name'] for f in self.fields if not f.get('custom')]
        cursor = db.cursor()
        cursor.execute("SELECT %s,time,changetime,id FROM object WHERE name='%s'"
                        % (','.join(std_fields), str(name)))
        row = cursor.fetchone()
        if not row:
            raise TracError('Object %s does not exist.' % (name))

        for i in range(len(std_fields)):
            self.values[std_fields[i]] = row[i] or ''
        self.time_created = row[len(std_fields)]
        self.time_changed = row[len(std_fields) + 1]
        self.obj_id = row[len(std_fields) + 2]
        self.values['id'] = self.obj_id
        self._fetch_object_custom(self.obj_id, db)
    
    def _fetch_object_by_id(self, obj_id, db=None):
        """Get an object from the database using the given id."""

        db = self._get_db(db)

        #getting the standard object fields
        std_fields = [f['name'] for f in self.fields if not f.get('custom')]
        cursor = db.cursor()
        cursor.execute("SELECT %s,time,changetime FROM object WHERE id='%s'"
                        % (','.join(std_fields), str(obj_id)))
        row = cursor.fetchone()
        if not row:
            raise TracError('Object does not exist.')

        for i in range(len(std_fields)):
            self.values[std_fields[i]] = row[i] or ''
        self.time_created = row[len(std_fields)]
        self.time_changed = row[len(std_fields) + 1]
        self.values['id'] = obj_id
        self.obj_id = obj_id
        self._fetch_object_custom(obj_id, db)

    def _fetch_object_custom(self, obj_id, db=None):
        """Get the custom fields of an object from the database"""
        
        db = self._get_db(db)
        cursor = db.cursor()

        custom_fields = [f['name'] for f in self.fields if f.get('custom')]
        cursor.execute("SELECT name,value FROM object_custom "
                       "WHERE id = %s" % str(obj_id))
        for name, value in cursor:
            if name in custom_fields:
                self.values[name] = value

    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):        
        """Log object modifications so the table object_change can be updated"""

        if self.values.has_key(name) and self.values[name] == value:
            return

        if not self._old.has_key(name): # Changed field
            self._old[name] = self.values.get(name)
        elif self._old[name] == value: # Change of field reverted
            del self._old[name]

        if value:
            field = [field for field in self.fields if field['name'] == name]                  

            if field and field[0].get('type') != 'textarea':
                value = value.strip()

        self.values[name] = value

    def populate(self, values):
        """Populate the object with 'suitable' values from a dictionary"""

        field_names = [f['name'] for f in self.fields]
        for name in [name for name in values.keys() if name in field_names]:
            self[name] = values.get(name, '')

        # We have to do an extra trick to catch unchecked checkboxes
        for name in [name for name in values.keys() if name[9:] in field_names
                     and name.startswith('checkbox_')]:
            if not values.has_key(name[9:]):
                self[name[9:]] = '0'

    def insert(self, when=0, db=None):
        """Add object to database.  The object cannot already exist in
        the database.  Returns True if the object is added, False otherwise
        """

        assert not self.exists, 'Cannot insert an existing object'
        db, handle_ra = self._get_db_for_write(db)

        # Add a timestamp
        if not when:
            when = time.time()
        when = int(when)
        self.time_created = self.time_changed = when

        cursor = db.cursor()

        cursor.execute("SELECT 'a' FROM object WHERE name='"+self.values['name']+"'")
        row = cursor.fetchone()
        if row:
            raise TracError('Object %s already exists.' % (self.values['name']))

        self['status'] = 'enabled'

         # Insert object record
        std_fields = [f['name'] for f in self.fields if not f.get('custom')
                      and self.values.has_key(f['name'])]

        cursor.execute("INSERT INTO object (%s,time,changetime) VALUES (%s)"
                       % (','.join(std_fields),
                          ','.join(['%s'] * (len(std_fields) + 2))),
                          [self[name] for name in std_fields] +
                          [self.time_created, self.time_changed])

        cursor.execute("SELECT id FROM object WHERE name = '"+self.values['name']+"'")
        row = cursor.fetchone()
        if row:
            self['id'] = row[0]
            self.obj_id = self['id']
        else:
            raise TracError('Failed to insert; could not find object with given name')

        # Insert custom fields
        custom_fields = [f['name'] for f in self.fields if f.get('custom')
                         and self.values.has_key(f['name'])]
        if custom_fields:
            cursor.executemany("INSERT INTO object_custom (id,name,value) "
                               "VALUES (%s,%s,%s)",
                               [(self.id, name, self[name])
                                for name in custom_fields])

        if handle_ra:
            db.commit()

        self._old = {}

        # clear cached data affected by this
        self.cache.clean_data(None, None, self.obj_id)

        for listener in ObjectSystem(self.env).change_listeners:
            listener.object_created(self)

        if self.obj_id is not None:
            return True
        else:
            return False

    def get_objects(self, db=None, timestamp=None, dict=False):
        """Return a list of objects
        
        If dict == False, returns a list of object ids that are/were
        enabled (valid) at the time given.
        If dict == True, returns a dictionary of {'id':'name', ...} 
        for all valid objects at the time given.
        """

        if timestamp:
            when = timestamp
        else:
            when = time.time()
        
        db = self._get_db(db)
        cursor1 = db.cursor()
        cursor2 = db.cursor()
        objects = []
        obj_dict = {}
        cursor1.execute("SELECT id, name, changetime, status FROM object WHERE time<=%s ORDER BY name", (when,))
        for obj in cursor1:
            # if timestamp is given and it comes before the last changetime
            if timestamp and (timestamp < obj[2]):
                # unroll changes from latest to oldest
                cursor2.execute("SELECT field, oldvalue FROM object_change WHERE id='%s' AND time>'%s' ORDER BY time DESC" % obj[0], timestamp)
                for change in cursor2:
                    # at this point we only care about name and status changes
                    if change[0]=='name':
                        obj[0] = change[1]
                    elif change[0]=='status':
                        obj[3] = change[1]
            
            # only return if enabled
            #if obj[3]=='enabled':
            objects.append(obj[0])
            obj_dict[obj[0]] = obj[1]
        if dict == True:
            return obj_dict
        else:
            return objects

    def save_changes(self, author, comment, when=0, db=None, cnum=''):
        """Store requirement changes in the database. The requirement 
        must already exist in the database. Returns False if there 
        were no changes to save, True  otherwise.
        """

        assert self.exists, 'Cannot update a new object'

        if not self._old and not comment:
            return False # Not modified

        db, handle_ra = self._get_db_for_write(db)
        cursor = db.cursor()
        when = int(when or time.time())

        # Fix up cc list separators and remove duplicates 
        if self.values.has_key('cc'):
            cclist = []
            for cc in re.split(r'[;,\s]+', self.values['cc']):
                if cc not in cclist:
                    cclist.append(cc)
            self.values['cc'] = ', '.join(cclist)

        custom_fields = [f['name'] for f in self.fields if f.get('custom')]
        for name in self._old.keys():
            if name in custom_fields:
                cursor.execute("SELECT * FROM object_custom WHERE id=%s "
                               "AND name =%s", (self.values['id'], name))
                if cursor.fetchone():
                    cursor.execute("UPDATE object_custom SET value=%s " 
                                   "WHERE id=%s AND name=%s",
                                   (self.values[name],self.values['id'], name))
                else:
                    cursor.execute("INSERT INTO object_custom (id,name,value) "
                                   "VALUES(%s,%s,%s", 
                                   (self.values['id'],name,self.values[name]))
            else:
                cursor.execute("UPDATE object SET %s=%%s WHERE id =%%s" % name, 
                               (self.values[name],self.values['id']))
            cursor.execute("INSERT INTO object_change "
                           "(id,time,author,field,oldvalue,newvalue) "
                           "VALUES (%s, %s, %s, %s, %s, %s)",
                           (self.values['id'], when, author, name, self._old[name], self[name]))
        # always save comment, even if empty (numbering support for
        # timeline)
        cursor.execute("INSERT INTO object_change "
                       "(id,time,author,field,oldvalue,newvalue) "
                       "VALUES (%s,%s,%s,'comment',%s,%s)",
                       (self.values['id'], when, author, cnum, comment))

        cursor.execute("UPDATE object SET changetime=%s "
                       "WHERE id=%s", (when, self.values['id']))

        if handle_ra:
            db.commit()

        # clear cached data affected by this
        self.cache.clean_data(None, None, self.values['id'])

        if self._old.has_key('status') and \
           self._old['status'] =='disabled' and \
           self['status'] == 'enabled':
            for listener in ObjectSystem(self.env).change_listeners:
                listener.object_enabled(self, comment, author)

        elif self._old.has_key('status') and \
             self._old['status'] == 'enabled' and \
             self['status'] == 'disabled':
            for listener in ObjectSystem(self.env).change_listeners:
                listener.object_disabled(self, comment, author)

        else:
            for listener in ObjectSystem(self.env).change_listeners:
                listener.object_changed(self, comment, author, self._old)

        self._old = {}
        self.time_changed = when

        return True

    def get_changelog(self, when=0, db=None):
        """Return the changelog as a list of tuples of the form
        (time, author, field, oldvalue, newvalue, permanent).
        """

        when = int(when)
        db = self._get_db(db)
        cursor = db.cursor()
        if when:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM object_change WHERE time=%s AND id=%%s"
                           % when, (self.values['id'],))
        else:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM object_change "
                           "WHERE id=%s "
                           "ORDER BY time", (self.values['id'],))
        log = []
        for t, author, field, oldvalue, newvalue in cursor:
            log.append((int(t), author, field, oldvalue or '', newvalue or ''))

        return log

    def get_obj_info(self, db=None):
        """Get information on objects in database.
        
        Returns a list of dictionaries. Each dictionary in the list
        has the keys 'name', 'status', and 'description'. Each value in
        the dictionary is a string. An empty string is returned if 
        there is a description or status missing in the database,
        but objects must all have names to exist.
        """

        db = self._get_db(db)
        obj_info = []
        temp_dict = {}
        cursor = db.cursor()

        cursor.execute("SELECT name,status,description FROM object "
                       "ORDER BY name")
        for row in cursor:
            temp_dict = {'name':str(row[0]), 
                         'description':'',
                         'status':''}
            if row[2] != None:
                temp_dict['description'] = str(row[2])
            if row[1] != None:
                temp_dict['status'] = str(row[1])
            obj_info.append(temp_dict)

        return obj_info

    def get_enabled_objects_prefix(self, prefix='', db=None):
        """Return a list of objects matching the prefix"""

        db = self._get_db(db)
        cursor = db.cursor()
        objects = []
        cursor.execute("SELECT name FROM object "
                       "WHERE name LIKE '%s%%' AND "
                       "status = 'enabled' ORDER BY name" % (prefix,))
        for obj in cursor:
            objects.append((obj[0],''))
        return objects

    def set_on_fly_obj(self, disenabled):
        db, handle_ra = self._get_db_for_write()
        cursor = db.cursor() 
        cursor.execute("UPDATE on_the_fly "
                       "SET status=%s "
                       "WHERE name='object'",(disenabled,))
        db.commit()
   
    def check_on_fly_obj(self):
        db = self._get_db()
        cursor = db.cursor() 
        cursor.execute("SELECT status "
                       "FROM on_the_fly "
                       "WHERE name='object'")
        row = cursor.fetchone()
        if row != None:
            if row[0] == "enabled":
                return "enabled"
        return "disabled"


class Hyponym(ReqBase):
    """Class representing a hyponym of a functional primitive.

    The purpose of this class it to act as model for the
    hyponym database table and allow the user to create,
    enable/disable, or update entries in the hyponym table.
    """

    def __init__(self, env, name=None, id=None, db=None):
        """Initialize an instance of hyponym.

        'name' is not actually a database key, it is used to get
        a hyponym when the id is not known, such as from a user
        (see Fp.__init__ for full explanation).
        """

        ReqBase.__init__(self, env, db)

        self.fields = HyponymSystem(self.env).get_hyponym_fields()
        self.values = {}


        if id is not None:
            if name is not None:
                #If I was given an hyponym id and a name, I need to check
                #that they are actually associated with each other in
                #the database.
                if not self._verify_id_name_map(name, id, db):
                    raise TracError('Name and id given did not match the database record.')
            #Grab the hyponym by its id number whether or not name was given
            self._fetch_hyponym_by_id(id, db)
    
        else:
            if name is not None:
                #If we were given a name and not the id, grab the hyponym
                #from the database by name.
                self._fetch_hyponym_by_name(name, db)
            else:
                #If we were given neither a name nor an hyponym, create a
                #default instance.
                self._init_defaults(db)
                self.hyp_id = None
                self.time_created = None
                self.time_changed = None

        self._old = {}

    exists = property(fget=lambda self: self.hyp_id is not None)

    def _verify_id_name_map(self, name, hyp_id, db):
        """Verify that the name/id combo given exists in the database."""

        db = self._get_db(db)

        cursor = db.cursor()
        cursor.execute("SELECT name FROM hyponym WHERE id = " + str(hyp_id))
        row = cursor.fetchone()
        if not row:
            raise TracError('Hyponym does not exist')
        if row[0] == name:
            return True
        else:
            return False
            
    def _init_defaults(self, db=None):
        for field in self.fields:
            default = None
        
            # If field is NOT a custom field then check the config file
            # for any default values for the specific field.
            if not field.get('custom'):
                default = self.env.config.get('hyponym',
                                          'default_' + field['name'])
            # If field IS a custom field then set the default values and
            # options appropriately.
            else:
                default = field.get('value')
                options = field.get('options')
                if default and options and default not in options:
                    try:
                        default = options[int(default)]
                    except (ValueError, IndexError):
                        self.env.log.warning('Invalid default value "%s" '
                                             'for custom field "%s"'
                                             % (default, field['name']))
            if default:
                self.values.setdefault(field['name'], default) 

    def _fetch_hyponym_by_name(self, name, db=None):
        """Get an hyponym from the database using the given name."""

        db = self._get_db(db)

        #getting the standard hyponym fields
        std_fields = [f['name'] for f in self.fields if not f.get('custom')]
        cursor = db.cursor()
        cursor.execute("SELECT %s,time,changetime,id "
                       "FROM hyponym WHERE name='%s'"
                        % (','.join(std_fields), str(name)))
        row = cursor.fetchone()
        if not row:
            raise TracError('Hyponym %s does not exist.' % (name))

        for i in range(len(std_fields)):
            self.values[std_fields[i]] = row[i] or ''
        self.time_created = row[len(std_fields)]
        self.time_changed = row[len(std_fields) + 1]
        self.hyp_id = row[len(std_fields) + 2]
        self.values['id'] = self.hyp_id
        self._fetch_hyponym_custom(self.hyp_id, db)
    
    def _fetch_hyponym_by_id(self, hyp_id, db=None):
        """Get an hyponym from the database using the given id."""

        db = self._get_db(db)

        #getting the standard hyponym fields
        std_fields = [f['name'] for f in self.fields if not f.get('custom')]
        cursor = db.cursor()
        cursor.execute("SELECT %s,time,changetime FROM hyponym WHERE id='%s'"
                        % (','.join(std_fields), str(hyp_id)))
        row = cursor.fetchone()
        if not row:
            raise TracError('Hyponym does not exist.')

        for i in range(len(std_fields)):
            self.values[std_fields[i]] = row[i] or ''
        self.time_created = row[len(std_fields)]
        self.time_changed = row[len(std_fields) + 1]
        self.values['id'] = hyp_id
        self.hyp_id = hyp_id
        self._fetch_hyponym_custom(hyp_id, db)

    def _fetch_hyponym_custom(self, hyp_id, db=None):
        """Get the custom fields of an hyponym from the database"""
        
        db = self._get_db(db)
        cursor = db.cursor()

        custom_fields = [f['name'] for f in self.fields if f.get('custom')]
        cursor.execute("SELECT name,value FROM hyponym_custom "
                       "WHERE id = %s" % str(hyp_id))
        for name, value in cursor:
            if name in custom_fields:
                self.values[name] = value

    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):        
        """Log hyponym modifications so the table hyponym_change can be updated"""

        if self.values.has_key(name) and self.values[name] == value:
            return

        if not self._old.has_key(name): # Changed field
            self._old[name] = self.values.get(name)
        elif self._old[name] == value: # Change of field reverted
            del self._old[name]

        if value:
            field = [field for field in self.fields if field['name'] == name]                  

            if field and field[0].get('type') != 'textarea':
                value = value.strip()

        self.values[name] = value

    def populate(self, values):
        """Populate the hyponym with 'suitable' values from a dictionary"""

        field_names = [f['name'] for f in self.fields]
        for name in [name for name in values.keys() if name in field_names]:
            self[name] = values.get(name, '')

        # We have to do an extra trick to catch unchecked checkboxes
        for name in [name for name in values.keys() if name[9:] in field_names
                     and name.startswith('checkbox_')]:
            if not values.has_key(name[9:]):
                self[name[9:]] = '0'

    def insert(self, when=0, db=None):
        """Add hyponym to database.  The hyponym cannot already exist in
        the database.  Returns True if the hyponym is added, False otherwise
        """

        assert not self.exists, 'Cannot insert an existing hyponym'
        db, handle_ra = self._get_db_for_write(db)

        # Add a timestamp
        if not when:
            when = time.time()
        when = int(when)
        self.time_created = self.time_changed = when

        cursor = db.cursor()

        cursor.execute("SELECT 'a' FROM hyponym WHERE name='"+self.values['name']+"'")
        row = cursor.fetchone()
        if row:
            raise TracError('Hyponym %s already exists.' % (self.values['name']))

        self['status'] = 'enabled'

         # Insert hyponym record
        std_fields = [f['name'] for f in self.fields if not f.get('custom')
                      and self.values.has_key(f['name'])]

        cursor.execute("INSERT INTO hyponym (%s,time,changetime) VALUES (%s)"
                       % (','.join(std_fields),
                          ','.join(['%s'] * (len(std_fields) + 2))),
                          [self[name] for name in std_fields] +
                          [self.time_created, self.time_changed])

        cursor.execute("SELECT id FROM hyponym WHERE name = '"+self.values['name']+"'")
        row = cursor.fetchone()
        if row:
            self['id'] = row[0]
            self.hyp_id = self['id']
        else:
            raise TracError('Failed to insert; could not find hyponym with given name')

        # Insert custom fields
        custom_fields = [f['name'] for f in self.fields if f.get('custom')
                         and self.values.has_key(f['name'])]
        if custom_fields:
            cursor.executemany("INSERT INTO hyponym_custom (id,name,value) "
                               "VALUES (%s,%s,%s)",
                               [(self.id, name, self[name])
                                for name in custom_fields])

        if handle_ra:
            db.commit()

        self._old = {}

        for listener in HyponymSystem(self.env).change_listeners:
            listener.hyponym_created(self)

        if self.hyp_id is not None:
            return True
        else:
            return False

    def save_changes(self, author, comment, when=0, db=None, cnum=''):
        """Store requirement changes in the database. The requirement 
        must already exist in the database. Returns False if there 
        were no changes to save, True  otherwise.
        """

        assert self.exists, 'Cannot update a new hyponym'

        if not self._old and not comment:
            return False # Not modified

        db, handle_ra = self._get_db_for_write(db)
        cursor = db.cursor()
        when = int(when or time.time())

        # Fix up cc list separators and remove duplicates 
        if self.values.has_key('cc'):
            cclist = []
            for cc in re.split(r'[;,\s]+', self.values['cc']):
                if cc not in cclist:
                    cclist.append(cc)
            self.values['cc'] = ', '.join(cclist)

        custom_fields = [f['name'] for f in self.fields if f.get('custom')]
        for name in self._old.keys():
            if name in custom_fields:
                cursor.execute("SELECT * FROM hyponym_custom WHERE id=%s "
                               "AND name =%s", (self.values['id'], name))
                if cursor.fetchone():
                    cursor.execute("UPDATE hyponym_custom SET value=%s " 
                                   "WHERE id=%s AND name=%s",
                                   (self.values[name],self.values['id'], name))
                else:
                    cursor.execute("INSERT INTO hyponym_custom (id,name,value) "
                                   "VALUES(%s,%s,%s", 
                                   (self.values['id'],name,self.values[name]))
            else:
                cursor.execute("UPDATE hyponym SET %s=%%s WHERE id =%%s" % name, 
                               (self.values[name],self.values['id']))
            cursor.execute("INSERT INTO hyponym_change "
                           "(id,time,author,field,oldvalue,newvalue) "
                           "VALUES (%s, %s, %s, %s, %s, %s)",
                           (self.values['id'], when, author, name, self._old[name], self[name]))
        # always save comment, even if empty (numbering support for
        # timeline)
        cursor.execute("INSERT INTO hyponym_change "
                       "(id,time,author,field,oldvalue,newvalue) "
                       "VALUES (%s,%s,%s,'comment',%s,%s)",
                       (self.values['id'], when, author, cnum, comment))

        cursor.execute("UPDATE hyponym SET changetime=%s "
                       "WHERE id=%s", (when, self.values['id']))

        if handle_ra:
            db.commit()

        if self._old.has_key('status') and \
           self._old['status'] =='disabled' and \
           self['status'] == 'enabled':
            for listener in HyponymSystem(self.env).change_listeners:
                listener.hyponym_enabled(self, comment, author)

        elif self._old.has_key('status') and \
             self._old['status'] == 'enabled' and \
             self['status'] == 'disabled':
            for listener in HyponymSystem(self.env).change_listeners:
                listener.hyponym_disabled(self, comment, author)

        else:
            for listener in HyponymSystem(self.env).change_listeners:
                listener.hyponym_changed(self, comment, author, old_values)

        old_values = self._old
        self._old = {}
        self.time_changed = when

        return True

    def get_changelog(self, when=0, db=None):
        """Return the changelog as a list of tuples of the form
        (time, author, field, oldvalue, newvalue, permanent).
        """

        when = int(when)
        db = self._get_db(db)
        cursor = db.cursor()
        if when:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM hyponym_change WHERE time=%s AND id=%%s"
                           % when, (self.values['id'],))
        else:
            cursor.execute("SELECT time,author,field,oldvalue,newvalue "
                           "FROM hyponym_change "
                           "WHERE id=%s "
                           "ORDER BY time", (self.values['id'],))
        log = []
        for t, author, field, oldvalue, newvalue in cursor:
            log.append((int(t), author, field, oldvalue or '', newvalue or ''))

        return log

    def swap_with_fp(self, author, comment, when=0, db=None, cnum=''):
        """This swaps the name of a hyponym with the name of its fp.

        This is used when a hyponym is in existence, but has a more
        contextually meaninful name than its associated fp. It trades
        names with it's fp, and logs all changes.

        example:
                fp | hyponyms
         'compose' | 'make', 'create'

        calling "Hyponym(self.env, name='make').swap_with_fp()"
        changes it to :
                fp | hyponyms
            'make' | 'compose', 'create'
        """
        # Make sure that both change logs use same time stamp
        # to prevent possible rollback issues.
        when = int(when or time.time())

        my_fp = Fp(self.env, id=self.values['fp'])
        temp = self.values['name']
        self['name'] = my_fp['name']
        my_fp['name'] = temp
        my_fp.save_changes(author, comment, when, db, cnum)
        self.save_changes(author, comment, when, db, cnum)

class DataCache(ReqBase):
    def get_data(self, component, fp, object, name, db=None):
        db = self._get_db(db)
        cursor = db.cursor()

        cursor.execute("SELECT name, data FROM requirement_data_cache WHERE component=%s AND fp=%s AND object=%s AND name=%s", (component or '*', fp or '*', object or '*', name))
        row = cursor.fetchone()
        if row:
            name, data = row
            return data.decode('hex')
        return None

    def set_data(self, component, fp, object, name, data, db=None):
        db, handle_ra = self._get_db_for_write(db)
        cursor = db.cursor()

        # clean the data so we can do a clean insert
        cursor.execute("DELETE FROM requirement_data_cache WHERE (component=%s OR component='*') AND (fp=%s OR fp='*') AND (object=%s OR object='*') AND name = %s", (component, fp, object, name))

        # Insert the data record
        cursor.execute("INSERT INTO requirement_data_cache (component,fp,object,name,data) VALUES (%s,%s,%s,%s,%s)",  (component or '*', fp or '*', object or '*', name, data.encode('hex')))

        if handle_ra:
            db.commit()

    def clean_data(self, component, fp, object, db=None):
        db, handle_ra = self._get_db_for_write(db)
        cursor = db.cursor()

        # Delete any existing data record
        cursor.execute("DELETE FROM requirement_data_cache WHERE (component=%s OR component='*') AND (fp=%s OR fp='*') AND (object=%s OR object='*')", (component, fp, object))

class Blob:
    """Automatically encode a binary string.
       http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/252531
    """
    def __init__(self, s):
        self.s = s

    def _quote(self):
        return "'%s'" % sqlite.encode(self.s)
