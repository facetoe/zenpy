from zenpy.lib.objects.base_object import BaseObject


class TweetEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self.type = None
        self.id = None
        self.recipients = None
        self.direct_message = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
