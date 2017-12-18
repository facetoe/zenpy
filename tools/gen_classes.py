#!/usr/bin/env python

import glob
import json
import re
import sys
from multiprocessing.pool import Pool
from optparse import OptionParser

import os
from yapf.yapflib.yapf_api import FormatCode

__author__ = 'facetoe'
from jinja2 import Template


class TemplateObject(object):
    OBJECT_TEMPLATE = None

    def render(self):
        return Template(self.OBJECT_TEMPLATE).render(object=self)


class Class(TemplateObject):
    OBJECT_TEMPLATE = """
class {{object.name}}(BaseObject):
        {{-object.init.render()-}}
        {{-object.properties.render()-}}

"""

    def __init__(self, name, _json, doc_json):
        attributes = []
        object_name = to_snake_case(name).lower() + 's'

        for attr_name, attr in iter(sorted(_json.items())):
            attribute = Attribute(attr_name=attr_name, attr_value=attr)
            if object_name in doc_json and attr_name in doc_json[object_name]:
                doc_strings = []
                attr_docs = doc_json[object_name][attr_name]
                if attr_docs['type'] not in ('string', 'boolean', 'date', 'integer', 'array', 'object'):
                    attr_docs['type'] = ':class:`%s`' % attr_docs['type']

                for key, value in sorted(attr_docs.items()):
                    doc_strings.append("%s: %s" % (key.capitalize(), value.replace('*', '')))
                attribute.attr_docs = doc_strings
            attributes.append(attribute)

        attributes = sorted(attributes, key=lambda x: x.attr_name)
        self.name = name
        self.init = Init(attributes)
        self.properties = Properties(attributes)


class Init(TemplateObject):
    OBJECT_TEMPLATE = """
    {% if object.init_params %}
    def __init__(self, api=None, {{ object.init_params }}, **kwargs):
    {% else %}
    def __init__(self, api=None, **kwargs):
    {% endif %}
        self.api = api
        {% for attr in object.attributes -%}
        {% if attr.attr_docs and attr.attr_name %}
        {% for docline in attr.attr_docs %}
        # {{ docline-}}
        {% endfor %}
        {% endif -%}
        {% if attr.attr_name and not attr.attr_name.startswith('_') -%}
        self.{{attr.attr_name}} = {{attr.attr_name}}
        {% elif attr.attr_name %}
        self.{{attr.attr_name}} = None
        {% endif -%}
        {% endfor %}
        for key, value in kwargs.items():
            setattr(self, key, value)
    """

    def __init__(self, attributes):
        self.attributes = attributes
        self.init_params = ", ".join(
            ["{}=None".format(a.attr_name)
             for a in attributes
             if not a.attr_name.startswith('_') and a.attr_name])
        self.attributes = attributes


class Properties(TemplateObject):
    OBJECT_TEMPLATE = """
    {%- for prop in object.properties -%}
    {{- prop.render() -}}
    {% endfor %}
    """

    def __init__(self, attributes):
        self.properties = [Property(a) for a in attributes]


