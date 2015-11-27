from zenpy.lib.objects.base_object import BaseObject


class Result(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.count = None
        self.facets = None
        self.prev_page = None
        self._results = None
        self.next_page = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def results(self):
        if self.api and self._results:
            return self.api.get_results(self._results)

    @results.setter
    def results(self, results):
        if results:
            self._results = results
