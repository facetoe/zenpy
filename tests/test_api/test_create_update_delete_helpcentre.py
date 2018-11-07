from zenpy.lib.api_objects.help_centre_objects import Category
from test_api.fixtures import SingleUpdateApiTestCase, SingleCreateApiTestCase, SingleDeleteApiTestCase


class TestCategoryCreateUpdateDelete(SingleUpdateApiTestCase, SingleCreateApiTestCase, SingleDeleteApiTestCase):
    __test__ = True
    ZenpyType = Category
    object_kwargs = dict(name='test', description='this is a test')
    api_name = 'help_center.categories'
