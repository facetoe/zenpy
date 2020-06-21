all:

PYTHON ?= python3
PYTHON_SOURCE_DIRS = zenpy/ tests/
PYTEST_ARG ?= -v

clean:
	$(RM) -r *.egg-info/ dist/
	$(RM) ../zenpy* test-*.xml

reformat:
	black $(PYTHON_SOURCE_DIRS)

unittest:
	nosetests -v --stop

pylint:
	pylint --rcfile .pylintrc $(PYTHON_SOURCE_DIRS)

flake8:
	$(PYTHON) -m flake8 --exclude=__init__.py --ignore=E722 --max-line-len=125 $(PYTHON_SOURCE_DIRS)

lint: pylint flake8

