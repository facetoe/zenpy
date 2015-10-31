
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class JobStatus(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._status = None
        self._url = None
        self._results = None
        self._progress = None
        self._message = None
        self._total = None
        self.id = None
        
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def results(self):
        if self.api and self._results:
            return self.api.get_results(self._results)
    @results.setter
    def results(self, results):
            if results:
                self._results = results
    @property
    def progress(self):
        if self.api and self._progress:
            return self.api.get_progress(self._progress)
    @progress.setter
    def progress(self, progress):
            if progress:
                self._progress = progress
    @property
    def message(self):
        if self.api and self._message:
            return self.api.get_message(self._message)
    @message.setter
    def message(self, message):
            if message:
                self._message = message
    @property
    def total(self):
        if self.api and self._total:
            return self.api.get_total(self._total)
    @total.setter
    def total(self, total):
            if total:
                self._total = total
    
    