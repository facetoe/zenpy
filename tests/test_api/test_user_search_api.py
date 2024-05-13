from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib.exception import ZenpyException


class TestUserSearchApi(ZenpyApiTestCase):
    def test_raises_zenpyexception_when_neither_query_nor_external_id_are_set(self):
        with self.assertRaises(ZenpyException):
            self.zenpy_client.users.search()

    def test_raises_zenpyexception_when_both_query_and_external_id_are_set(self):
        with self.assertRaises(ZenpyException):
            self.zenpy_client.users.search(query=1, external_id=2)


class TestUserSearchExportApi(ZenpyApiTestCase):
    __test__ = True
    def test_cbp_small_iterations(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            created_at = "2023-09-14T00:39:54Z"
            count = 0
            users = self.zenpy_client.search_export(query=f"created_at>={created_at}", type="user", cursor_pagination=1)
            for _ in users:
                count = count + 1
                if count >= 2:
                    break
            self.assertGreater(count, 1, "Default pagination returned less than 2 objects")

    def test_cbp_large_block(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            created_at = "2019-09-14T00:39:54Z"
            count = 0
            users = self.zenpy_client.search_export(query=f"created_at>={created_at}", type="user", cursor_pagination=1000)
            for _ in users:
                count = count + 1
                if count >= 1001:
                    break
            self.assertGreater(count, 1000, "Default pagination returned less than 1001 objects")
