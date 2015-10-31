from zenpy.lib.objects.base_object import BaseObject


class JobStatus(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.status = None
        self.url = None
        self.results = None
        self.progress = None
        self.message = None
        self.total = None
        self.id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
