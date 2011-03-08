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

from trac.requirement.api import RequirementSystem
from trac.requirement.cache import RequirementCacheSystem
from trac.test import EnvironmentStub, Mock

import unittest


class RequirementSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.requirement_system = RequirementSystem(self.env)

    def test_custom_field_text(self):
        self.env.config.set('requirement-custom', 'test', 'text')
        self.env.config.set('requirement-custom', 'test.label', 'Test')
        self.env.config.set('requirement-custom', 'test.value', 'Foo bar')
        fields = RequirementSystem(self.env).get_custom_fields()
        self.assertEqual({'name': 'test', 'type': 'text', 'label': 'Test',
                          'value': 'Foo bar', 'order': 0},
                         fields[0])

    def test_custom_field_select(self):
        self.env.config.set('requirement-custom', 'test', 'select')
        self.env.config.set('requirement-custom', 'test.label', 'Test')
        self.env.config.set('requirement-custom', 'test.value', '1')
        self.env.config.set('requirement-custom', 'test.options', 'option1|option2')
        fields = RequirementSystem(self.env).get_custom_fields()
        self.assertEqual({'name': 'test', 'type': 'select', 'label': 'Test',
                          'value': '1', 'options': ['option1', 'option2'],
                          'order': 0},
                         fields[0])

    def test_custom_field_optional_select(self):
        self.env.config.set('requirement-custom', 'test', 'select')
        self.env.config.set('requirement-custom', 'test.label', 'Test')
        self.env.config.set('requirement-custom', 'test.value', '1')
        self.env.config.set('requirement-custom', 'test.options', '|option1|option2')
        fields = RequirementSystem(self.env).get_custom_fields()
        self.assertEqual({'name': 'test', 'type': 'select', 'label': 'Test',
                          'value': '1', 'options': ['option1', 'option2'],
                          'order': 0, 'optional': True},
                         fields[0])

    def test_custom_field_textarea(self):
        self.env.config.set('requirement-custom', 'test', 'textarea')
        self.env.config.set('requirement-custom', 'test.label', 'Test')
        self.env.config.set('requirement-custom', 'test.value', 'Foo bar')
        self.env.config.set('requirement-custom', 'test.cols', '60')
        self.env.config.set('requirement-custom', 'test.rows', '4')
        fields = RequirementSystem(self.env).get_custom_fields()
        self.assertEqual({'name': 'test', 'type': 'textarea', 'label': 'Test',
                          'value': 'Foo bar', 'width': 60, 'height': 4,
                          'order': 0},
                         fields[0])

    def test_custom_field_order(self):
        self.env.config.set('requirement-custom', 'test1', 'text')
        self.env.config.set('requirement-custom', 'test1.order', '2')
        self.env.config.set('requirement-custom', 'test2', 'text')
        self.env.config.set('requirement-custom', 'test2.order', '1')
        fields = RequirementSystem(self.env).get_custom_fields()
        self.assertEqual('test2', fields[0]['name'])
        self.assertEqual('test1', fields[1]['name'])

def suite():
    suite = unittest.makeSuite(RequirementSystemTestCase, 'test')

    return suite

if __name__ == '__main__':
    unittest.main()
