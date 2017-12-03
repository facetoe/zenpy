from unittest import TestCase
from zenpy import ZenpyCache

from zenpy.lib.api_objects import Ticket, UserField
from zenpy.lib.cache import add_to_cache, query_cache, delete_from_cache
from zenpy.lib.exception import ZenpyCacheException
from zenpy.lib.util import get_object_type


class TestZenpyCache(TestCase):
    def setUp(self):
        self.cache = ZenpyCache('LRUCache', 100)

    def test_throws_cache_exception_on_invalid_object(self):
        with self.assertRaises(ZenpyCacheException):
            self.cache[1] = object()

    def test_throws_cache_exception_on_none(self):
        with self.assertRaises(ZenpyCacheException):
            self.cache[1] = None

    def test_object_retrieval(self):
        ticket_id = 1
        ticket = Ticket(id=ticket_id)
        self.cache[ticket_id] = ticket

        self.assertEqual(len(self.cache), 1)
        self.assertIs(self.cache[ticket_id], ticket)

    def test_cache_purge(self):
        num_objects = 10
        self.populate_cache(num_objects)
        self.assertEqual(len(self.cache), num_objects)
        self.cache.purge()
        self.assertEqual(len(self.cache), 0)

    def test_set_maxsize(self):
        num_objects = 10
        self.populate_cache(10)
        self.cache.set_maxsize(20)
        self.assertEqual(len(self.cache), num_objects)

    def populate_cache(self, num_objects):
        for i in range(num_objects):
            self.cache[i] = Ticket(id=i)

    def tearDown(self):
        self.cache.purge()


class TestCacheModuleMethods(TestCase):
    def test_cache_object(self):
        cache_key = 1
        ticket = self.cache_item(id=cache_key)
        self.assertIs(query_cache(get_object_type(ticket), cache_key), ticket)

    def test_remove_from_cache(self):
        cache_key = 1
        zenpy_object = self.cache_item(id=cache_key)
        self.assertIs(query_cache(get_object_type(zenpy_object), cache_key), zenpy_object)
        delete_from_cache(zenpy_object)
        self.assertIs(query_cache(get_object_type(zenpy_object), cache_key), None)

    def cache_item(self, zenpy_class=Ticket, **kwargs):
        zenpy_object = zenpy_class(**kwargs)
        add_to_cache(zenpy_object)
        return zenpy_object
