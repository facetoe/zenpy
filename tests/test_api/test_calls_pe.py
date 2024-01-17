from test_api.fixtures import ZenpyApiTestCase

from zenpy.lib.api_objects.talk_objects import (
    CallPe,
    VoiceComment
)

TEST_APP_ID = 1003048

class TestCallPE(
    ZenpyApiTestCase
):
    __test__ = True
    ZenpyType = CallPe

    def test_create_update_get(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            call = CallPe(
                            app_id=TEST_APP_ID,
                            call_ended_at="2022-01-27T15:32:40+01",
                            call_started_at="2022-01-27T15:31:40+01",
                            direction="inbound",
                            from_line="+183808333456",
                            from_line_nickname="Sales",
                            to_line="+149488484873",
                            to_line_nickname="Technical Support"
            )
            call_created = self.zenpy_client.calls.create(call)
            self.assertIsInstance(call_created, self.ZenpyType)

            call_upd = CallPe(
                            id=call_created.id,
                            call_ended_at="2022-04-16T09:15:37Z"
            )
            call_updated = self.zenpy_client.calls.update(call_upd)
            self.assertIsInstance(call_updated, self.ZenpyType)

            call_requested = self.zenpy_client.calls(id=call_updated.id)
            self.assertIsInstance(call_requested, self.ZenpyType)

    def test_create_with_comment(self):
        cassette_name = "{}-".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            call = CallPe(
                            app_id=TEST_APP_ID,
                            call_ended_at="2022-01-27T15:32:40+01",
                            call_started_at="2022-01-27T15:31:40+01",
                            direction="inbound",
                            from_line="+183808333456",
                            from_line_nickname="Sales",
                            to_line="+149488484873",
                            to_line_nickname="Technical Support"
            )
            comment = VoiceComment(
                            call_fields=["from_line", "to_line", "call_started_at"],
                            title="This is a ticket comment 2"
            )
            call_created = self.zenpy_client.calls.create(call, comment)
            self.assertIsInstance(call_created, self.ZenpyType)

    def test_add_comment(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
            cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            call = CallPe(
                            app_id=TEST_APP_ID,
                            call_ended_at="2022-01-27T15:32:40+01",
                            call_started_at="2022-01-27T15:31:40+01",
                            direction="inbound",
                            from_line="+183808333456",
                            from_line_nickname="Sales",
                            to_line="+149488484873",
                            to_line_nickname="Technical Support"
            )
            call_res = self.zenpy_client.calls.create(call)
            comment = VoiceComment(
                            call_fields=["direction", ],
                            title="This is a ticket comment 2"
            )
            result = self.zenpy_client.calls.comment(call_res, comment)
            self.assertEqual(result["type"], "TpeVoiceComment")
