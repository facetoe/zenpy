from test_api import configure
from time import sleep
from unittest import TestCase

from zenpy.lib.api_objects import BaseObject
from zenpy.lib.cache import should_cache, in_cache, query_cache_by_object
from zenpy.lib.exception import TooManyValuesException, ZenpyException
from zenpy.lib.generator import BaseResultGenerator


class ZenpyApiTestCase(TestCase):
    __test__ = False

    @classmethod
    def setUpClass(cls):
        cls.zenpy_client, cls.recorder = configure()

    def generate_cassette_name(self):
        """
        Taken from BetamaxTestCase. 
        """
        cls = getattr(self, '__class__')
        test = self._testMethodName
        return '{0}.{1}'.format(cls.__name__, test)

    def assertInCache(self, zenpy_object):
        """ If an object should be cached, assert that it is """
        if should_cache(zenpy_object):
            return in_cache(zenpy_object)
        else:
            return True

    def assertNotInCache(self, zenpy_object):
        """ If an object should have been purged from the cache, assert that it is. """
        if should_cache(zenpy_object):
            return not in_cache(zenpy_object)
        else:
            return True

    def assertCacheUpdated(self, zenpy_object, attr, expected):
        """ If an object should be cached, assert that the specified attribute is equal to 'expected'. """
        if should_cache(zenpy_object):
            cached_object = query_cache_by_object(zenpy_object)
            # We expect it to be present
            if cached_object is None:
                return False
            return getattr(zenpy_object, attr) == expected
        else:
            return True

    def wait_for_job_status(self, job_status, max_attempts=30):
        """ Wait until a background job has completed. """

        # If we are currently recording be nice and don't hammer Zendesk for status updates.
        # If not we are replaying an interaction and can hammer the status update to speed up the tests.
        if self.recorder.current_cassette.is_recording():
            request_interval = 2
        else:
            request_interval = 0.0001
        n = 0
        while True:
            sleep(request_interval)
            n += 1
            job_status = self.zenpy_client.job_status(id=job_status.id)
            if job_status.progress == job_status.total:
                return job_status
            elif n > max_attempts:
                raise Exception("Too many attempts to retrieve job status!")

    def recursively_call_properties(self, zenpy_object):
        """ Recursively test that a Zenpy object's properties, and each linked property can be called without error. """
        for attr_name in dir(zenpy_object):
            if isinstance(getattr(type(zenpy_object), attr_name, None), property):
                prop_val = getattr(zenpy_object, attr_name)
                if prop_val and issubclass(prop_val.__class__, BaseObject):
                    self.recursively_call_properties(prop_val)
                elif issubclass(prop_val.__class__, BaseResultGenerator):
                    for obj in prop_val:
                        self.recursively_call_properties(obj)


