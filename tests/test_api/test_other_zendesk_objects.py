from time import sleep

from test_api.fixtures import ZenpyApiTestCase

from test_api.fixtures.__init__ import (
    SingleCreateApiTestCase,
    SingleUpdateApiTestCase,
    SingleDeleteApiTestCase,
    CRUDApiTestCase,
    PaginationTestCase,
    IncrementalPaginationTestCase
)

from zenpy.lib.api_objects import (
    Automation,
    Activity,
    Macro,
    Ticket,
    GroupMembership,
    Group,
    Organization,
    Tag,
    RecipientAddress,
    TicketAudit,
    Trigger,
    User,
    View,
)
from zenpy.lib.api_objects.help_centre_objects import (
    Category,
    Topic
)
from zenpy.lib.exception import (
    RecordNotFoundException,
)
from zenpy.lib import util
from datetime import datetime
from unittest import TestCase
class DateTimeTest(TestCase):
    def test_datetime_import(self):
        util.to_unix_ts(datetime.utcnow())
class TicketsIncrementalTest(IncrementalPaginationTestCase):
    __test__ = True
    ZenpyType = Ticket
    api_name = "tickets.incremental"
    object_kwargs = {}

class UsersIncrementalTest(IncrementalPaginationTestCase):
    __test__ = True
    ZenpyType = User
    api_name = "users.incremental"
    object_kwargs = {}

class TestActivities(PaginationTestCase):
    __test__ = True
    ZenpyType = Activity
    api_name = "activities"
    object_kwargs = {}

class TestAutomations(SingleCreateApiTestCase, SingleUpdateApiTestCase, SingleDeleteApiTestCase, PaginationTestCase):
    __test__ = True
    ZenpyType = Automation
    api_name = "automations"

    object_kwargs = dict(
        title="testAutomation{}",
        all=[
                {"field": "status", "operator": "is", "value": "pending"},
                {"field": "PENDING", "operator": "greater_than", "value": "24"}
        ],
        actions=[{"field": "status", "value": "open"}]
    )

    def create_objects(self):
        """ We can't use create_multiple_zenpy_objects for automations - they must have different conditions """
        for i in range(100, 105):
            zenpy_object = Automation(
                title="testAutomation{}".format(i),
                all=[
                        {"field": "PENDING", "operator": "is", "value": "{}".format(i)}
                ],
                actions=[{"field": "status", "value": "open"}]
            )
            self.created_objects.append(self.create_method(zenpy_object))


class TestMacrosCreateUpdateDelete(SingleUpdateApiTestCase, SingleCreateApiTestCase, PaginationTestCase):
    __test__ = True
    ZenpyType = Macro
    object_kwargs = dict(
        title="TestMacro", actions=[{"field": "status", "value": "solved"}]
    )
    api_name = "macros"

    def create_objects(self):
        for i in range(100, 105):
            zenpy_object = Macro(**self.object_kwargs)
            self.created_objects.append(self.create_method(zenpy_object))


class TestDeletedTickets(PaginationTestCase):
    __test__ = True
    ZenpyType = Ticket
    api_name = "tickets"
    expected_single_result_type = TicketAudit
    object_kwargs = dict(subject="test", description="test")
    pagination_limit = 10

    def create_objects(self):
        # Firstly, let's create some tickets
        job_status = self.create_multiple_zenpy_objects(5)
        for r in job_status.results:
            self.created_objects.append(Ticket(id=r.id))

        # And then delete
        self.delete_method(self.created_objects)
        self.created_objects = []

    def test_delete_and_restore(self):
        """ Test restoring tickets """
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            # Let's create a ticket
            ticket_audit = self.create_single_zenpy_object()
            ticket = self.unpack_object(ticket_audit)

            # Then delete it
            self.delete_method(ticket)

            # Then restore
            self.get_api_method("restore")(ticket)

            # And check if it is ok
            ticket_restored = self.api(id=ticket.id)
            self.assertIsInstance(ticket_restored, self.ZenpyType)
            self.assertInCache(ticket_restored)
            self.recursively_call_properties(ticket_restored)

    def test_permanently_delete(self):
        """ Test deteling tickets permanently """
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            # Let's create a ticket
            ticket_audit = self.create_single_zenpy_object()
            ticket = self.unpack_object(ticket_audit)

            # Then delete it
            self.delete_method(ticket)
            self.created_objects = []
            job_status = self.get_api_method("permanently_delete")(ticket)
            self.wait_for_job_status(job_status)

            # Then try to restore
            with self.assertRaises(RecordNotFoundException):
                self.get_api_method("restore")(ticket)


