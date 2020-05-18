from unittest import TestCase

from zenpy.lib.api import UserSearchApi
from zenpy.lib.exception import ZenpyException
from tests.test_api import configure


class TestUserSearchApi(TestCase):
    def test_raises_zenpyexception_when_neither_query_nor_external_id_are_set(self):
        client, _ = configure()
        with self.assertRaises(ZenpyException):
            client.users.search()

    def test_raises_zenpyexception_when_both_query_and_external_id_are_set(self):
        client, _ = configure()
        with self.assertRaises(ZenpyException):
            client.users.search(query=1, external_id=2)
