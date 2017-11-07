from test_api.fixtures.__init__ import SingleCreateApiTestCase, CRUDApiTestCase, \
    SingleUpdateApiTestCase, SingleDeleteApiTestCase
from zenpy.lib.api_objects import Ticket, TicketAudit, Group, User, Organization, Macro


class TestTicketCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = 'tickets'
    expected_single_result_type = TicketAudit


class TestGroupCreateUpdateDelete(SingleCreateApiTestCase,
                                  SingleUpdateApiTestCase,
                                  SingleDeleteApiTestCase):
    __test__ = True
    ZenpyType = Group
    object_kwargs = dict(name='testGroup')
    api_name = 'groups'


class TestUserCreateUpdateDelete(SingleCreateApiTestCase,
                                 SingleUpdateApiTestCase,
                                 SingleDeleteApiTestCase):
    __test__ = True
    ZenpyType = User
    object_kwargs = dict(name='testUser')
    api_name = 'users'


class TestOrganizationCreateUpdateDelete(SingleCreateApiTestCase, SingleUpdateApiTestCase):
    __test__ = True
    ZenpyType = Organization
    object_kwargs = dict(name='testOrganization')
    api_name = 'organizations'


class TestMacrosCreateUpdateDelete(SingleUpdateApiTestCase, SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = Macro
    object_kwargs = dict(title='TestMacro', actions=[{"field": "status", "value": "solved"}])
    api_name = 'macros'
