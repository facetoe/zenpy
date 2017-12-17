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

            self.assertTrue(len(values) == 1)
            ticket = values[0]
            self.assertIsInstance(ticket, Ticket)
            self.assertTrue(ticket.id == 1)

    def test_ticket_slice_lower_page_size_boundry(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[99:100]

            self.assertTrue(len(values) == 1)
            ticket = values[0]
            self.assertIsInstance(ticket, Ticket)
            self.assertTrue(ticket.id == 100)

    def test_ticket_slice_cross_page_size_boundry(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[99:101]
            self.assertTrue(len(values) == 2)
            for i, n in enumerate(range(100, 102)):
                self.assertIsInstance(values[i], Ticket)
                self.assertTrue(values[i].id == n,
                                msg="expected Ticket id: {}, found: {}, values: {}".format(n, values[i], values))

    def test_ticket_slice_on_lower_boundry(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            ticket_generator = self.zenpy_client.tickets()
            values = ticket_generator[100:101]
            self.assertTrue(len(values) == 1)
            self.assertIsInstance(values[0], Ticket)
            self.assertTrue(values[0].id == 101)
