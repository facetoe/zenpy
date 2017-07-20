import inspect
from collections import namedtuple

from docutils.nodes import paragraph, container
from docutils.parsers.rst import Directive
from docutils.statemachine import StringList

from zenpy import Api, Zenpy
from zenpy.lib.endpoint import PrimaryEndpoint, SecondaryEndpoint

__author__ = 'facetoe'

ClassInfo = namedtuple('ClassInfo', ['name', 'signature', 'docstring', 'methods', 'method_count'])
MethodInfo = namedtuple('MethodInfo', ['signature', 'docstring'])


def get_api_class_info(obj):
    ignore_methods = [x[0] for x in inspect.getmembers(Api)]

    def valid_method(m):
        return inspect.ismethod(m) \
               and not m.__name__.startswith('_') \
               and m.__name__ not in ignore_methods

    results = list()
    for name, api in inspect.getmembers(obj, lambda x: issubclass(x.__class__, Api)):
        signature = "%s%s" % (name, inspect.signature(getattr(api, '__call__')))
        docstring = api.endpoint.__doc__ if not any(
            (isinstance(api.endpoint, o) for o in [PrimaryEndpoint, SecondaryEndpoint])) else None
        methods = list()

        for method_name, method in inspect.getmembers(api, valid_method):
            method_signature = method_name + str(inspect.signature(method))
            methods.append(MethodInfo(method_signature, method.__doc__))

        class_info = ClassInfo(name, signature, docstring, methods, len(methods))
        results.append(class_info)

    return sorted(results, key=lambda c: c.method_count, reverse=True)


class CacheDoc(Directive):
    required_arguments = 0
    has_content = True

    def run(self):
        zenpy = Zenpy.__new__(Zenpy)
        zenpy.__init__(zenpy, ' ', ' ')

        node_list = []
        cache_node = container()
        cache_sections = self.generate_cache_sections(zenpy)
        for cache_section in cache_sections:
            node = paragraph()
            self.state.nested_parse(StringList(cache_section.split('\n')), 0, node)
            node_list.append(node)
        node_list.append(cache_node)
        return node_list

    def generate_cache_sections(self, zenpy):
        cache_sections = []
        for method_tuple in inspect.getmembers(zenpy, lambda x: inspect.ismethod(x)):
            method_name, method = method_tuple
            if method_name.startswith('_'):
                continue
            output = '.. py:method:: %s%s\n' % (method_name, inspect.signature(method))
            output += '   %s\n\n' % method.__doc__
            cache_sections.append(output)
        return cache_sections


class ApiDoc(Directive):
    required_arguments = 0
    has_content = True
    ignore_methods = [x[0] for x in inspect.getmembers(Api)]

    def run(self):
        zenpy = Zenpy.__new__(Zenpy)
        zenpy.__init__(zenpy, ' ', ' ')

        node_list = []
        doc_sections = self.generate_sections(zenpy)

        output = '.. py:class:: Zenpy%s\n\n' % inspect.signature(zenpy.__class__)
        output += '  %s' % zenpy.__doc__

        node = container()
        self.state.nested_parse(StringList(output.split('\n')), 0, node)
        node_list.append(node)

        for doc_section in doc_sections:
            node = paragraph()
            self.state.nested_parse(StringList(doc_section.split('\n')), 0, node)
            node_list.append(node)
        return node_list

    def generate_sections(self, zenpy):
        doc_sections = []
        for class_info in get_api_class_info(zenpy):
            member_docs = "   .. py:method:: %s\n\n" % class_info.signature
            if class_info.docstring:
                member_docs += "      %s\n\n" % class_info.docstring

            for method in class_info.methods:
                if method.docstring:
                    member_docs += "      .. py:method:: %s\n\n" % method.signature
                    member_docs += "         %s\n\n" % method.docstring
            doc_sections.append(member_docs)

        return doc_sections


def setup(app):
    app.add_directive("apidoc", ApiDoc)
    app.add_directive('cachedoc', CacheDoc)
