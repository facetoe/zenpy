from test_api.fixtures.__init__ import MultipleCreateApiTestCase, SingleCreateApiTestCase
from zenpy.lib.api_objects import Ticket, TicketAudit, Group


class TestMultipleTicketCreate(MultipleCreateApiTestCase):
    __test__ = True
    ZenpyClass = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = "tickets"


class TestSingleTicketCreate(SingleCreateApiTestCase):
    __test__ = True
    ZenpyClass = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = 'tickets'
    expected_single_result_type = TicketAudit


class TestSingleGroupCreate(SingleCreateApiTestCase):
    __test__ = True
    ZenpyClass = Group
    object_kwargs = dict(name='testGroup')
    api_name = 'groups'