class Property(TemplateObject):
    OBJECT_TEMPLATE = """
    {%- if object.attribute.is_property -%}
    @property
    def {{object.attribute.object_name}}(self):
        {% if object.attribute.attr_docs -%}
        \"\"\"
        |  {{ object.attribute.attr_docs[0] }}
        \"\"\"
        {%- endif -%}
        {{- object.prop_body -}}

    @{{object.attribute.object_name}}.setter
    def {{object.attribute.object_name}}(self, {{object.attribute.object_name}}):
        {{- object.prop_setter_body -}}
    {%- endif -%}

    """

    DATE_TEMPLATE = """
        if self.{{object.attribute.key}}:
            return dateutil.parser.parse(self.{{object.attribute.key}})
    """

    PROPERTY_TEMPLATE = """
        if self.api and self.{{object.attribute.attr_name}}:
            return self.api._get_{{object.attribute.object_type}}(self.{{object.attribute.attr_name}})
    """

    SETTER_TEMPLATE_ASSIGN = """
            if {{object.attribute.object_name}}:
                self.{{object.attribute.attr_name}} = {{object.attribute.attr_assignment}}
                self._{{object.attribute.object_name}} = {{object.attribute.object_name}}
    """

    SETTER_TEMPLATE_DEFAULT = """
            if {{object.attribute.object_name}}:
                self.{{object.attribute.attr_name}} = {{object.attribute.object_name}}
    """

    def __init__(self, attribute):
        self.attribute = attribute
        self.prop_name = attribute.object_name
        self.prop_body = self.get_prop_body(attribute)
        self.prop_setter_body = self.get_prop_setter_body(attribute)

    def get_prop_body(self, attribute):
        if attribute.object_type == 'date':
            template = self.DATE_TEMPLATE
        else:
            template = self.PROPERTY_TEMPLATE

        return Template(template).render(object=self, trim_blocks=True)

    def get_prop_setter_body(self, attribute):
        if attribute.attr_assignment:
            template = self.SETTER_TEMPLATE_ASSIGN
        else:
            template = self.SETTER_TEMPLATE_DEFAULT
        return Template(template).render(object=self, trim_blocks=True)


class Attribute(object):
    def __init__(self, attr_name, attr_value, attr_docs=None):
        if attr_name == 'from':
            attr_name = 'from_'

        self.key = '_{}'.format(attr_name) if attr_name.endswith('timestamp') else attr_name
        self.attr_docs = attr_docs
        self.object_type = self.get_object_type(attr_name)
        self.object_name = self.get_object_name(attr_name, attr_value)
        self.attr_name = self.get_attr_name(self.object_name, attr_name, attr_value)
        self.attr_assignment = self.get_attr_assignment(self.object_name, self.object_type, attr_name)
        self.is_property = self.get_is_property(attr_name)

    def get_object_type(self, attr_name):
        if attr_name in ('assignee_id', 'submitter_id', 'requester_id',
                         'author_id', 'updater_id', 'recipient_id',
                         'created_by_id', 'updated_by_id'):
            object_type = 'user'
        elif attr_name in ('photo',):
            object_type = 'attachment'
        elif attr_name.endswith('time_in_minutes'):
            object_type = 'ticket_metric_item'
        elif attr_name in ('recipients', 'collaborator_ids'):
            object_type = 'users'
        elif attr_name in ('forum_topic_id',):
            object_type = 'topic'
        elif attr_name.endswith('_at') or attr_name.endswith('timestamp'):
            object_type = 'date'
        else:
            object_type = attr_name.replace('_id', '')
        return object_type

    def get_attr_name(self, object_name, attr_name, attr_value):
        should_modify = attr_name.endswith('timestamp')
        if should_modify:
            return "_%s" % attr_name
        else:
            return attr_name

    def get_attr_assignment(self, object_name, object_type, key):
        if object_type != key and object_type != 'date' and key.endswith('_id'):
            return '%s.id' % object_name
        elif key.endswith('_ids'):
            return '[o.id for o in %(object_name)s]' % locals()

    def get_object_name(self, attr_name, attr_value):
        if attr_name == 'locale_id':
            return attr_name
        for replacement in ('_at', '_id'):
            if attr_name.endswith(replacement):
                return attr_name.replace(replacement, '')
            elif attr_name.endswith('_ids'):
                return "%ss" % attr_name.replace('_ids', '')
        return attr_name

    def get_is_property(self, attr_name):
        if attr_name in ('locale_id', 'external_id', 'graph_object_id',
                         'agreement_id', 'content_id', 'item_id', 'source_id', 'community_id'):
            return False
        if attr_name.endswith('_id') or attr_name.endswith('_ids'):
            return True
        elif self.object_type == 'date':
            return True
        return False

    def __str__(self):
        return "[is_prop=%(is_property)s, " \
               "key=%(key)s, " \
               "obj_type=%(object_type)s, " \
               "obj_name=%(object_name)s, " \
               "attr_name=%(attr_name)s, " \
               "assn=%(attr_assignment)s]" \
               "attr_doc=%(attr_docs)s " % self.__dict__

    def __repr__(self):
        return self.__str__()


