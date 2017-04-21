from test_api.fixtures.__init__ import MultipleCreateApiTestCase, SingleCreateApiTestCase, CRUDApiTestCase, \
    SingleUpdateApiTestCase
from zenpy.lib.api_objects import Ticket, TicketAudit, Group, User


class TestTicketCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = 'tickets'
    expected_single_result_type = TicketAudit


class TestGroupCreateUpdateDelete(SingleCreateApiTestCase, SingleUpdateApiTestCase):
    __test__ = True
    ZenpyType = Group
    object_kwargs = dict(name='testGroup')
    api_name = 'groups'



