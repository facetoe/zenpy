from zenpy.lib.objects.base_object import BaseObject


class OrganizationActivityEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self._via = None
        self.recipients = None
        self.type = None
        self.id = None
        self.subject = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
