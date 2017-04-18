from test_fixtures import ZenpyApiTestCase
from zenpy.lib.api_objects import Ticket, TicketAudit, Audit
from zenpy.lib.exception import RecordNotFoundException, ZenpyException


class TicketAPITestCase(ZenpyApiTestCase):
    """ Base class for testing ticket functionality. Ensures we start and finish with no tickets in Zendesk. """

    def setUp(self):
        super(TicketAPITestCase, self).setUp()
        cassette_name = '{0}-setUp'.format(self.__class__.__name__)
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            # Sanity check, we expect our test environment to be empty.
            for _ in self.zenpy_client.tickets():
                raise Exception("Tickets exist in test environment, bailing out!")

    def tearDown(self):
        super(TicketAPITestCase, self).setUp()
        cassette_name = '{0}-tearDown'.format(self.__class__.__name__)
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            tickets = [t for t in self.zenpy_client.tickets()]
            if tickets:
                self.zenpy_client.tickets.delete(tickets)


class TestSingleTicketCRUD(TicketAPITestCase):
    def test_ticket_create_update_delete(self):
        """ Test that create/update/delete works and the cache updated correctly. """
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            # Ensure create works
            ticket_audit = self.zenpy_client.tickets.create(Ticket(subject="lol", description="thing"))
            self.assertInCache(ticket_audit.ticket)

            self.assertIsInstance(ticket_audit, TicketAudit)
            self.assertIsInstance(ticket_audit.ticket, Ticket)
            self.assertIsInstance(ticket_audit.audit, Audit)
            self.assertEqual(ticket_audit.ticket.subject, "lol")

            # Ensure update works
            updated_subject = "new subject"
            ticket_audit.ticket.raw_subject = updated_subject
            update_ta = self.zenpy_client.tickets.update(ticket_audit.ticket)
            self.assertEqual(update_ta.ticket.raw_subject, updated_subject)

            # Ensure the cache was updated
            self.assertCacheUpdated(update_ta.ticket, attr='raw_subject', expected=updated_subject)

            # Ensure delete works
            response = self.zenpy_client.tickets.delete(update_ta.ticket)
            self.assertEqual(response.status_code, 204)

            # Ensure object removed from cache
            self.assertNotInCache(update_ta.ticket)


class TestMultipleTicketCRUD(TicketAPITestCase):
    def test_multiple_ticket_create_update_delete(self):
        """ Test that create/update/delete works and that the cache is updated correctly.  """

        def compare_ticket_lists(lista, listb):
            self.assertEqual(
                sorted((t.raw_subject, t.description) for t in lista),
                sorted((t.raw_subject, t.description) for t in listb)
            )

        # Create tickets and ensure cache is updated.
        orig_tickets, created_tickets = self.create_tickets()
        for ticket in sorted(created_tickets, key=lambda x: x.raw_subject):
            self.assertInCache(ticket)
        compare_ticket_lists(orig_tickets, created_tickets)

        # Update tickets and ensure cache is updated.
        to_update, updated_tickets = self.update_tickets(created_tickets)
        for expected, actual in zip(to_update, updated_tickets):
            self.assertCacheUpdated(expected, attr='raw_subject', expected=actual.raw_subject)
        compare_ticket_lists(to_update, updated_tickets)

        # Delete tickets and ensure removed from cache.
        self.delete_tickets(updated_tickets)

    def delete_tickets(self, updated_tickets):
        with self.recorder.use_cassette("{}-delete".format(self.generate_cassette_name()), serialize_with='prettyjson'):
            self.zenpy_client.tickets.delete(updated_tickets)
            for ticket in updated_tickets:
                self.assertNotInCache(ticket)

    def create_tickets(self):
        """ Helper method for creating some tickets with the raw_subject set. """
        with self.recorder.use_cassette("{}-create".format(self.generate_cassette_name()), serialize_with='prettyjson'):
            tickets = list()
            for i in range(5):
                tickets.append(Ticket(subject=str(i), raw_subject=str(i), description="desc{}".format(i)))
            job_status = self.zenpy_client.tickets.create(tickets)
            self.wait_for_job_status(job_status)
            return tickets, [t for t in self.zenpy_client.tickets()]

    def update_tickets(self, created_tickets):
        """ Helper method for updating the raw_subject attribute. """
        with self.recorder.use_cassette("{}-update".format(self.generate_cassette_name()), serialize_with='prettyjson'):
            to_update = list()
            for ticket in created_tickets:
                ticket.raw_subject = str(int(ticket.subject) + 10)
                to_update.append(ticket)
            job_status = self.zenpy_client.tickets.update(to_update)
            self.wait_for_job_status(job_status)
            return to_update, [t for t in self.zenpy_client.tickets()]


class TestTicketApiExceptions(TicketAPITestCase):
    """ Test the correct exceptions are raised where expected. """

    def test_throws_record_not_found(self):
        """ Ensure a RecordNotFoundException is raised on invalid id. """
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            with self.assertRaises(RecordNotFoundException):
                self.zenpy_client.tickets(id=1337)

    def test_throws_on_invalid_type(self):
        """ Ensure a ZenpyException is raised when attempting CRUD operations on an invalid type. """
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            with self.assertRaises(ZenpyException):
                not_a_ticket = object
                self.zenpy_client.tickets.create(not_a_ticket)
                self.zenpy_client.tickets.update(not_a_ticket)
                self.zenpy_client.tickets.delete(not_a_ticket)


class TestTicketProperties(TicketAPITestCase):
    def setUp(self):
        super(TestTicketProperties, self).setUp()
        cassette_name = "{}-create-test-ticket".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            ticket_audit = self.zenpy_client.tickets.create(Ticket(subject="test-properties", description='things'))
            self.test_ticket = ticket_audit.ticket

    def test_ticket_properties(self):
        """ Recursively test that a ticket's properties, and each linked property can be called without error. """
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            self.recursively_call_properties(self.test_ticket)