class TestGroupMemberships(PaginationTestCase):
    __test__ = True
    ZenpyType = GroupMembership
    api_name = "group_memberships"
    object_kwargs = {}
    pagination_limit = 10


class TestGroupCreateUpdateDelete(
    SingleCreateApiTestCase, SingleUpdateApiTestCase, SingleDeleteApiTestCase, PaginationTestCase
):
    __test__ = True
    ZenpyType = Group
    object_kwargs = dict(name="testGroup{}")
    api_name = "groups"
    pagination_limit = 10

    def create_objects(self):
        for i in range(5):
            zenpy_object = self.instantiate_zenpy_object(format_val=i)
            self.created_objects.append(self.create_method(zenpy_object))

    def destroy_objects(self):
        for zenpy_object in self.created_objects:
            self.delete_method(zenpy_object)
        self.created_objects = []


class TestOrganizationCreateUpdateDelete(CRUDApiTestCase, PaginationTestCase):
    __test__ = True
    ZenpyType = Organization
    object_kwargs = dict(name="testOrganization{}")
    api_name = "organizations"
    pagination_limit = 10

    def create_objects(self):
        job_status = self.create_multiple_zenpy_objects(5)
        for r in job_status.results:
            self.created_objects.append(Organization(id=r.id))


class TestTags(PaginationTestCase):
    __test__ = True
    ZenpyType = Tag
    api_name = "tags"
    object_kwargs = {}
    pagination_limit = 10


class TestRecipientAddresses(PaginationTestCase):
    __test__ = True
    ZenpyType = RecipientAddress
    api_name = "recipient_addresses"
    from test_api import credentials
    object_kwargs = dict(
        name="From ZenPyTest {}",
        email="test_zenpy{}@" + credentials['subdomain'] + ".com"
    )
    pagination_limit = 10

    def create_objects(self):
        for i in range(5):
            zenpy_object = self.instantiate_zenpy_object(format_val=i)
            self.created_objects.append(self.create_method(zenpy_object))

    def destroy_objects(self):
        for zenpy_object in self.created_objects:
            self.delete_method(zenpy_object)
        self.created_objects = []


class TestTriggers(SingleCreateApiTestCase, SingleUpdateApiTestCase, SingleDeleteApiTestCase, PaginationTestCase):
    __test__ = True
    ZenpyType = Trigger
    api_name = "triggers"

    object_kwargs = dict(
        title="testTrigger{}",
        all=[
                {"field": "status", "operator": "less_than", "value": "solved"},
                {"field": "update_type", "operator": "is", "value": "Create"}
        ],
        actions=[{"field": "status", "value": "open"}]
    )

    def create_objects(self):
        for i in range(100, 105):
            zenpy_object = self.instantiate_zenpy_object(format_val=i)
            self.created_objects.append(self.create_method(zenpy_object))

    def destroy_objects(self):
        for zenpy_object in self.created_objects:
            self.delete_method(zenpy_object)
        self.created_objects = []


class TestTicketsPagination(PaginationTestCase):
    __test__ = True
    ZenpyType = Ticket
    api_name = "tickets"
    expected_single_result_type = TicketAudit
    object_kwargs = dict(subject="test", description="test")
    pagination_limit = 10

    def create_objects(self):
        job_status = self.create_multiple_zenpy_objects(5)
        for r in job_status.results:
            self.created_objects.append(Ticket(id=r.id))


class TestUsersPagination(PaginationTestCase):
    __test__ = True
    ZenpyType = User
    object_kwargs = dict(name="testUser{}")
    api_name = "users"
    pagination_limit = 10

    def create_objects(self):
        for i in range(100, 105):
            zenpy_object = self.instantiate_zenpy_object(format_val=i)
            self.created_objects.append(self.create_method(zenpy_object))


