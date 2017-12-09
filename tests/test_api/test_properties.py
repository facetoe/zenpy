from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib import api_objects
from zenpy.lib.api_objects import BaseObject


class TestProperties(ZenpyApiTestCase):
    __test__ = True

    def setUp(self):
        # Could pick any api class, the methods are in the Api class which they all subclass from.
        self.mock_api = self.zenpy_client.tickets
        self.mock_api._call_api = self.call_api

    def test_zendesk_object_properties_implemented(self):
        self.properties_are_implemented(api_objects)

    def properties_are_implemented(self, mod):
        for cls in self.iter_classes(mod):
            obj = cls(api=self.mock_api)
            for attr in (a for a in dir(obj) if a.endswith('id')):
                # Just mock an id of 1
                setattr(obj, attr, 1)

            try:
                self.call_properties(obj)
            except AttributeError as e:
                object_name = "{}.{}".format(cls.__module__, cls.__name__)
                missing_method_name = str(e).split()[-1]
                self.fail("{} contains a property that calls a non existent method: {}.\n"
                          "This method needs to be implemented in the zenpy.lib.api.Api class."
                          .format(object_name, missing_method_name))

    def iter_classes(self, mod):
        for name, cls in vars(mod).items():
            if isinstance(cls, type) and cls is not BaseObject:
                yield cls

    def call_properties(self, zenpy_object):
        for attr_name in dir(zenpy_object):
            if isinstance(getattr(type(zenpy_object), attr_name, None), property):
                getattr(zenpy_object, attr_name)

    def call_api(self, *args, **kwargs):
        class DummyResponse:
            status_code = 204

            def json(self):
                return {}

        return DummyResponse()
