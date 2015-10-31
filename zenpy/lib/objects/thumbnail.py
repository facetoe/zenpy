from zenpy.lib.objects.base_object import BaseObject


class Thumbnail(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.file_name = None
        self.content_type = None
        self.id = None
        self.content_url = None
        self.size = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
