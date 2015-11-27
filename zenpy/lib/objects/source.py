from zenpy.lib.objects.base_object import BaseObject


class Source(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._to = None
        self._from_ = None
        self.rel = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def from_(self):
        if self.api and self._from_:
            return self.api.get_from_(self._from_)

    @from_.setter
    def from_(self, from_):
        if from_:
            self._from_ = from_
