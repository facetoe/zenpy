from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib.api_objects.engagement import Engagement
from datetime import datetime, timezone

class TestEngagementsApi(ZenpyApiTestCase):
    __test__ = True

    def test_fetch_engagements(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            response = self.zenpy_client.engagements.fetch_all()
            for engagement in response:
                self.assertIsInstance(engagement, Engagement)

    def test_fetch_engagements_with_start_time(self):
        cassette_name = "{}_start_time".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            start_time = 1751068800
            response = self.zenpy_client.engagements.fetch_all(start_time=start_time)

            for engagement in response:
                self.assertIsInstance(engagement, Engagement)
                engagement_start_time_epoch = int(datetime.strptime(engagement.engagement_start_time, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())
                self.assertGreaterEqual(engagement_start_time_epoch, start_time)

    def test_fetch_engagements_with_ticket_id(self):
        cassette_name = "{}_ticket_id".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            ticket_id = 94579
            response = self.zenpy_client.engagements.fetch_all(ticket_id=ticket_id)

            for engagement in response:
                self.assertIsInstance(engagement, Engagement)
                self.assertEqual(engagement.ticket_id, ticket_id)

    def test_fetch_engagement_by_id(self):
        cassette_name = "{}_engagement_id".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            engagement_id = "C604EBEFC12F6FFB0B38EEC7F6A8B5EF"
            response = self.zenpy_client.engagements.fetch_by_id(engagement_id)

            self.assertEqual(response.engagement_id, engagement_id)