def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


BASE_CLASS = '''
######################################################################
#  Do not modify, these classes are autogenerated by gen_classes.py  #
######################################################################

import dateutil.parser

class BaseObject(object):
    """
    Base for all Zenpy objects. Keeps track of which attributes have been modified.
    """

    def __new__(cls, *args, **kwargs):
        instance = super(BaseObject, cls).__new__(cls)
        instance.__dict__['_dirty_attributes'] = set()
        return instance

    def __setattr__(self, key, value):
        self.__dict__['_dirty_attributes'].add(key)
        self.__dict__[key] = value

    def _clean_dirty(self):
        self.__dict__['_dirty_attributes'].clear()

    def to_dict(self, serialize=False):
        copy_dict = self.__dict__.copy()
        for key in list(copy_dict):
            if serialize and key == 'id':
                continue
            elif copy_dict[key] is None or key in ('api', '_dirty_attributes'):
                del copy_dict[key]
            elif serialize and key not in self._dirty_attributes:
                del copy_dict[key]
            elif key.startswith('_'):
                copy_dict[key[1:]] = copy_dict[key]
                del copy_dict[key]
        return copy_dict

    def __repr__(self):
        class_name = type(self).__name__
        if class_name in ('UserField',):
            return "{}()".format(class_name)

        def formatted(item):
            return item if (isinstance(item, int) or item is None) else "'{}'".format(item)

        for identifier in ('id', 'token', 'key', 'name', 'account_key'):
            if hasattr(self, identifier):
                return "{}({}={})".format(class_name, identifier, formatted(getattr(self, identifier)))
        return "{}()".format(class_name)
'''

parser = OptionParser()

parser.add_option("--spec-path", "-s", dest="spec_path",
                  help="Location of .json spec", metavar="SPEC_PATH")
parser.add_option("--doc-json", "-d", dest="doc_json_path",
                  help="Location of .json documentation file", metavar="DOC_JSON")
parser.add_option("--out-path", "-o", dest="out_path",
                  help="Where to put generated classes",
                  metavar="OUT_PATH",
                  default=os.getcwd())

(options, args) = parser.parse_args()

if not options.spec_path:
    print("--spec-path is required!")
    sys.exit()
elif not os.path.isdir(options.spec_path):
    print("--spec-path must be a directory!")
    sys.exit()
elif not options.doc_json_path:
    print("--doc-json is required!")
    sys.exit()

doc_json = json.load(open(options.doc_json_path))


def process_file(path):
    class_name = os.path.basename(os.path.splitext(path)[0]).capitalize()
    class_name = "".join([w.capitalize() for w in class_name.split('_')])
    with open(path) as f:
        class_code = Class(class_name, json.load(f), doc_json).render()
    print("Processed: %s -> %s" % (os.path.basename(path), class_name))
    return class_code


def process_specification_directory(glob_pattern, outfile_name, write_baseclass=True):
    with open(os.path.join(options.out_path, outfile_name), 'w+') as out_file:
        paths = [p for p in glob.glob(os.path.join(options.spec_path, glob_pattern))]
        classes = list()
        with Pool() as pool:
            classes.extend(pool.map(process_file, paths))
        print("Formatting...")
        formatted_code = FormatCode("\n".join(sorted(classes)))[0]
        if write_baseclass:
            header = BASE_CLASS
        else:
            header = "from zenpy.lib.api_objects import BaseObject\nimport dateutil.parser"

        out_file.write("\n\n\n".join((header, formatted_code)))


process_specification_directory('zendesk/*.json', 'api_objects/__init__.py')
process_specification_directory('chat/*.json', 'api_objects/chat_objects.py', write_baseclass=False)
process_specification_directory('help_centre/*.json', 'api_objects/help_centre_objects.py', write_baseclass=False)
