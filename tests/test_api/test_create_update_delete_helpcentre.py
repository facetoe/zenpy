from zenpy.lib.api_objects.help_centre_objects import Category, Topic, ContentTag
from test_api.fixtures import (
    SingleUpdateApiTestCase,
    SingleCreateApiTestCase,
    SingleDeleteApiTestCase,
)


class TestContentTagCreateUpdateDelete(
    SingleUpdateApiTestCase, SingleCreateApiTestCase, SingleDeleteApiTestCase
):
    __test__ = True
    ZenpyType = ContentTag
    object_kwargs = dict(name="mama_was_a_rolling_stone")
    api_name = "help_center.content_tags"
    def test_single_delete_raises_recordnotfoundexception(self):
        cassette_name = "{}-recordnotfound-delete".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with="prettyjson"):
            hopefully_not_real_id = (
                "09J5PBXP9XEZ39AC3AABC042PY"
            )
            with self.assertRaises(Exception):
                res = self.delete_method(self.ZenpyType(id=hopefully_not_real_id))
                self.assertEqual(res.status == 204)

    def test_single_update_raises_recordnotfoundexception(self):
        cassette_name = "{}-recordnotfound-update".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with="prettyjson"):
            with self.assertRaises(Exception):
                zenpy_object = self.instantiate_zenpy_object()
                hopefully_not_real_id = (
                    "09J5PBXP9XEZ39AC3AABC042PY"
                )
                zenpy_object.id = hopefully_not_real_id
                self.update_method(zenpy_object)


class TestCategoryCreateUpdateDelete(
    SingleUpdateApiTestCase, SingleCreateApiTestCase, SingleDeleteApiTestCase
):
    __test__ = True
    ZenpyType = Category
    object_kwargs = dict(name="test", description="this is a test")
    api_name = "help_center.categories"

class TestCommunityTopicCreateUpdateDelete(
    SingleUpdateApiTestCase, SingleCreateApiTestCase, SingleDeleteApiTestCase
):
    __test__ = True
    ZenpyType = Topic
    object_kwargs = dict(name="test", description="this is a Topic test")
    api_name = "help_center.topics"
