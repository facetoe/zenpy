from zenpy.lib.api_objects import RoutingAttribute
from test_api.fixtures import SingleCreateApiTestCase
from zenpy.lib.exception import ZenpyException

# https://developer.zendesk.com/rest_api/docs/support/skill_based_routing

class TestRoutingApi(SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = RoutingAttribute
    object_kwargs = dict(name='test_attribute')
    api_name = 'routing.attributes'

