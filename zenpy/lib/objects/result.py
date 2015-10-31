from zenpy.lib.objects.base_object import BaseObject


class Result(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._count = None
        self._facets = None
        self._prev_page = None
        self._results = None
        self._next_page = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def facets(self):
        if self.api and self._facets:
            return self.api.get_facets(self._facets)

    @facets.setter
    def facets(self, facets):
        if facets:
            self._facets = facets

    @property
    def prev_page(self):
        if self.api and self._prev_page:
            return self.api.get_prev_page(self._prev_page)

    @prev_page.setter
    def prev_page(self, prev_page):
        if prev_page:
            self._prev_page = prev_page