class CRUDApiTestCase(ZenpyApiTestCase):
    # The type of object the API under test expects.
    ZenpyType = None

    # Any kwargs that should be passed to the __init__ method.
    # If a format placeholder is detected it will be replaced
    # with the object number when generating many objects.
    object_kwargs = None

    # Name of the api such that getattr(Zenpy, api_name) returns
    # the Api under test.
    api_name = None

    # The expected return type when creating a single Zenpy object
    # This is only necessary when the expected return type differs
    # from the ZenpyType.
    expected_single_result_type = None

    def __init__(self, *args, **kwargs):
        super(CRUDApiTestCase, self).__init__(*args, **kwargs)
        if not issubclass(self.ZenpyType, BaseObject):
            raise Exception("ZenpyType must be a subclass of BaseObject!")
        elif self.object_kwargs is None:
            raise Exception("object_kwargs cannot be None!")
        elif self.api_name is None:
            raise Exception("api_name cannot be None!")

    @property
    def create_method(self):
        """ Return the method used for creating objects. """
        if not hasattr(self.api, 'create'):
            raise Exception("Api has not create method - {}".format(self.api))
        return self.api.create

    @property
    def api(self):
        """ Return the current Api under test. """
        if not hasattr(self.zenpy_client, self.api_name):
            raise Exception("Zenpy has not Api named: {}".format(self.api_name))
        return getattr(self.zenpy_client, self.api_name)

    @property
    def single_response_type(self):
        """ Return the expected response type when creating a single object. """
        return self.expected_single_result_type or self.ZenpyType

    def create_and_verify_single_object_creation(self, dummy=False):
        """ Generate a single Zenpy object and ensure it is created correctly.  """
        with self.recorder.use_cassette("{}-create-single".format(self.generate_cassette_name()),
                                        serialize_with='prettyjson'):
            zenpy_object = self.create_single_zenpy_object(dummy=dummy)
            self.assertIsInstance(zenpy_object, self.single_response_type)
            self.assertInCache(zenpy_object)
            self.recursively_call_properties(zenpy_object)

    def create_single_zenpy_object(self, dummy=False):
        """ Helper method for creating single Zenpy object. """
        zenpy_object = self.instantiate_zenpy_object(dummy=dummy)
        return self.create_method(zenpy_object)

    def create_and_verify_objects_creation(self, num_objects):
        """ Generate Zenpy objects and ensure they are created correctly. """
        with self.recorder.use_cassette(cassette_name="{}-create-multiple".format(self.generate_cassette_name()),
                                        serialize_with='prettyjson'):
            job_status = self.create_multiple_zenpy_objects(
                create_func=self.create_method,
                num_objects=num_objects,
                wait_on_job_status=True
            )
            self.assertEqual(len(job_status.results), num_objects)
            for zenpy_object in self.api(ids=[r['id'] for r in job_status.results]):
                self.assertIsInstance(zenpy_object, self.ZenpyType)
                self.assertInCache(zenpy_object)
                self.recursively_call_properties(zenpy_object)

    def create_multiple_zenpy_objects(self, create_func, num_objects, wait_on_job_status=True, dummy=False):
        """ Helper method for creating multiple Zenpy objects. """
        to_create = list()
        for i in range(num_objects):
            zenpy_object = self.instantiate_zenpy_object(i, dummy=dummy)
            to_create.append(zenpy_object)
        result = create_func(to_create)
        if wait_on_job_status:
            return self.wait_for_job_status(result)
        else:
            return result

    def instantiate_zenpy_object(self, format_val=None, dummy=False):
        """ 
        Create a Zenpy object of type ZenpyType with obj_kwargs passed to __init__. 
        Any values with the formatter "{}" will be replaced with format_val. 
        
        If dummy is True, simply return object (for testing type checking).
        """
        obj_kwargs = self.object_kwargs.copy()
        for key in obj_kwargs:
            value = obj_kwargs[key]
            if '{}' in value:
                if format_val is None:
                    raise Exception("Formatter found in object_kwargs but format_val is None!")
                obj_kwargs[key] = value.format(format_val)

        return self.ZenpyType(**obj_kwargs) if not dummy else object()

    def create_dummy_objects(self):
        """ Create some dummy objects for checking invalid types. """
        self.create_multiple_zenpy_objects(
            create_func=self.create_method,
            num_objects=10,
            wait_on_job_status=True,
            dummy=True
        )


class MultipleCreateApiTestCase(CRUDApiTestCase):
    """ Base class for testing passing multiple objects to the create_method. """

    def test_single_object_create(self):
        self.create_and_verify_objects_creation(1)

    def test_half_objects_create(self):
        self.create_and_verify_objects_creation(50)

    def test_full_objects_create(self):
        self.create_and_verify_objects_creation(100)  # Maximum the endpoint supports

    def test_raises_toomanyvaluesexception_create(self):
        with self.assertRaises(TooManyValuesException):
            self.create_and_verify_objects_creation(150)

    def test_raises_zenpyexception_on_invalid_type(self):
        with self.assertRaises(ZenpyException):
            self.create_dummy_objects()


class SingleCreateApiTestCase(CRUDApiTestCase):
    """ Base class for testing passing a single object to the create_method. """

    def test_single_object_creation(self):
        self.create_and_verify_single_object_creation()

    def test_zenpyexception_raised_on_invalid_type(self):
        with self.assertRaises(ZenpyException):
            self.create_and_verify_single_object_creation(dummy=True)
