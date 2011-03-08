
DOCS_EGG = dist/Docs-0.1-py$(PYVERSION).egg

SRC := setup.py $(wildcard docs/*.py) $(wildcard docs/htdocs/css/*.css) $(wildcard docs/templates/*.cs)

egg: $(DOCS_EGG)

$(DOCS_EGG): $(SRC)
	python setup.py bdist_egg

install: $(DOCS_EGG)
	cp $(DOCS_EGG) ../../../$(TRACENV_PATH)/plugins