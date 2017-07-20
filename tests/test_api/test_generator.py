from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib.generator import SearchResultGenerator


class TestSearchGenerator(ZenpyApiTestCase):
    __test__ = True

    def test_search_generator_len(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            search_generator = self.zenpy_client.search(type='ticket')
            self.assertEqual(len(search_generator), len([t for t in search_generator]))

    def test_search_returns_search_result_generator(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            search_generator = self.zenpy_client.search(type='ticket')
            self.assertIsInstance(search_generator, SearchResultGenerator)
