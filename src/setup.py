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



from setuptools import setup

PACKAGE = 'TracRequirements'
VERSION = '0.1'

setup(name=PACKAGE,
    license = "GNU GPL v2",
    version=VERSION,
    packages=['requirement'],
    author = "Lifecycle Manager Dev Team",
    author_email = "",
    url = "https://extsvn.cyph.org:8000/projects/trac_req_ext",
    description = """Tracks project requirements and their impact on development.""",
    long_description = """
    Lifecycle Manager is a full-featured collaborative project management
    environment seamlessly integrating project milestones, requirements, tickets,
    documentation, and artifact versioning in a multi-user concurrent
    service-oriented infrastructure. Lifecycle Manager may be used to record,
    predict, and evaluate performance of project features and teams, allowing
    better planning and management of development efforts ranging from simple to complex.
    """,
    entry_points={'trac.plugins':
                  [ 'RequirementComponent = requirement.requirement',
                    'ReportModule = requirement.report',
                    'ViewModule = requirement.view',
                    'RequirementModule = requirement.web_ui',
                    'NewrequirementModule = requirement.web_ui',
                    'NewrequirementAjaxModule = requirement.web_ui',
                    'CacheComponent = requirement.cache',
                    'RequirementGraphComponent = requirement.graph',
                    'RequirementSystem = requirement.api']},
    package_data={'requirement': ['upgrades/*.py',
                                  'templates/*.cs',
                                  'htdocs/images/*.jpg',
                                  'htdocs/css/*.css',
                                  'htdocs/javascript/*.js',
                                  'htdocs/timeline/*.js',
                                  'htdocs/timeline/*.css',
                                  'htdocs/timeline/images/*.png',
                                  'htdocs/timeline/images/*.gif'
                                  'htdocs/timeline/scripts/*.js',
                                  'htdocs/timeline/styles/*.css',
                                  'htdocs/timeline/scripts/l10n/cs/*.js',
                                  'htdocs/timeline/scripts/l10n/de/*.js',
                                  'htdocs/timeline/scripts/l10n/en/*.js',
                                  'htdocs/timeline/scripts/l10n/es/*.js',
                                  'htdocs/timeline/scripts/l10n/fr/*.js',
                                  'htdocs/timeline/scripts/l10n/it/*.js',
                                  'htdocs/timeline/scripts/l10n/ru/*.js',
                                  'htdocs/timeline/scripts/l10n/se/*.js',
                                  'htdocs/timeline/scripts/l10n/tr/*.js',
                                  'htdocs/timeline/scripts/l10n/vi/*.js',
                                  'htdocs/timeline/scripts/l10n/zh/*.js']},
)
