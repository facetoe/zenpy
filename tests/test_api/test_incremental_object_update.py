from test_api.fixtures import ZenpyApiTestCase


class TestIncrementalObjectUpdate(ZenpyApiTestCase):
    __test__ = True

    def setUp(self):
        with self.recorder.use_cassette(cassette_name="{}-setup".format(self.generate_cassette_name()),
                                        serialize_with='prettyjson'):
            self.ticket = self.zenpy_client.tickets(id=6566)
            self.ticket._clean_dirty()

    def test_new_ticket_only_serializes_id(self):
        self.assertEqual(dict(id=self.ticket.id),
                         self.ticket.to_dict(serialize=True))

    def test_modified_attribute_serialized(self):
        self.ticket.subject = 'YOLOTIME'
        self.assertEqual(dict(id=self.ticket.id, subject=self.ticket.subject),
                         self.ticket.to_dict(serialize=True))

    def test_clean_dirty(self):
        for name, attr in vars(self.ticket).items():
            setattr(self.ticket, name, attr)
        self.assertEqual(self.ticket.to_dict(serialize=True).keys(),
                         self.ticket.to_dict().keys())

        self.ticket._clean_dirty()
        self.assertEqual(dict(id=self.ticket.id),
                         self.ticket.to_dict(serialize=True))

    def test_set_dirty(self):
        self.ticket._set_dirty()
        self.assertEqual(self.ticket.to_dict(serialize=True).keys(),
                         self.ticket.to_dict().keys())
