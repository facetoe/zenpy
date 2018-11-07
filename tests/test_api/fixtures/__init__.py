import hashlib
import uuid
from operator import attrgetter
from time import sleep
from unittest import TestCase

from test_api import configure
from zenpy.lib.api_objects import BaseObject
from zenpy.lib.endpoint import basestring
from zenpy.lib.exception import TooManyValuesException, ZenpyException, RecordNotFoundException
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
        if self.zenpy_client.cache.should_cache(zenpy_object):
            self.assertTrue(self.zenpy_client.cache.in_cache(zenpy_object))

    def assertNotInCache(self, zenpy_object):
        """ If an object should have been purged from the cache, assert that it is. """
        if self.zenpy_client.cache.should_cache(zenpy_object):
            self.assertTrue(not self.zenpy_client.cache.in_cache(zenpy_object))

    def assertCacheUpdated(self, zenpy_object, attr, expected):
        """ If an object should be cached, assert that the specified attribute is equal to 'expected'. """
        if self.zenpy_client.cache.should_cache(zenpy_object):
            cached_object = self.zenpy_client.cache.query_cache_by_object(zenpy_object)
            # We expect it to be present
            assert cached_object is not None
            self.assertTrue(getattr(zenpy_object, attr) == expected)

    def wait_for_job_status(self, job_status, max_attempts=50):
        """ Wait until a background job has completed. """

        # If we are currently recording be nice and don't hammer Zendesk for status updates.
        # If not we are replaying an interaction and can hammer the status update to speed up the tests.
        if self.recorder.current_cassette.is_recording():
            request_interval = 5
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


class ModifiableApiTestCase(ZenpyApiTestCase):
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

    # Kwargs whose values should not be changed in the the update request.
    # Some fields in update requests cannot have their value changed
    # due to Zendesk API constraints.
    ignore_update_kwargs = []

    def setUp(self):
        super(ModifiableApiTestCase, self).setUp()
        self.created_objects = []

    def tearDown(self):
        super(ModifiableApiTestCase, self).tearDown()
        if self.created_objects:
            cassette_name = "{}-tearDown".format(self.generate_cassette_name())
            with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
                if len(self.created_objects) == 1:
                    self.delete_method(self.created_objects[0])
                else:
                    self.delete_method(self.created_objects)

    def __init__(self, *args, **kwargs):
        super(ModifiableApiTestCase, self).__init__(*args, **kwargs)
        if not issubclass(self.ZenpyType, BaseObject):
            raise Exception("ZenpyType must be a subclass of BaseObject!")
        elif self.object_kwargs is None:
            raise Exception("object_kwargs cannot be None!")
        elif self.api_name is None:
            raise Exception("api_name cannot be None!")

    @property
    def create_method(self):
        """ Return the method used for creating objects. """
        return self.get_api_method('create')

    @property
    def update_method(self):
        """ Return the method used for updating objects. """
        return self.get_api_method('update')

    @property
    def delete_method(self):
        """ Return the method used for deleting objects. """
        return self.get_api_method('delete')

    def get_api_method(self, method_name):
        """ Return the named method. If it doesn't exist, raise an Exception. """
        if not hasattr(self.api, method_name):
            raise Exception("Api has no {} method - {}".format(method_name, self.api))
        return getattr(self.api, method_name)

    @property
    def api(self):
        """ Return the current Api under test. """
        f = attrgetter(self.api_name)
        return f(self.zenpy_client)

    @property
    def single_response_type(self):
        """ Return the expected response type when creating a single object. """
        return self.expected_single_result_type or self.ZenpyType

    def unpack_object(self, zenpy_object):
        """
        If we have a nested object, return the nested object we are interested in.
        Otherwise just return the passed object.
        """
        if hasattr(zenpy_object, self.api.object_type):
            obj = getattr(zenpy_object, self.api.object_type)
        else:
            obj = zenpy_object
        if obj is not None and obj not in self.created_objects:
            self.created_objects.append(obj)
        return obj

    def create_single_zenpy_object(self, dummy=False):
        """ Helper method for creating single Zenpy object. """
        zenpy_object = self.instantiate_zenpy_object(dummy=dummy)
        return self.create_method(zenpy_object)

    def create_multiple_zenpy_objects(self, num_objects, wait_on_job_status=True, dummy=False):
        """ Helper method for creating multiple Zenpy objects. """
        to_create = list()
        for i in range(num_objects):
            zenpy_object = self.instantiate_zenpy_object(uuid.uuid4(), dummy=dummy)
            to_create.append(zenpy_object)
        result = self.create_method(to_create)
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
                    print("Formatter found in object_kwargs but format_val is None!")
                obj_kwargs[key] = value.format(format_val)

        zenpy_object = self.ZenpyType(**obj_kwargs) if not dummy else None
        if zenpy_object:
            # Ensure creating a new object sets the passed attributes as dirty.
            self.assertTrue(all(k in zenpy_object.to_dict(serialize=True) for k in obj_kwargs))
        return zenpy_object

    def modify_object(self, zenpy_object):
        """
        Given a Zenpy object, modify it by hashing it's kwargs and appending the result to the
        existing values.
        """

        def hash_of(to_hash):
            return hashlib.sha1(to_hash.encode()).hexdigest()

        new_kwargs = self.object_kwargs.copy()
        for attr_name in new_kwargs:
            if isinstance(new_kwargs[attr_name], basestring) and attr_name not in self.ignore_update_kwargs:
                new_kwargs[attr_name] += hash_of(new_kwargs[attr_name])
                setattr(zenpy_object, attr_name, new_kwargs[attr_name])
                self.assertTrue(attr_name in zenpy_object._dirty_attributes,
                                msg="Object modification failed to set _dirty_attributes!")
        return zenpy_object, new_kwargs

    def verify_object_updated(self, new_kwargs, zenpy_object):
        """ Given a dict of updated kwargs and a Zenpy object, verify it was correctly updated. """
        updated_object = self.unpack_object(zenpy_object)
        self.assertIsInstance(updated_object, self.ZenpyType)
        self.assertInCache(updated_object)
        for attr_name, attr in new_kwargs.items():
            if isinstance(attr, basestring):
                self.assertEqual(getattr(updated_object, attr_name), new_kwargs[attr_name])
                self.assertCacheUpdated(updated_object, attr_name, attr)
        # Ensure that updating the object cleared the dirty attributes.
        self.assertFalse(updated_object._dirty_attributes)

    def create_dummy_objects(self):
        """ Create some dummy objects for checking invalid types. """
        self.create_multiple_zenpy_objects(
            num_objects=10,
            wait_on_job_status=True,
            dummy=True
        )


