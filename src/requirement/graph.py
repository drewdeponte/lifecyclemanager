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
import gd
import re
import datetime
import cStringIO
import time
import matplotlib
import pickle
from pylab import *
from trac.core import *
from trac.web.main import IRequestHandler
from model import Requirement
from model import Fp
from model import Object
from model import DataCache
from metric import RequirementMetric
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

class RequirementGraphComponent(Component):
    implements(IRequestHandler)

    # Don't let trac.web.main.process_request use a template on us
    use_template = False

    # Reserve room for a Requirement instance
    requirement = None
 
    # IRequestHandler methods
    def match_request(self, req):
        """
        Match /requirement/graph/component-fp-object/graph_name
        """
        if re.match(r'/requirement/graph/\w+-\w+-\w+/\w+/?$', req.path_info) is not None:
            return True
        elif re.match(r'/requirements/graph/\w+/?$', req.path_info) is not None:
            return True
        else:
            return False

    def process_request(self, req):
        # initialize cache component
        self.cache = DataCache(self.env)

        # Grab arguments
        if re.match(r'/requirements/graph/\w+/?$',req.path_info) is not None:
            m = re.match(r'/requirements/graph/(\w+)/?$', req.path_info)
            (graph,) = m.groups()

            cacheddata = self.cache.get_data(None, None, None, graph)
            if cacheddata:
                data = pickle.loads(cacheddata)
            else:
                # Determine which image generator to call
                canvas = None

                # Initialize requirement (to grab metric data)
                self.requirement = Requirement(self.env)

                # Dashboard Graphs
                if graph[0:12] == 'dash_overall':
                    canvas = self.dash_overall()
                elif graph[0:19] == 'component_req_count':
                    canvas = self.component_req_count()     
                elif graph[0:8] == 'dash_pie':
                    canvas = self.dash_pie()

                # Other Graphs
                elif graph[0:7] == 'entropy':
                    canvas = self.entropy_graph()

                # Extract the image into a string
                data = self._image_data(canvas)

                self.cache.set_data(None, None, None, graph, pickle.dumps(data))
 
        else:
            m = re.match(r'/requirement/graph/(\w+)-(\w+)-(\w+)/(\w+)/?$', req.path_info)
            (component, fp, object, graph) = m.groups()

            cacheddata = self.cache.get_data(component, fp, object, graph)
            if cacheddata:
                data = pickle.loads(cacheddata)
            else:
                # Initialize requirement (to grab metric data)
                self.requirement = Requirement(self.env, component, 
                                              Fp(self.env, name=fp)['id'], 
                                              Object(self.env, name=object)['id'])

                # Determine which image generator to call
                # *** Requirement specific graphs ***
                canvas = None
                if graph[0:3] == 'mls':
                    (mls, width) = graph.split('_')
                    data = self.most_least_cited( int( width ) )
                else:
                    if graph == 'test':
                        canvas = self.test()
                    elif graph[0:17] == 'changes_over_time':
                        ( garbage, garbage, garbage, secs_in_unit ) = graph.split('_')
                        canvas = self.changes_over_time(int(secs_in_unit))
                    elif graph[0:17] == 'tickets_over_time':
                        canvas = self.tickets_over_time()
                    # Extract the image into a string
                    data = self._image_data(canvas)

                self.cache.set_data(component, fp, object, graph, pickle.dumps(data))

        # Send reponse headers & the image string
        req.send_header('content-type', 'image/png')
        req.end_headers()
        req.write(data)

        # Return nothing, as we have done all the work
        return None

    def test(self):
        # Grab a blank, 100x100 image and the color palette
        fig = self._new_image((2,2))
        canvas = FigureCanvasAgg(fig)

        plot = fig.add_subplot(111)
        
        # Return our image
        return canvas

    def entropy_graph(self):
        """Creates a graph of entropy over time for requirements

        This returns an image with each requirement's entropy over
        time shown over the course of the project. If a project is old,
        or there are a lot of requirements, this can be a time consuming 
        process.
        """
        # Image generation prelude.
        fig = self._new_image((4,4))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_axes([0.1, 0.2, 0.85, 0.75])
        
        # Set up our time range from oldest time to now/newest.
        metric = RequirementMetric(Requirement(self.env))
        start_time = metric.model.get_timestamp_first_entity()
        end_time = metric.model.get_timestamp_latest_req_reqchange_milestone()
        current_time = int(time.time())
        if current_time > end_time:
            end_time = current_time
        
        #create the list of timestamps and make labels.
        times = []
        timestamp = end_time
        # We'll use two week increments for now to reduce 
        # delay while loading. 
        seconds_in_unit = (60 * 60 * 24 * 7 * 2)
        while timestamp > start_time:
            times.append(timestamp)
            timestamp -= seconds_in_unit        
        times.reverse()
        labels = [time.strftime("%b %d '%y",time.gmtime(timestamp)) \
                  for timestamp in times]

        # Create the coordinates lists for graphing
        coords = {}
        i = 0
        for timestamp in times:
            i = i + 1
            if timestamp > current_time:
                break;
            entropy_data = metric.entropy(timestamp)
            if entropy_data:
                _,_,_, req_entropies, _, _ = entropy_data
                for key in req_entropies.keys():
                    if not coords.has_key(key):
                        coords[key] = [(i, req_entropies[key])]
                    else:
                        coords[key].append((i, req_entropies[key]))

        biggest = []
        # Now we can actually graph them all
        for req in coords.keys():
            x = [x[0] for x in coords[req]]
            y = [y[1] for y in coords[req]]
            biggest.append(max(y))
            ax.plot(x,y,'k-')

        # Add the milestone markers.
        milestones = Requirement(self.env).get_milestones()
        x = []
        for (_, due) in milestones:
            if due == 0:
                continue
            x.append( float(due - times[0]) / float( seconds_in_unit))
        height = int(float(max(biggest)) + 1.5) 
        ax.vlines(x, 0, height,colors='r')
        # Label and shape the graph

        ax.set_xticks(range(0, len(times), 1))
        ax.set_xticklabels(labels)
        ax.set_xlim(0, len(times))
        setp(ax.get_xticklabels(),'rotation', 80, fontsize=6)
        ax.set_xlabel('Time in two-week increments', fontsize=6)
        
        ax.set_yticks(arange(0,height, 1))
        ax.set_ylim(0, height)
        setp(ax.get_yticklabels(), fontsize=6)
        ax.set_ylabel("Entropy", fontsize=6)

        return canvas

    def tickets_over_time(self):
        fig = self._new_image((3,3))
        canvas = FigureCanvasAgg(fig)
        when = now = int(time.time())
        month=['Jan','Feb','Mar','Apr','May','Jun',
        'Jul','Aug','Sep','Oct','Nov','Dec']
        numMonth=datetime.date.today().month
        dates={}        

        #rotates months to puts the current month 
        #as the last month in the array
        # FIXME: there has to be a simpler/clearer/faster
        # way to do this. (modulus and offsets?)
        for j in range(0,12):
            dates[j+1]=month[j]
        current=dates[numMonth]

        while(month[11]!=current):
            tempMonth=month[0]
            for i in range(0,11):
                month[i]=month[i+1]
            month[11]=tempMonth

        valEnh=[0,0,0,0,0,0,0,0,0,0,0,0]
        valDef=[0,0,0,0,0,0,0,0,0,0,0,0]
        valTas=[0,0,0,0,0,0,0,0,0,0,0,0]
       
        for i in range(11, -1, -1):
            metrics = self.requirement.get_tickets_over_time_metrics(when)
            for metric in metrics:
                type, count = metric
                if type == 'task':
                    valTas[i] = count
                elif type == 'defect':
                    valDef[i] = count
                elif type == 'enhancement':
                    valEnh[i] = count
                
            when = when - (3600 * 24 * 30)
        
        maxVal = max([max(valEnh), max(valDef), max(valTas)]) #the maximum value
        if maxVal == 0:
            # If there are no tickets ever associated, return blank
            # image instead of empty graph.
            return canvas
        # If we have usable data (tickets reference this requirement)
        # then we will graph them by month.
        ax=fig.add_subplot(111)
        num = 12 #the total number of values
        ind = arange(num)  # the x locations for the groups
        if maxVal > 20: # sets how often the y-axis increments
            inc = maxVal / 10
        else:
            inc=1
        width=.2 # sets the width of the bars
        
        maxY = maxVal + 5
        
        p1 = ax.bar(ind,valEnh, width=width, align='center',color='b')
        p2 = ax.bar(ind+width,valTas, width=width, align='center',color='g')
        p3 = ax.bar(ind+2*width,valDef, width=width, align='center',color='r')
        ax.set_xticks(ind+((3/2)*width))
        ax.set_xticklabels(month)
        ax.set_xlim(-width,len(ind))
        setp(ax.get_xticklabels(),'rotation', 45, fontsize=8)
        ax.set_yticks(arange(0,maxY,(inc)))
        ax.set_ylim(0,maxY)
        # Return 
        return canvas


    def component_req_count(self):
        """Show graph of how many requirements each component has.

        This returns a canvas drawn with matplotlib's backend graphics
        tools for display on the requirements dashboard. This graph
        list all components so they can be compared by their number
        of associated (active) requirements. This is one way of 
        describing a components relative 'size' and 'importance' in 
        relation to the other components.
        """
        cr_list = Requirement(self.env).get_component_req_count()
        count = len(cr_list)

        #heres a trick to cycle colors. Can add more base colors later.
        base_colors = ['b', 'g', 'r', 'c', 'm']
        colors = [base_colors[x % 5] for x in range(count)]

        fig = self._new_image((5,4))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_axes([0.08, 0.35, 0.9, 0.6])
        
        #extract the labels and values from cr_list
        labels = [x[0] for x in cr_list]
        y = [y[1] for y in cr_list]
        
        #establish height of y axis
        if max(y) == 0:
            height = 5
        elif max(y) % 5 == 0:
            height = max(y)
        else:
            height = max(y) + 5 - (max(y) % 5)

        
        #relative width of each bar
        width = 1 
        
        #scale vertically
        if height >= 20:
            inc = height/10
        else:
            inc = 1
        
        #position labels appropriately for horizontal scaling
        if count > 20:
            label_offset = 0
            if count > 30:
                rotation = 80
        else:
            label_offset = .5*width
            rotation = 60

        #set the horizontal points
        x = arange(0,count * width, width)

        #draw the graph
        p1 = ax.bar(x, y, width=width, color=colors)

        #set the x axis labels
        ax.set_xticks(x + label_offset)
        ax.set_xticklabels(labels)
        ax.set_xlim(0,count)
        setp(ax.get_xticklabels(), 'rotation',rotation,fontsize=6)

        #set the y axis labels
        ax.set_yticks(arange(0,height + 1, (inc)))
        ax.set_ylim(0,height)

        #we're done!
        return canvas


    def changes_over_time(self, seconds_in_unit=60):
        fig = self._new_image((3,3))
        canvas = FigureCanvasAgg(fig)

        (time_created, times_changed) = self.requirement.get_changes_metrics()
        
        ax = fig.add_subplot(111)
        
        # Obtain the timestamp of the first entity every created and treat
        # that as the projects start time since there is no available project
        # start time.
        proj_start_time = self.requirement.get_timestamp_first_entity()
        
        # Obtain the largest timestamp of either a milestone, requirement,
        # or a requirement change.
        most_recent_time = self.requirement.get_timestamp_latest_req_reqchange_milestone()
        
        # Obtain the current time.
        current_time = int(time.time())
        
        if (current_time > most_recent_time):
            most_recent_time = current_time
        
        # Obtain all the milestones and their associated due dates in
        # seconds since epoch.
        milestones = self.requirement.get_milestones()
        tot_horiz_units = int((most_recent_time - proj_start_time) / seconds_in_unit)
       
        # Initialize base variables
        height=10
        startY=0
        startX=time_created
        
        # Obtain the amount of time between each change made to the
        # requirement, and place them in an array
        valid_change_offsets = []
        prev_time = time_created
        for cur_time in times_changed:
            if (cur_time != prev_time):
                cur_horiz_unit_offset = int(((cur_time - prev_time) / seconds_in_unit))
                valid_change_offsets.append(cur_horiz_unit_offset)
                prev_time = cur_time
        
        # Append the amount of time between the last change and
        # the current time to the array
        cur_horiz_unit_offset = int(((current_time - prev_time) / seconds_in_unit))
        valid_change_offsets.append(cur_horiz_unit_offset)

        # Set the point where the requirement will begin graphing
        cur_x_pos = int((time_created - proj_start_time) / seconds_in_unit)
        
        height=1
        startX=0
        startY=0
        tot_horiz_units = ((most_recent_time - proj_start_time) / seconds_in_unit)
        
        #setup a blank template for y-axis increments
        graphSegments=[]
        for unit in range(0,tot_horiz_units):
            graphSegments.append(0)
	
        # Graph the requirement
        for cur_x_offset in valid_change_offsets:
            ax.broken_barh([ (cur_x_pos, cur_x_offset)] , (startY, height), facecolors='blue')
            cur_x_pos += cur_x_offset
            startY += height
            
        # Graph the milestones
        for (garbage, milestone_due) in milestones:
            if milestone_due == 0:
                continue
            milestone_x_pos = int((milestone_due - proj_start_time) / seconds_in_unit)
            ax.axvline(milestone_x_pos, color='r')
        last_date=milestone_due
	
	if last_date == 0:
            last_date = current_time
        
        # Set the limits and ticks of the graph
        x_tick_lines=[]
        for i in range(0, (tot_horiz_units + 1)):
            x_tick_lines.append(i)
        ax.set_xticks(x_tick_lines)
        ax.set(xticklabels=[])
        ax.set_yticks(arange(0,(startY+height),height))
        
        # Return our image
        return canvas
        
    def most_least_cited( self, width ):
        """This is the only function using gd, so we handle it more 
        directly for now.

        """
        image = gd.image((10*width, 10))
        image.filledRectangle((0,0),(10*width-1, 10), image.colorAllocate((255,0,0)))
        buffer = cStringIO.StringIO()
        image.writePng(buffer)
        data = buffer.getvalue()
        buffer.close()

        return data

    def dash_overall(self, seconds_in_unit=604800):
        fig = self._new_image((5,5))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        # Obtain the timestamp of the first entity every created and treat
        # that as the projects start time since there is no available project
        # start time.
        proj_start_time = self.requirement.get_timestamp_first_entity()
        start_time = proj_start_time 
        # Obtain the largest timestamp of either a milestone, requirement,
        # or a requirement change.
        most_recent_time = self.requirement.get_timestamp_latest_req_reqchange_milestone()
        
        # Obtain the current time.
        current_time = int(time.time())
        if (current_time > most_recent_time):
            most_recent_time = current_time
        #This is the bargraph portion
        #Initialize variables
        width = 1
        val = []       
        xTime = current_time
        endTime = proj_start_time #current_time - (31536000)
        
        #Get data
        while(xTime >= endTime):
            val.append(self.requirement.get_num_changes(endTime,endTime+seconds_in_unit))
            endTime+=seconds_in_unit
       

        ind = arange(len(val))  # the x locations for the groups
        
        #Create bargraph
        graphBar = ax.bar(ind,val,width=width, color='y')
        
        #This is the line graph portion
        #   this shows the number of active requirements
        #Initialize Variables
        #Get data
        #get the total number of requirements
        #       at each given time
        checktime=proj_start_time
        yValues=[]
        while checktime <= current_time+seconds_in_unit:
            yValues.append(self.requirement.get_num_req(checktime))
            checktime+=seconds_in_unit
        xValues=[]
        for _ in range(0,len(yValues)):
            xValues.append(_) 
        
        #Create Line graph
        lineGraph=ax.plot(xValues,yValues)                

        #create the list of timestamps and make labels.
        times = []
        timestamp = current_time
        # We'll use two week increments for now to reduce 
        # delay while loading. 
        while timestamp > start_time:
            times.append(timestamp)
            timestamp -= seconds_in_unit        
        times.reverse()
        labels = [time.strftime("%b %d '%y",time.gmtime(timestamp)) \
                  for timestamp in times]



        maxY=max(max(val),max(yValues))
        if maxY < 20:
            maxY+=5
        else:
            maxY=int(maxY*1.5)
        
        #This is the triangles portion
        #   this is the validation points
        #Initialize Variables
        #Get data
        valTimes=[]
        valTimes=self.requirement.get_val_times()
        valHeight=[]
        temp=[]

        if len(valTimes) is not 0:
            for elem in valTimes:
                valHeight.append(maxY*0.9)
                temp.append(int((elem - proj_start_time) / seconds_in_unit))
            valTimes=temp
            #Create triangles graph
            #use a scatterplot maybe and make each point for the graph be a triangle
            validationGraph=ax.scatter(valTimes,valHeight,color='g', marker='^', linewidth=5)


        #This is the milestones portion
        #Initialize Variables
        
        #Get data
        

        # Obtain all the milestones and their associated due dates in
        # seconds since epoch.
        milestones = self.requirement.get_milestones()
        tot_horiz_units = ((most_recent_time - proj_start_time) / seconds_in_unit)
        
        #Create line for milestones graph
        for (garbage, milestone_due) in milestones:
            if milestone_due == 0:
                continue
            milestone_x_pos = int((milestone_due - proj_start_time) / seconds_in_unit)
            #axvline(x=milestone_x_pos, xymin=0,ymax=100, color='r')
            milestoneBar = ax.bar(milestone_x_pos+0.5,maxY,width=(0),
                                    color='r', edgecolor='r')
        ax.set_xticklabels(labels)
        ax.set_xlim(0, len(times))
        setp(ax.get_xticklabels(),'rotation', 80, fontsize=6)
        
 
        #format the graph
        #ax.set_xlim(proj_start_time,most_recent_time)
        ax.set_ylim(0,maxY)
        #return the graph
        return canvas

    def dash_pie(self):
        fig = self._new_image((4,4))
        canvas = FigureCanvasAgg(fig)

        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])

        fracs = []

        vals = Requirement(self.env).get_type_req_tickets()
        
        total = 0
        for val in vals:
            total += val

        labels = []
        if total == 0:
            labels = ['None']
            fracs = [1]
        else:
            if vals[0] != 0:
                labels.append('Open')
                fracs.append(float(vals[0]) / float(total))
            if vals[1] != 0:
                labels.append('Closed')
                fracs.append(float(vals[1]) / float(total))
            if vals[2] != 0:
                labels.append('None')
                fracs.append(float(vals[2]) / float(total))

        labels = tuple(labels)

        ax.pie(fracs, labels=labels, autopct='%1.1f%%')

        return canvas

    def _new_image(self, (width,height)):
        # Return the blank figure
        return Figure(figsize=(width,height)) 

    def _image_data(self, canvas):
        # Create a receptor for output
        if canvas == None:
            return ''

        data_stream = cStringIO.StringIO()
        canvas.print_figure(data_stream)
        data_stream.seek(0)
        raw_data = data_stream.read()
        data_stream.close()

        # Return the image as a string
        return raw_data
