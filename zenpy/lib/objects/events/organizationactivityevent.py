from zenpy.lib.objects.base_object import BaseObject


class OrganizationActivityEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.body = None
        self.via = None
        self.recipients = None
        self.type = None
        self.id = None
        self.subject = None
