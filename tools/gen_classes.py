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

        self.key = '_{}'.format(attr_name) if attr_name == 'timestamp' else attr_name
        self.attr_docs = attr_docs
        self.object_type = self.get_object_type(attr_name)
        self.object_name = self.get_object_name(attr_name, attr_value)
        self.attr_name = self.get_attr_name(self.object_name, attr_name, attr_value)
        self.attr_assignment = self.get_attr_assignment(self.object_name, self.object_type, attr_name)
        self.is_property = self.get_is_property(attr_name, attr_value)

    def get_object_type(self, attr_name):
        if attr_name in ('assignee_id', 'submitter_id', 'requester_id', 'author_id', 'updater_id'):
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
        should_modify = attr_name.endswith('timestamp') \
                        or (isinstance(attr_value, dict) and object_name not in ('ticket', 'audit')) \
                        or (object_name == attr_name and isinstance(attr_value, list) and attr_name not in ('tags',))
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
        for replacement in ('_at', '_id'):
            if attr_name.endswith(replacement):
                return attr_name.replace(replacement, '')
            elif attr_name.endswith('_ids'):
                return "%ss" % attr_name.replace('_ids', '')
        return attr_name

    def get_is_property(self, attr_name, attr_value):
        not_properties = (
            'author',
            'to',
            'from',
            'locale',
            'locale_id',
            'tags',
            'domain_names',
            'ticket',
            'audit',
            'conditions',
            'all',
            'any',
            'execution',
            'columns',
            # ChatApi
            'agent_names',
            'count',
            'response_time',
            'session',
            'visitor',
            'agent_names',
            'count',
            'definition',
            'actions',
            'condition',
            'billing',
            'plan',
            'agent',
            'roles',
            'department',
            'members'
        )
        if attr_name in not_properties:
            return False
        elif any([isinstance(attr_value, t) for t in (dict, list)]):
            return True
        elif self.object_type == 'date':
            return True
        elif attr_name.endswith('_id') and isinstance(attr_value, int):
            return True
        else:
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


BASE_CLASSS = """
######################################################################
#  Do not modify, these classes are autogenerated by gen_classes.py  #
######################################################################

import dateutil.parser

class BaseObject(object):
    def to_dict(self):
        copy_dict = self.__dict__.copy()
        for key in list(copy_dict.keys()):
            if copy_dict[key] is None or key == 'api':
                del copy_dict[key]
                continue

            if key.startswith('_'):
                copy_dict[key[1:]] = copy_dict[key]
                del copy_dict[key]
        return copy_dict

    def __repr__(self):
        def stringify(item):
            return item if isinstance(item, int) else "'{}'".format(item)
        if hasattr(self, 'id'):
            return "[%s(id=%s)]" % (self.__class__.__name__, stringify(self.id))
        elif hasattr(self, 'token'):
            return "[%s(token='%s')]" % (self.__class__.__name__, self.token)
        elif hasattr(self, 'key'):
            return "[%s(key='%s')]" % (self.__class__.__name__, self.key)
        elif hasattr(self, 'name'):
            return "[%s(name='%s')]" % (self.__class__.__name__, self.name)
        elif hasattr(self, 'account_key'):
            return "[%s(account_key='%s')]" % (self.__class__.__name__, self.account_key)
        else:
            return "[%s()]" % self.__class__.__name__
"""

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
        if write_baseclass:
            classes = [BASE_CLASSS]
        else:
            classes = ["from zenpy.lib.api_objects import BaseObject"]

        paths = [p for p in glob.glob(os.path.join(options.spec_path, glob_pattern))]
        with Pool() as pool:
            classes.extend(pool.map(process_file, paths))
        print("Formatting...")
        formatted_code = FormatCode("\n".join(classes))[0]
        out_file.write(formatted_code)


process_specification_directory('zendesk/*.json', 'api_objects/__init__.py')
process_specification_directory('chat/*.json', 'api_objects/chat_objects.py')
