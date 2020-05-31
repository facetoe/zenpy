from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib.exception import ZenpyException


class TestUserSearchApi(ZenpyApiTestCase):
    def test_raises_zenpyexception_when_neither_query_nor_external_id_are_set(self):
        with self.assertRaises(ZenpyException):
            self.zenpy_client.users.search()

    def test_raises_zenpyexception_when_both_query_and_external_id_are_set(self):
        with self.assertRaises(ZenpyException):
            self.zenpy_client.users.search(query=1, external_id=2)
