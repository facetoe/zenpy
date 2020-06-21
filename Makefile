all:

PYTHON ?= python3
PYTHON_SOURCE_DIRS = zenpy/ tests/

clean:
	$(RM) -r *.egg-info/ dist/

reformat:
	black $(PYTHON_SOURCE_DIRS)

unittest:
	nosetests -v --stop


