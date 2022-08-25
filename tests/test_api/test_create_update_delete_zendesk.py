import os
from io import BytesIO

from test_api.fixtures.__init__ import (
    SingleCreateApiTestCase,
    CRUDApiTestCase,
    SingleUpdateApiTestCase,
    SingleDeleteApiTestCase,
    ZenpyApiTestCase,
)

from zenpy.lib.api_objects import (
    Ticket,
    TicketAudit,
    Group,
    User,
    Organization,
    Macro,
    RecipientAddress,
    TicketField,
    OrganizationField,
    Upload,
    UserField,
    Webhook,
    Invocation,
    InvocationAttempt
)


class TestTicketCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = "tickets"
    expected_single_result_type = TicketAudit


class TestGroupCreateUpdateDelete(
    SingleCreateApiTestCase, SingleUpdateApiTestCase, SingleDeleteApiTestCase
):
    __test__ = True
    ZenpyType = Group
    object_kwargs = dict(name="testGroup")
    api_name = "groups"


class TestUserCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = User
    object_kwargs = dict(name="testUser")
    api_name = "users"


class TestOrganizationCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = Organization
    object_kwargs = dict(name="testOrganization{}")
    api_name = "organizations"


class TestMacrosCreateUpdateDelete(SingleUpdateApiTestCase, SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = Macro
    object_kwargs = dict(
        title="TestMacro", actions=[{"field": "status", "value": "solved"}]
    )
    api_name = "macros"


class TestRecipientAddressCreateUpdateDelete(
    SingleUpdateApiTestCase, SingleCreateApiTestCase
):
    __test__ = True
    ZenpyType = RecipientAddress
    object_kwargs = dict(name="Sales", email="help@omniwearshop.com")
    ignore_update_kwargs = ["email"]  # Email value cannot be changed after creation
    api_name = "recipient_addresses"


class TestOrganizationFieldsCreateUpdateDelete(
    SingleCreateApiTestCase, SingleDeleteApiTestCase, SingleUpdateApiTestCase
):
    __test__ = True
    ZenpyType = OrganizationField
    object_kwargs = dict(
        description="test", title="i am test", key="somethingsomethingsomething"
    )
    ignore_update_kwargs = ["key"]  # Can't update key after creation.
    api_name = "organization_fields"


class TestTicketFieldCreateUpdateDelete(
    SingleCreateApiTestCase, SingleUpdateApiTestCase, SingleDeleteApiTestCase
):
    __test__ = True
    ZenpyType = TicketField
    object_kwargs = dict(type="text", title="I AM A TEST")
    api_name = "ticket_fields"


class TestAttachmentUpload(ZenpyApiTestCase):
    __test__ = True

    @property
    def file_path(self):
        """
        Use the projects README.md file (readonly!) as a test file to upload.

        Should work across various python versions and regardless of current
        working dir.
        """
        base_test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return base_test_dir.replace("/tests", "/README.md")

    def call_upload_method(self, *args, **kwargs):
        with self.recorder.use_cassette(
            "{}-upload-single".format(self.generate_cassette_name()),
            serialize_with="prettyjson",
        ):
            return self.zenpy_client.attachments.upload(*args, **kwargs)

    def test_upload_with_file_obj(self):
        with open(self.file_path, "r") as f:
            upload = self.call_upload_method(f, target_name="README.md")
            self.assertTrue(isinstance(upload, Upload))

    def test_upload_with_bytes_io(self):
        buffer = BytesIO(b"a" * 1024 * 1024)
        upload = self.call_upload_method(buffer, target_name="fancybytes.txt")
        self.assertTrue(isinstance(upload, Upload))

    def test_upload_with_path_str(self):
        upload = self.call_upload_method(self.file_path, target_name="README.md")
        self.assertTrue(isinstance(upload, Upload))

    def test_upload_with_pathlib_path(self):
        try:
            from pathlib import Path
        except ImportError:
            # probably python2
            return
        path = Path(self.file_path)
        upload = self.call_upload_method(path)
        self.assertTrue(isinstance(upload, Upload))


class UserFieldsCreateUpdateDelete(
    SingleCreateApiTestCase, SingleDeleteApiTestCase, SingleUpdateApiTestCase
):
    __test__ = True
    ZenpyType = UserField
    object_kwargs = dict(
        description="test", title="i am test", key="somethingsomethingsomething"
    )
    ignore_update_kwargs = ["key"]  # Can't update key after creation.
    api_name = "user_fields"


class TestWebhooksCreateUpdateDelete(SingleCreateApiTestCase):
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
        endpoint="https://example.com/status/200",
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
            zenpy_object = self.create_single_zenpy_object()
            zenpy_object = self.unpack_object(zenpy_object)
            zenpy_object, new_kwargs = self.modify_object(zenpy_object)

            response = self.update_method(zenpy_object)
            self.assertEqual(response.status_code, 204)

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
            webhook = self.zenpy_client.webhooks(id='01FVJ1J73MG04AJRDPD2AKKXH7')  # !!!!!
            count = 0
            for invocation in self.zenpy_client.webhooks.invocations(webhook):
                count += 1
                self.assertIsInstance(invocation, Invocation)

    def test_invocation_attempts(self):
        cassette_name = "{}-invocation-attemps".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            webhook = self.zenpy_client.webhooks(id='01FVJ1J73MG04AJRDPD2AKKXH7')  # !!!!!
            invocation = self.zenpy_client.webhooks.invocations(webhook).next()
            count = 0
            for attempt in self.zenpy_client.webhooks.invocation_attempts(webhook.id, invocation.id):
                count += 1
                self.assertIsInstance(attempt, InvocationAttempt)