class TestViews(SingleCreateApiTestCase, SingleUpdateApiTestCase, SingleDeleteApiTestCase, PaginationTestCase):
    __test__ = True
    ZenpyType = View
    object_kwargs = dict(
        title="testView{}",
        all=[
                {"field": "status", "operator": "less_than", "value": "solved"},
        ],
    )
    api_name = "views"
    pagination_limit = 10

    def create_objects(self):
        for i in range(100, 105):
            zenpy_object = self.instantiate_zenpy_object(format_val=i)
            self.created_objects.append(self.create_method(zenpy_object))

    def test_count_views(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            view = self.create_single_zenpy_object()
            self.created_objects.append(view)
            count = self.zenpy_client.views.count()
            self.assertGreater(count.value, 0, "Has non zero count")

    def test_get_active_views(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            view = self.create_single_zenpy_object()
            self.created_objects.append(view)
            count = 0
            for _ in self.zenpy_client.views.active():
                count += 1

            self.assertNotEqual(count, 0, "Must be positive")

    def test_get_compact_views(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            view = self.create_single_zenpy_object()
            self.created_objects.append(view)
            count = 0
            for _ in self.zenpy_client.views.compact():
                count += 1

            self.assertNotEqual(count, 0, "Must be positive")

    def wait_for_view_is_ready(self, view, max_attempts=50):
        if self.recorder.current_cassette.is_recording():
            request_interval = 5
        else:
            request_interval = 0.0001
        n = 0
        while True:
            sleep(request_interval)
            n += 1
            view_count = self.zenpy_client.views.count(view)
            if view_count.fresh:
                return
            elif n > max_attempts:
                raise Exception("Too many attempts to retrieve view count!")

    def count_tickets_in_a_view(self, view, cursor_pagination=None):
        if cursor_pagination is not None:
            generator = self.zenpy_client.views.tickets(view, cursor_pagination=cursor_pagination)
        else:
            generator = self.zenpy_client.views.tickets(view)

        tickets_count = 0
        for _ in generator:
            tickets_count += 1
            if tickets_count > 10:
                break
        return tickets_count

    def test_getting_tickets_from_a_view(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            ticket_audit = self.zenpy_client.tickets.create(Ticket(subject="test", description="test"))
            ticket = ticket_audit.ticket
            view = self.create_single_zenpy_object()
            # We have to wait until view's cache is updated
            self.wait_for_view_is_ready(view)

            try:
                count = self.zenpy_client.views.count(view)

                self.assertNotEqual(count.value, 0, "Tickets count must be positive")

                tickets_count_default = self.count_tickets_in_a_view(view)
                tickets_count_obp = self.count_tickets_in_a_view(view, cursor_pagination=False)
                tickets_count_cbp = self.count_tickets_in_a_view(view, cursor_pagination=True)
                tickets_count_cbp1 = self.count_tickets_in_a_view(view, cursor_pagination=1)

                self.assertGreater(tickets_count_default, 1, "Default pagination returned less than 2 objects")
                self.assertNotEqual(tickets_count_cbp, 0, "CBP returned zero")
                self.assertNotEqual(tickets_count_obp, 0, "OBP returned zero")
                self.assertEqual(tickets_count_cbp, tickets_count_obp, "OBP<>CBP")
                self.assertEqual(tickets_count_cbp, tickets_count_cbp1, "CBP<>CBP[1]")

            finally:
                self.zenpy_client.tickets.delete(ticket)
                self.zenpy_client.views.delete(view)


class TestTicketAudits(PaginationTestCase):
    __test__ = True
    ZenpyType = TicketAudit
    object_kwargs = {}
    api_name = "tickets.audits"
    pagination_limit = 10
    skip_obp = True

class CategoryTest(PaginationTestCase):
    __test__ = True
    ZenpyType = Category
    api_name = "help_center.categories"
    object_kwargs = {}

class TopicTest(PaginationTestCase):
    __test__ = True
    ZenpyType = Topic
    api_name = "help_center.topics"
    object_kwargs = {}

class TestUserMe(ZenpyApiTestCase):
    __test__ = True
    def test_users_me(self):
        """ Test restoring tickets """
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            me = self.zenpy_client.users.me()
            self.assertNotEqual(me, None, "me is valid")
            self.assertNotEqual(me.email, "", "email is valid in me")
