
OUTPUT_DIRECTORY=.
STRIP_FROM_PATH=../../testenv/trac-0.10.4
INPUT=../../testenv/trac-0.10.4

all:

doxygen:
	rm -Rf lifecycle_manager-api-html lifecycle_manager-api-latex
	perl -pe 's!__OUTPUT_DIRECTORY__!${OUTPUT_DIRECTORY}!g; s!__STRIP_FROM_PATH__!${STRIP_FROM_PATH}!g; s!__INPUT__!${INPUT}!g;' Doxyfile | doxygen -
	$(MAKE) -C lifecycle_manager-api-latex
	cp lifecycle_manager-api-latex/refman.pdf lifecycle_manager-api.pdf
	tar zcf lifecycle_manager-api-html.tar.gz lifecycle_manager-api-html