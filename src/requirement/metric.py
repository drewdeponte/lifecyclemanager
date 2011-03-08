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

from math import log
from trac.core import *
from model import Requirement

class RequirementMetric:

    def __init__(self, model):
        self.model = model

    def pmi(self, predicate=None, timestamp=None):
        pairings = self.model.get_pairings(predicate, None, timestamp)
        matrix = self.model.get_requirements_matrix(predicate, None, timestamp)
        numreqs = self.model.get_requirements_count(matrix)

        pmis = {}

        for (fp, obj) in pairings:
            rowsum = self.model.get_requirements_matrix_rowsum(matrix, fp)
            colsum = self.model.get_requirements_matrix_colsum(matrix, obj)

            if matrix[fp][obj] > 0 and rowsum > 0 and colsum > 0 and numreqs > 0:
                pmi = log(float(matrix[fp][obj] * numreqs) / float(rowsum * colsum), 2)
            else:
                pmi = 0

            pmis[(fp, obj)] = pmi

        return pmis
        

    def entropy(self, timestamp=None):
        """
        Information entropy metric.
        
        See accompanying document metrics.pdf
        """

        total_entropy = 0.0
        avg_entropy = 0.0
        component_entropies = {}
        fp_entropies = {}
        object_entropies = {}
        req_entropies = {}
        components, component_counts = self.model.get_components_metrics(None, timestamp)
        fps, fp_objects, fp_counts = self.model.get_fp_metrics(None, timestamp)
        objects, object_fps, object_counts = self.model.get_object_metrics(None, timestamp)
        requirements = self.model.get_requirements(None, timestamp)

        try:
            for component, reqs in requirements:
                component_entropies[component] = 0.0
            
                for fp, object in reqs:
                    fp_entropies[fp] = 0.0
                    for object_tmp in objects:
                        if fp in object_fps[object_tmp]:
                            prob = float(object_fps[object_tmp][fp]) / float(object_counts[object_tmp])
                            fp_entropies[fp] -= prob * log(prob, 2)
                    
                    object_entropies[object] = 0.0
                    for fp_tmp in fps:
                        if object in fp_objects[fp_tmp]:
                            prob = float(fp_objects[fp_tmp][object]) / float(fp_counts[fp_tmp])
                            object_entropies[object] -= prob * log(prob, 2)
                    
                    req_entropies[component,fp,object] = \
                        fp_entropies[fp] + object_entropies[object]
                    component_entropies[component] += \
                        req_entropies[component,fp,object]
                    
                total_entropy += component_entropies[component]
        
            avg_entropy = total_entropy / float(len(components))

        except ZeroDivisionError:
            return None
        
        return total_entropy, avg_entropy, component_entropies, \
               req_entropies, fp_entropies, object_entropies
