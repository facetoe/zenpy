all:

PYTHON ?= python3
PYTHON_SOURCE_DIRS = zenpy/ tests/

clean:
	$(RM) -r *.egg-info/ dist/

reformat:
	black $(PYTHON_SOURCE_DIRS)

unittest:
	nosetests -v --stop


gen_classes:
	cd tools && ./gen_classes.py --spec-path ../specification --doc-json doc_dict.json -o ../zenpy/lib/
