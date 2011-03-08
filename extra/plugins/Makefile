
plugins: docs userlog

.PHONY : docs userlog
docs:
	$(MAKE) -C docs egg

userlog:
	$(MAKE) -C userlog egg

install: docs
	$(MAKE) -C docs install
	$(MAKE) -C userlog install