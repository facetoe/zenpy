from zenpy.lib.objects.base_object import BaseObject


class FacebookEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._body = None
        self._communication = None
        self._ticket_via = None
        self._type = None
        self.id = None
        self._page = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def page(self):
        if self.api and self._page:
            return self.api.get_page(self._page)

    @page.setter
    def page(self, page):
        if page:
            self._page = page
