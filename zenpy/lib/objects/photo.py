from zenpy.lib.objects.base_object import BaseObject


class Photo(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.content_url = None
        self.name = None
        self.id = None
        self._thumbnails = None
        self.content_type = None
        self.size = None

    @property
    def thumbnails(self):
        if self.api and self._thumbnails:
            for thumbnail in self._thumbnails:
                yield self.api.object_manager.object_from_json('thumbnail', thumbnail)