class MultipleCreateApiTestCase(ModifiableApiTestCase):
    """ Base class for testing passing multiple objects to the create_method. """

    def test_single_object_create(self):
        self.create_and_verify_multiple_objects_creation(1)

    def test_half_objects_create(self):
        self.create_and_verify_multiple_objects_creation(50)

    def test_full_objects_create(self):
        self.create_and_verify_multiple_objects_creation(100)  # Maximum the endpoint supports

    def test_raises_toomanyvaluesexception_create(self):
        with self.assertRaises(TooManyValuesException):
            self.create_and_verify_multiple_objects_creation(150)

    def create_and_verify_multiple_objects_creation(self, num_objects):
        """ Generate Zenpy objects and ensure they are created correctly. """
        with self.recorder.use_cassette(cassette_name="{}-create-multiple".format(self.generate_cassette_name()),
                                        serialize_with='prettyjson'):
            job_status = self.create_multiple_zenpy_objects(
                num_objects=num_objects,
                wait_on_job_status=True
            )
            self.assertEqual(len(job_status.results), num_objects)
            for zenpy_object in self.api(ids=[r.id for r in job_status.results]):
                self.assertIsInstance(zenpy_object, self.ZenpyType)
                self.assertInCache(zenpy_object)
                self.recursively_call_properties(zenpy_object)

    def test_raises_zenpyexception_on_invalid_type(self):
        with self.assertRaises(ZenpyException):
            self.create_dummy_objects()


class SingleCreateApiTestCase(ModifiableApiTestCase):
    """ Test passing a single object to the create_method. """

    def test_single_object_creation(self):
        self.create_and_verify_single_object_creation()

    def test_single_create_raises_zenpyexception_on_invalid_type(self):
        """ Test that a single object can be created correctly. """
        with self.assertRaises(ZenpyException):
            self.create_method(None)

    def create_and_verify_single_object_creation(self):
        """ Generate a single Zenpy object and ensure it is created correctly.  """
        with self.recorder.use_cassette("{}-create-single".format(self.generate_cassette_name()),
                                        serialize_with='prettyjson'):
            zenpy_object = self.create_single_zenpy_object()
            self.assertIsInstance(zenpy_object, self.single_response_type)
            zenpy_object = self.unpack_object(zenpy_object)
            self.assertIsInstance(zenpy_object, self.ZenpyType)
            self.assertInCache(zenpy_object)
            self.recursively_call_properties(zenpy_object)


