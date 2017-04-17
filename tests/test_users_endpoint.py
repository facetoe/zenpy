from zenpy.lib.api_objects import User

from test_fixtures import ZenpyApiTestCase


class UserAPITestCase(ZenpyApiTestCase):
    """ Base class for testing user functionality. Ensures we start and finish with no non-admin users in Zendesk. """

    def setUp(self):
        super().setUp()
        cassette_name = '{0}-setUp'.format(self.__class__.__name__)
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            # Sanity check, we expect our test environment to be empty of non-admin users.
            for user in self.zenpy_client.search(type="user"):
                if user.role != "admin":
                    raise Exception("Non-admin users found in test instance, bailing out!")

    def tearDown(self):
        super().setUp()
        cassette_name = '{0}-tearDown'.format(self.__class__.__name__)
        with self.recorder.use_cassette(cassette_name=cassette_name, serialize_with='prettyjson'):
            to_delete = list()
            for user in self.zenpy_client.search(type='user'):
                if user.role != "admin":
                    to_delete.append(user)
            if to_delete:
                self.zenpy_client.users.delete(to_delete)


class TestSingleUserCRUD(UserAPITestCase):
    def test_user_create_update_delete(self):
        with self.recorder.use_cassette(self.generate_cassette_name(), serialize_with='prettyjson'):
            user_name, user_email = "Fred", "examplethings@example.com"
            user = self.zenpy_client.users.create(User(email=user_email, name=user_name))

            self.assertIsInstance(user, User)
            self.assertEqual(user.name, user_name)
            self.assertEqual(user.email, user_email)
            self.assertInCache(user)

            new_name = "Not Fred Anymore"
            user.name = new_name
            updated_user = self.zenpy_client.users.update(user)
            self.assertEqual(updated_user.name, new_name)
            self.assertCacheUpdated(updated_user, attr="name", expected=new_name)

            self.zenpy_client.users.delete(updated_user)
            self.assertNotInCache(updated_user)



