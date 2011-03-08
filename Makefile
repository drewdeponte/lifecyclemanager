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

export PROGNAME = TracRequirements
export VERSION = 0.1
export PYVERSION = $(shell python pyversion.py)

export SRC_PATH = src
export DOC_PATH = doc
export TEST_PATH = testenv

export EGG = $(PROGNAME)-$(VERSION)-py$(PYVERSION).egg
export DIST_PATH = ${SRC_PATH}/dist
export EGG_PATH = ${DIST_PATH}/${EGG}

export SERVER_PORT = 8000

export PROJECT_TEST_NAME = lcmtest

export SVN_ROOT = ${TEST_PATH}/test_svn_repos
export SVN_PATH = ${SVN_ROOT}/${PROJECT_TEST_NAME}

export TRACENV_TEST_PATH = ${TEST_PATH}/test_trac_envs
export TRACENV_PATH = ${TRACENV_TEST_PATH}/${PROJECT_TEST_NAME}
export TRACAUTH_PATH = --basic-auth lcmtest,${TEST_PATH}/users.htdigest,

export TRACSRC_PATH = ${TEST_PATH}/trac-0.10.4
export TRACSRC_TAR = ${TRACSRC_PATH}.tar.gz

export TEMPLATE_PATH = ${TRACSRC_PATH}/templates



all: egg tests test-server

egg:
	$(MAKE) -C ${SRC_PATH} egg

docs:
	$(MAKE) -C ${DOC_PATH}/src pdfs

alldocs:
	$(MAKE) -C ${DOC_PATH}/src pdfs htmls

tests: egg tracsrc unittests

alltests: egg tracsrc allunittests

test-server: egg cleanenv svnenv tracsrc tracenv test-install tracup server-restart

svnenv:
	mkdir -p ${SVN_ROOT}
	svnadmin create ${SVN_PATH}

tracsrc: cleansrc
	tar -C ${TEST_PATH} -xzf ${TRACSRC_TAR}
	cd ${TRACSRC_PATH}/trac && ln -sf ../../../${SRC_PATH}/requirement

tracenv:
	mkdir -p ${TRACENV_PATH}
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} initenv \
		${PROJECT_TEST_NAME} sqlite:db/trac.db svn ${SVN_PATH} ${TEMPLATE_PATH}

tracup:
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} upgrade
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add admin TRAC_ADMIN
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add reqview REQUIREMENT_VIEW
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add reqappend REQUIREMENT_APPEND
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add reqmodify REQUIREMENT_MODIFY
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add reqcreate REQUIREMENT_CREATE
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add reqdisenable REQUIREMENT_DISENABLE
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add reqadmin REQUIREMENT_ADMIN
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add anonymous REQUIREMENT_DISENABLE
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add anonymous REQUIREMENT_VIEW
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add anonymous REQUIREMENT_APPEND
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add anonymous REQUIREMENT_MODIFY
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add anonymous REQUIREMENT_CREATE
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} permission add anonymous REQUIREMENT_ADMIN
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} component add component3 admin
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} component add component4 admin
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/trac-admin ${TRACENV_PATH} component add jellyfish admin
	cp ${TEST_PATH}/trac.ini ${TRACENV_PATH}/conf/

test-install:
	cp ${EGG_PATH} ${TRACENV_PATH}/plugins

server-restart:
	-cat ${TEST_PATH}/tracd.pid | xargs kill
	TRAC_ENV="${TRACENV_PATH}" PYTHONPATH="${PYTHONPATH}:${TRACSRC_PATH}" ${TRACSRC_PATH}/scripts/tracd \
		--port ${SERVER_PORT} ${TRACAUTH_PATH} -d --pidfile=${TEST_PATH}/tracd.pid ${TRACENV_PATH}

unittests:
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" python ${TRACSRC_PATH}/trac/requirement/test.py

allunittests:
	PYTHONPATH="$$PYTHONPATH:${TRACSRC_PATH}" python ${TRACSRC_PATH}/trac/test.py

clean: cleanenv cleansrc
	$(MAKE) -C ${SRC_PATH} clean
	$(MAKE) -C ${DOC_PATH}/src clean

cleanenv:
	rm -rf ${TRACENV_TEST_PATH}
	rm -rf ${SVN_ROOT}

cleansrc:
	rm -rf ${TRACSRC_PATH}

dist: egg docs
	tar -c -f $(PROGNAME)-$(VERSION).tar AUTHORS INSTALL NEWS README TODO -C ${DIST_PATH} ${EGG}
	ls -1 ${DOC_PATH}/pdf/*.pdf | perl -pe 's!${DOC_PATH}/!!' | tar -u -f $(PROGNAME)-$(VERSION).tar -C ${DOC_PATH} -T -
	gzip -f $(PROGNAME)-$(VERSION).tar


.PHONY : extra
extra:
	$(MAKE) -C extra extra

extra-install: extra
	$(MAKE) -C extra install
	$(MAKE) server-restart


doxygen: tracsrc
	$(MAKE) -C ${DOC_PATH}/doxygen doxygen
