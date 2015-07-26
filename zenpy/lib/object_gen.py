import json
import os
import glob


__author__ = 'facetoe'


CLASS_TEMPLATE = """
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class %(class_name)s(BaseObject):
	def __init__(self, api=None):
		self.api = api
%(init_assignments)s
%(methods)s
%(properties)s
"""

PROPERTY_TEMPLATE = """
	@property
	def %(property_name)s(self):
		%(property_body)s

	@%(property_name)s.setter
	def %(property_name)s(self, value):
		self._%(property_name)s = value
		"""

PROPERTY_DATE_TEMPLATE = """if self.%(key)s:
			return dateutil.parser.parse(self.%(key)s)
			"""

PROPERTY_OBJECT_TEMPLATE = """if self.api and self.%(object_id)s:
			return self.api.get_%(object_type)s(self.%(object_id)s)"""


def get_properties(item):
	properties = ""
	for key in item:
		if not key == 'locale_id':
			if key.endswith('_id'):
				if key in ('assignee_id', 'submitter_id', 'requester_id'):
					object_type = 'user'
				elif key in ('forum_topic_id'):
					object_type = 'topic'
				else:
					object_type = key.replace('_id', '')
				property_name = key.replace('_id', '')
				object_id = key
				property_body = PROPERTY_OBJECT_TEMPLATE % locals()
				properties += PROPERTY_TEMPLATE % locals()
			elif key.endswith('_at'):
				object_type = key.replace('_at', '')
				property_name = key.replace('_at', '')
				property_body = PROPERTY_DATE_TEMPLATE % locals()
				properties += PROPERTY_TEMPLATE % locals()
	return properties

def get_methods(item, class_name):
	if class_name == 'Result':
		return """
	@property
	def results(self):
		return self.api.result_generator(vars(self))

	def __iter__(self):
		if self.api:
			return self.results

			"""
	else:
		return ""

def get_init_section(item):
	init = ""
	for key in item:
		if key == 'results':
			key = '_results'

		if key.endswith('_id'):
			init += "\t\tself._%s = None\n" % key.replace('_id', '')


		init += "\t\tself.%s = None\n" % key
	return init

def generate_all(specification_path, out_path):
	for file_path in glob.glob(os.path.join(specification_path, '*.json')):
		class_name = os.path.basename(os.path.splitext(file_path)[0]).capitalize()
		class_code = generate_class(file_path, class_name)
		with open(os.path.join(out_path, "%s.py" % class_name.lower()), 'w+') as out_file:
			out_file.write(class_code)


def generate_class(spec_path, class_name):
	object_json = json.load(open(spec_path, 'r'))
	init_assignments = get_init_section(object_json)
	properties = get_properties(object_json)
	methods = get_methods(object_json, class_name)
	return CLASS_TEMPLATE % locals()


spec_path = '/home/facetoe/git/zenpyreloaded/zenpy/specification'
out_path = '/home/facetoe/git/zenpyreloaded/zenpy/lib/objects'


generate_all(spec_path, out_path)