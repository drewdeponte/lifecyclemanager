
USERLOG_EGG = dist/UserLog-0.1-py$(PYVERSION).egg

SRC := setup.py $(wildcard userlog/*.py) $(wildcard userlog/htdocs/css/*.css) $(wildcard userlog/templates/*.cs)

egg: $(USERLOG_EGG)

$(USERLOG_EGG): $(SRC)
	python setup.py bdist_egg

install: $(USERLOG_EGG)
	cp $(USERLOG_EGG) ../../../$(TRACENV_PATH)/plugins