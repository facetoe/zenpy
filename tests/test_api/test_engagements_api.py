from test_api.fixtures import ZenpyApiTestCase
from zenpy.lib.api_objects.engagement import Engagement

class TestEngagementsApi(ZenpyApiTestCase):
    __test__ = True

    def test_fetch_engagements(self):
        cassette_name = "{}".format(self.generate_cassette_name())
        with self.recorder.use_cassette(
                cassette_name=cassette_name, serialize_with="prettyjson"
        ):
            response = self.zenpy_client.engagements()
            # Validate the response structure
            for engagement in response:
                self.assertIsInstance(engagement, Engagement)
                