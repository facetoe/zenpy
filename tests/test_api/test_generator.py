from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib.api_objects import Ticket
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


class TestTicketGeneratorSlice(ZenpyApiTestCase):
    """ These tests rely on the ticket ids starting at 1. """
    __test__ = True

    def test_ticket_slice_low_bound(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[:1]
            self.check_slice_range(values, range(1, 2))

    def test_ticket_slice_lower_page_size_boundary(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[99:100]
            self.check_slice_range(values, range(100, 101))

    def test_ticket_slice_cross_page_size_boundary(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[99:101]
            self.check_slice_range(values, range(100, 102))

    def test_ticket_slice_on_lower_boundary(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[100:101]
            self.check_slice_range(values, range(101, 102))

    def test_ticket_slice_exact_page_size_boundary(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[100:200]
            self.check_slice_range(values, range(101, 201))

    def test_ticket_slice_with_page_size(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[3950:4000:50]
            self.check_slice_range(values, range(3951, 4001))

    def check_slice_range(self, values, slice_range):
        self.assertEqual(len(values), len(slice_range))

        for i, n in enumerate(slice_range):
            self.assertIsInstance(values[i], Ticket)
            self.assertTrue(values[i].id == n,
                            msg="expected Ticket id: {}, found: {}, values: {}".format(n, values[i], values))

