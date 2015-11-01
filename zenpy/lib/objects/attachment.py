from zenpy.lib.objects.base_object import BaseObject


class Attachment(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._thumbnails = None
        self.file_name = None
        self.content_url = None
        self.content_type = None
        self.id = None
        self.size = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def thumbnails(self):
        if self.api and self._thumbnails:
            return self.api.get_thumbnails(self._thumbnails)

    @thumbnails.setter
    def thumbnails(self, thumbnails):
        if thumbnails:
            self._thumbnails = thumbnails
