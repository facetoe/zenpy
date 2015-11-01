from zenpy.lib.objects.base_object import BaseObject


class TweetEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self.type = None
        self.id = None
        self._recipients = None
        self.direct_message = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def recipients(self):
        if self.api and self._recipients:
            return self.api.get_users(self._recipients)

    @recipients.setter
    def recipients(self, recipients):
        if recipients:
            self._recipients = recipients
