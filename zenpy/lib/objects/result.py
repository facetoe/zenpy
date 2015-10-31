from zenpy.lib.objects.base_object import BaseObject


class Result(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.count = None
        self.facets = None
        self.prev_page = None
        self.results = None
        self.next_page = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
