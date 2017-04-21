from test_api.fixtures.__init__ import MultipleCreateApiTestCase, SingleCreateApiTestCase
from zenpy.lib.api_objects import Ticket, TicketAudit, Group, User


class TestMultipleTicketCreate(MultipleCreateApiTestCase):
    __test__ = True
    ZenpyType = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = "tickets"


class TestSingleTicketCreate(SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = 'tickets'
    expected_single_result_type = TicketAudit


class TestSingleGroupCreate(SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = Group
    object_kwargs = dict(name='testGroup')
    api_name = 'groups'


class TestSingleUserCreate(SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = User
    object_kwargs = dict(name='Fred')
    api_name = 'users'
