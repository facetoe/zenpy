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
    CustomStatus,
)

from zenpy.lib.exception import (
    ZenpyException,
)

class TestTicketCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = Ticket
    object_kwargs = dict(subject="test", description="test")
    api_name = "tickets"
    expected_single_result_type = TicketAudit


class TestUserCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = User
    object_kwargs = dict(name="testUser", id="")
    api_name = "users"

class TestUserCreateUpdateDeleteNoID(CRUDApiTestCase):
    __test__ = True
    ZenpyType = User
    object_kwargs = dict(name="testUser")
    api_name = "users"

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
        with open(self.file_path, "rb") as f:
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

class CustomStatusesCreateUpdateDelete(
    SingleCreateApiTestCase, SingleUpdateApiTestCase
):
    __test__ = True
    ZenpyType = CustomStatus
    api_name = "custom_statuses"
    object_kwargs = dict(
        agent_label="agent", end_user_label="end", status_category="open"
    )

    # Deletions aren't possible, so clean out any created objects of CustomStatus before tear down
    def tearDown(self):
        self.created_objects = list(object for object in self.created_objects if type(object) is not self.ZenpyType)
        super(CustomStatusesCreateUpdateDelete, self).tearDown()

    # Doesn't matter what the ID is, it should throw an exception
    def test_single_object_deletion(self):
        with self.assertRaises(ZenpyException):
            hopefully_not_real_id = (
                9223372036854775807  # This is the largest id that Zendesk will accept.
            )
            self.delete_method(self.ZenpyType(id=hopefully_not_real_id))
