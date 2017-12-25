from zenpy.lib.proxy import ProxyDict, ProxyList
from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib import api_objects
from zenpy.lib.api_objects import BaseObject
from zenpy.lib.api_objects import chat_objects, help_centre_objects


class TestProperties(ZenpyApiTestCase):
    __test__ = True

    def setUp(self):
        # Could pick any api class, the methods are in the Api class which they all subclass from.
        self.mock_api = self.zenpy_client.tickets
        self.mock_api._call_api = mock_api_call

    def test_zendesk_object_properties_implemented(self):
        self.check_properties_are_implemented(api_objects)

    def test_chat_object_properties_implemented(self):
        self.check_properties_are_implemented(chat_objects)

    def test_help_centre_properties_implemented(self):
        self.check_properties_are_implemented(help_centre_objects)

    def check_properties_are_implemented(self, object_module):
        for cls in iter_classes(object_module):
            obj = cls(api=self.mock_api)
            for attr in (a for a in dir(obj) if a.endswith('id')):
                setattr(obj, attr, 1)
            try:
                call_properties(obj)
            except AttributeError as e:
                object_name = "{}.{}".format(cls.__module__, cls.__name__)
                missing_method_name = str(e).split()[-1]
                self.fail("{} contains a property that calls a non existent method: {}.\n"
                          "This method needs to be implemented in the zenpy.lib.api.Api class."
                          .format(object_name, missing_method_name))


def iter_classes(mod):
    for cls in vars(mod).values():
        if isinstance(cls, type) and cls not in (BaseObject, ProxyDict, ProxyList):
            yield cls


def call_properties(zenpy_object):
    for attr_name in dir(zenpy_object):
        if isinstance(getattr(type(zenpy_object), attr_name, None), property):
            getattr(zenpy_object, attr_name)


def mock_api_call(*args, **kwargs):
    class DummyResponse:
        status_code = 204

        def json(self):
            return {}

    return DummyResponse()
