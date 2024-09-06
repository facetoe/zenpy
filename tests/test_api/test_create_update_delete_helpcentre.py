from zenpy.lib.api_objects.help_centre_objects import Category, Topic, ContentTag, Article
from test_api.fixtures import (
    SingleUpdateApiTestCase,
    SingleCreateApiTestCase,
    SingleDeleteApiTestCase,
    ZenpyApiTestCase
)
from datetime import datetime

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


class TestHelpCenterCreateArticle(ZenpyApiTestCase):
    __test__ = True
    def test_create_article_with_notify_subscribers(self):
        cassette_name = "{}-true".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with="prettyjson"):
            section_id = 33152317085843  # In my test instance
            new_article = self.zenpy_client.help_center.articles.create(
                section=section_id,
                article=Article(
                    name="Article html content body notifies subscribers",
                    body="<p>Article html content body notifies subscribers</p>",
                    locale="en-us",
                    title="Article html content body notifies subscribers",
                    user_segment_id=33152086785683,
                    permission_group_id=33152086795411,
                    section_id=section_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                notify_subscribers=True
            )
            self.assertTrue((new_article is not None) and (new_article.name == "Article html content body notifies subscribers"))


    def test_create_article_false_notify_subscribers(self):
        cassette_name = "{}-false".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with="prettyjson"):
            section_id = 33152317085843  # In my test instance
            new_article = self.zenpy_client.help_center.articles.create(
                section=section_id,
                article=Article(
                    name="Notify Off Article Name",
                    body="<p>Article html content body does not notifies subscribers</p>",
                    locale="en-us",
                    title="Notify Off Article Name",
                    user_segment_id=33152086785683,
                    permission_group_id=33152086795411,
                    section_id=section_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                notify_subscribers=False
            )
            self.assertTrue((new_article is not None) and (new_article.name == "Notify Off Article Name"))

    def test_create_article_without_notify_subscribers(self):
        cassette_name = "{}-None".format(self.generate_cassette_name())
        with self.recorder.use_cassette(cassette_name, serialize_with="prettyjson"):
            section_id = 33152317085843  # In my test instance
            new_article = self.zenpy_client.help_center.articles.create(
                section=section_id,
                article=Article(
                    name="Notify None Article Name",
                    body="<p>Article html content body does not notifies subscribers</p>",
                    locale="en-us",
                    title="Notify None Article Name",
                    user_segment_id=33152086785683,
                    permission_group_id=33152086795411,
                    section_id=section_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
            )
            self.assertTrue((new_article is not None) and (new_article.name == "Notify None Article Name"))
