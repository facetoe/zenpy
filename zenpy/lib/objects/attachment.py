from zenpy.lib.objects.base_object import BaseObject


class Attachment(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.thumbnails = None
        self.file_name = None
        self.content_url = None
        self.content_type = None
        self.id = None
        self.size = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
