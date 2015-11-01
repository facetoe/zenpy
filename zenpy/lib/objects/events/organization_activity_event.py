from zenpy.lib.objects.base_object import BaseObject


class OrganizationActivityEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self._via = None
        self._recipients = None
        self.type = None
        self.id = None
        self.subject = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def via(self):
        if self.api and self._via:
            return self.api.get_via(self._via)

    @via.setter
    def via(self, via):
        if via:
            self._via = via

    @property
    def recipients(self):
        if self.api and self._recipients:
            return self.api.get_users(self._recipients)

    @recipients.setter
    def recipients(self, recipients):
        if recipients:
            self._recipients = recipients
