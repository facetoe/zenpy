import os
from time import sleep

from test_api.fixtures.__init__ import (
    SingleCreateApiTestCase,
)

from zenpy.lib.api_objects import (
    Webhook,
    Invocation,
    InvocationAttempt,
    WebhookSecret,
)


class TestWebhooks(SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = Webhook
    object_kwargs = dict(
        authentication={
                    "add_position": "header",
                    "data": {
                        "password": "hello_123",
                        "username": "john_smith"
                    },
                    "type": "basic_auth"
                },
        endpoint="https://example.com",
        http_method="GET",
        name="Example Webhook X1234",
        description="Description",
        request_format="json",
        status="active",
        subscriptions=["conditional_ticket_events"],
    )
    ignore_update_kwargs = ["http_method", "request_format", "status"]
    api_name = "webhooks"

    def test_create_and_update_webhook(self):
        cassette_name = "{}-update-single".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            webhook = self.create_single_zenpy_object()
            new_webhook = Webhook(
                                name="New name",
                                request_format="json",
                                http_method="GET",
                                endpoint="https://example.com/status/200",
                                status="active"
            )
            response = self.zenpy_client.webhooks.update(webhook.id, new_webhook)
            self.assertEqual(response.status_code, 204)

    def test_patch_webhook(self):
        cassette_name = "{}-patch-single".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            webhook = self.create_single_zenpy_object()
            try:
                new_name = 'A new name'
                webhook.name = new_name
                response = self.zenpy_client.webhooks.patch(webhook)
                self.assertEqual(response.status_code, 204)
                new_webhook = self.zenpy_client.webhooks(id=webhook.id)
                self.assertEqual(new_webhook.name, new_name)
            finally:
                self.zenpy_client.webhooks.delete(webhook)

    def create_and_check_webhook(self, webhook, test_label, delete_object=True):
        cassette_name = "{}-{}".format(self.generate_cassette_name(), test_label)
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            new_webhook = self.zenpy_client.webhooks.create(webhook)
            try:
                requested_webhook = self.zenpy_client.webhooks(id=new_webhook.id)
                self.assertIsInstance(requested_webhook, self.ZenpyType)
            finally:
                if delete_object:
                    self.zenpy_client.webhooks.delete(new_webhook)

    def test_create_webhook_no_auth(self):
        webhook = self.instantiate_zenpy_object(dummy=False)
        webhook.name += ' No Auth'
        webhook.authentication = None
        self.create_and_check_webhook(webhook, 'create_webhook_no_auth')

    def test_create_webhook_basic_auth(self):
        webhook = self.instantiate_zenpy_object(dummy=False)
        webhook.name += ' Basic Auth'
        webhook.authentication = dict (
                type="basic_auth",
                data={
                    "username": "username",
                    "password": "password"
                },
                add_position="header"
        )
        self.create_and_check_webhook(webhook, 'create_webhook_basic_auth')

    def test_create_webhook_token_auth(self):
        webhook = self.instantiate_zenpy_object(dummy=False)
        webhook.name += ' Token Auth'
        webhook.authentication = dict (
                type="bearer_token",
                data={
                    "token": "token"
                },
                add_position="header"
        )
        self.create_and_check_webhook(webhook, 'create_webhook_token_auth')

    def test_list_webhooks(self):
        cassette_name = "{}-list".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            new_webhook = self.create_single_zenpy_object()
            try:
                found = False
                for object in self.get_api_method("list")():
                    if object.id == new_webhook.id:
                        self.assertIsInstance(object, self.ZenpyType)
                        found = True
                        break
                self.assertTrue(found)

                count = 0
                for object in self.get_api_method("list")(filter='X1234'):
                    count += 1
                self.assertTrue(count == 1)
            finally:
                self.get_api_method("delete")(new_webhook)

    def test_show_webhook(self):
        cassette_name = "{}-show".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            new_webhook = self.create_single_zenpy_object()
            try:
                requested_webhook = self.zenpy_client.webhooks(id=new_webhook.id)
                self.assertIsInstance(requested_webhook, self.ZenpyType)
                self.assertEqual(new_webhook.id, requested_webhook.id)
            finally:
                self.get_api_method("delete")(new_webhook)

    def test_clone_webhook(self):
        cassette_name = "{}-clone".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            first_webhook = self.create_single_zenpy_object()
            try:
                second_webhook = self.get_api_method("clone")(first_webhook)
                self.assertIsInstance(second_webhook, self.ZenpyType)
                self.assertNotEqual(first_webhook.id, second_webhook.id)
                self.get_api_method("delete")(second_webhook)
            finally:
                self.get_api_method("delete")(first_webhook)

    def test_invocations(self):
        cassette_name = "{}-invocations".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            # Needs a webhook with real invocations :(
            webhook = self.zenpy_client.webhooks(id='01HAN96XNH1J7DY8D7RZ22QMT9') # TESTING_CHANGE: OK TO KEEP
            count = 0
            for invocation in self.zenpy_client.webhooks.invocations(webhook):
                count += 1
                self.assertIsInstance(invocation, Invocation)

    def test_invocation_attempts(self):
        cassette_name = "{}-invocation-attemps".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            # Needs a webhook with real invocations :(
            webhook = self.zenpy_client.webhooks(id='01HAN96XNH1J7DY8D7RZ22QMT9') # TESTING_CHANGE: OK TO KEEP
            invocation = self.zenpy_client.webhooks.invocations(webhook).next()
            count = 0
            for attempt in self.zenpy_client.webhooks.invocation_attempts(webhook.id, invocation.id):
                count += 1
                self.assertIsInstance(attempt, InvocationAttempt)

    def test_webhook_show_secret(self):
        cassette_name = "{}-show-secret".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            webhook = self.create_single_zenpy_object()
            try:
                response = self.zenpy_client.webhooks.show_secret(webhook)
                self.assertIsInstance(response, WebhookSecret)
            finally:
                self.zenpy_client.webhooks.delete(webhook)

    def test_webhook_reset_secret(self):
        cassette_name = "{}-reset-secret".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            webhook = self.create_single_zenpy_object()
            try:
                response = self.zenpy_client.webhooks.reset_secret(webhook)
                self.assertIsInstance(response, WebhookSecret)
            finally:
                self.zenpy_client.webhooks.delete(webhook)

    def test_webhook_simple_testing(self):
        cassette_name = "{}-testing-simple".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            if self.recorder.current_cassette.is_recording():
                sleep(60)  # Because of live api limits
            webhook = self.create_single_zenpy_object()
            try:
                response = self.zenpy_client.webhooks.test(webhook)
                self.assertEqual(response.status_code, 200)
            finally:
                self.zenpy_client.webhooks.delete(webhook)

    def test_webhook_testing_with_partial_request(self):
        cassette_name = "{}-testing-request-partial".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            if self.recorder.current_cassette.is_recording():
                sleep(60)  # Because of live api limits
            webhook = self.create_single_zenpy_object()
            try:
                response = self.zenpy_client.webhooks.test(webhook, request={"endpoint": "https://example.org/fail"})
                self.assertEqual(response.status_code, 404)
            finally:
                self.zenpy_client.webhooks.delete(webhook)

    def test_webhook_testing_with_full_request(self):
        cassette_name = "{}-testing-request-full".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            if self.recorder.current_cassette.is_recording():
                sleep(60)  # Because of live api limits
            webhook = self.create_single_zenpy_object()
            try:
                response = self.zenpy_client.webhooks.test(
                    request=dict(
                        endpoint="https://example.org",
                        request_format="json",
                        http_method="GET",
                    )
                )
                self.assertEqual(response.status_code, 200)
            finally:
                self.zenpy_client.webhooks.delete(webhook)
