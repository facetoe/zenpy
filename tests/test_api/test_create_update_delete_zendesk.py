from test_api.fixtures.__init__ import SingleCreateApiTestCase, CRUDApiTestCase, \
    SingleUpdateApiTestCase, SingleDeleteApiTestCase, ZenpyApiTestCase
from zenpy.lib.api_objects import Ticket, TicketAudit, Group, User, Organization, Macro, RecipientAddress, TicketField, \
    OrganizationField, Upload


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


class TestUserCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = User
    object_kwargs = dict(name='testUser')
    api_name = 'users'


class TestOrganizationCreateUpdateDelete(CRUDApiTestCase):
    __test__ = True
    ZenpyType = Organization
    object_kwargs = dict(name='testOrganization{}')
    api_name = 'organizations'


class TestMacrosCreateUpdateDelete(SingleUpdateApiTestCase,
                                   SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = Macro
    object_kwargs = dict(title='TestMacro', actions=[{"field": "status", "value": "solved"}])
    api_name = 'macros'


class TestRecipientAddressCreateUpdateDelete(SingleUpdateApiTestCase,
                                             SingleCreateApiTestCase):
    __test__ = True
    ZenpyType = RecipientAddress
    object_kwargs = dict(name='Sales', email='help@omniwearshop.com')
    ignore_update_kwargs = ['email']  # Email value cannot be changed after creation
    api_name = 'recipient_addresses'


class TestOrganizationFieldsCreateUpdateDelete(SingleCreateApiTestCase,
                                               SingleDeleteApiTestCase,
                                               SingleUpdateApiTestCase):
    __test__ = True
    ZenpyType = OrganizationField
    object_kwargs = dict(description='test', title='i am test', key='somethingsomethingsomething')
    ignore_update_kwargs = ['key']  # Can't update key after creation.
    api_name = 'organization_fields'


class TestTicketFieldCreateUpdateDelete(SingleCreateApiTestCase,
                                        SingleUpdateApiTestCase,
                                        SingleDeleteApiTestCase):
    __test__ = True
    ZenpyType = TicketField
    object_kwargs = dict(type='text', title='I AM A TEST')
    api_name = 'ticket_fields'


class TestAttachmentUpload(ZenpyApiTestCase):
    __test__ = True

    def call_upload_method(self, *args, **kwargs):
        with self.recorder.use_cassette(
            "{}-upload-single".format(
                self.generate_cassette_name()
            ),
            serialize_with='prettyjson'
        ):
            return self.zenpy_client.attachments.upload(
                *args, **kwargs
            )

    def test_upload_with_file_obj(self):
        f = open('README.md', 'r')
        upload = self.call_upload_method(f, target_name='README.md')
        self.assertTrue(isinstance(upload, Upload))

    def test_upload_with_path_str(self):
        upload = self.call_upload_method('README.md', target_name='README.md')
        self.assertTrue(isinstance(upload, Upload))

    def test_upload_with_pathlib_path(self):
        try:
            from pathlib import Path
        except ImportError:
            # probably python2
            return
        path = Path('README.md')
        upload = self.call_upload_method(path)
        self.assertTrue(isinstance(upload, Upload))
