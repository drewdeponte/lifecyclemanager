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


SRC = setup.py $(wildcard requirement/*.py) $(wildcard requirement/htdocs/css/*.css) \
	$(wildcard requirement/templates/*.cs) $(wildcard requirement/tests/*.py) \
	$(wildcard requirement/htdocs/javascript/*.js) $(wildcard requirement/upgrades/*.py)

egg: dist/$(EGG)

dist/$(EGG): $(SRC)
	python setup.py bdist_egg

clean: cleanpyc
	rm -rf ../${DIST_PATH}
	rm -rf build
	rm -rf TracRequirements.egg-info

cleanpyc:
	rm -rf requirement/*.pyc
	rm -rf requirement/tests/*.pyc