class SingleDeleteApiTestCase(ModifiableApiTestCase):
    """ Test passing a single object to the create_method. """

    def test_single_object_deletion(self):
        self.create_and_verify_single_object_deletion()

    def test_single_delete_raises_zenpyexception_on_invalid_type(self):
        """ Test that a single object can be created correctly. """
        with self.assertRaises(ZenpyException):
            self.delete_method(None)

    def test_single_delete_raises_recordnotfoundexception(self):
        cassette_name = "{}-recordnotfound-delete".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with='prettyjson'):
            hopefully_not_real_id = 9223372036854775807  # This is the largest id that Zendesk will accept.
            with self.assertRaises(RecordNotFoundException):
                self.delete_method(self.ZenpyType(id=hopefully_not_real_id))

    def create_and_verify_single_object_deletion(self):
        """ Generate a single Zenpy object and ensure it is deleted correctly.  """
        cassette_name = "{}-delete-single".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with='prettyjson'):
            zenpy_object = self.create_single_zenpy_object()
            zenpy_object = self.unpack_object(zenpy_object)
            self.delete_method(zenpy_object)
            self.created_objects.remove(zenpy_object)


class SingleUpdateApiTestCase(ModifiableApiTestCase):
    def test_single_object_update(self):
        self.create_and_verify_single_object_update()

    def test_single_update_raises_zenpyexception_on_invalid_type(self):
        """ Test that a single object can be created correctly. """
        with self.assertRaises(ZenpyException):
            self.update_method(None)

    def test_single_update_raises_recordnotfoundexception(self):
        cassette_name = "{}-recordnotfound-update".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with='prettyjson'):
            with self.assertRaises(RecordNotFoundException):
                zenpy_object = self.instantiate_zenpy_object()
                hopefully_not_real_id = 9223372036854775807  # This is the largest id that Zendesk will accept.
                zenpy_object.id = hopefully_not_real_id
                self.update_method(zenpy_object)

    def create_and_verify_single_object_update(self):
        cassette_name = "{}-update-single".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            zenpy_object = self.create_single_zenpy_object()
            zenpy_object = self.unpack_object(zenpy_object)
            zenpy_object, new_kwargs = self.modify_object(zenpy_object)

            updated_object = self.update_method(zenpy_object)
            self.assertIsInstance(updated_object, self.single_response_type)

            self.verify_object_updated(new_kwargs, zenpy_object)


class MultipleUpdateApiTestCase(ModifiableApiTestCase):
    def test_multiple_update_single_object(self):
        self.create_and_verify_multiple_object_update(1)

    def test_multiple_update_half_full_objects(self):
        self.create_and_verify_multiple_object_update(50)

    def test_multiple_update_full_objects(self):
        self.create_and_verify_multiple_object_update(100)

    def test_raises_multiple_update_raises_toomanyvaluesexception(self):
        with self.assertRaises(TooManyValuesException):
            self.create_and_verify_multiple_object_update(150)

    def test_multiple_update_raises_zenpyexception_on_invalid_type(self):
        with self.assertRaises(ZenpyException):
            self.delete_method([None])

    def create_and_verify_multiple_object_update(self, num_objects):
        cassette_name = "{}-update-many".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            job_status = self.create_multiple_zenpy_objects(num_objects)
            self.assertEqual(len(job_status.results), num_objects)
            updated_objects = list()
            for zenpy_object in self.api(ids=[r.id for r in job_status.results]):
                modified_object, new_kwargs = self.modify_object(zenpy_object)
                updated_objects.append((modified_object, new_kwargs))
            self.update_method([m[0] for m in updated_objects])
            for modified_object, new_kwargs in updated_objects:
                self.verify_object_updated(new_kwargs, modified_object)


class MultipleDeleteApiTestCase(ModifiableApiTestCase):
    def test_multiple_delete_single_object(self):
        self.create_and_verify_multiple_object_delete(1)

    def test_multiple_delete_half_full_objects(self):
        self.create_and_verify_multiple_object_delete(50)

    def test_multiple_delete_full_objects(self):
        self.create_and_verify_multiple_object_delete(100)

    def test_multiple_delete_raises_zenpyexception_on_invalid_type(self):
        with self.assertRaises(ZenpyException):
            self.delete_method([None])

    def test_multiple_delete_raises_toomanyvaluesexception(self):
        with self.assertRaises(TooManyValuesException):
            self.create_and_verify_multiple_object_delete(150)

    def create_and_verify_multiple_object_delete(self, num_objects):
        cassette_name = "{}-delete-many".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            job_status = self.create_multiple_zenpy_objects(num_objects)
            self.assertEqual(len(job_status.results), num_objects)
            returned_objects = self.api(ids=[r.id for r in job_status.results])
            self.delete_method(list(returned_objects))
            [self.created_objects.remove(obj) for obj in returned_objects]


class CRUDApiTestCase(SingleCreateApiTestCase,
                      SingleUpdateApiTestCase,
                      SingleDeleteApiTestCase,
                      MultipleCreateApiTestCase,
                      MultipleUpdateApiTestCase,
                      MultipleDeleteApiTestCase):
    pass
