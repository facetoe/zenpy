
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class TicketAudit(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._audit = None
        self._ticket = None
        
    @property
    def audit(self):
        if self.api and self._audit:
            return self.api.get_audit(self._audit)
    @audit.setter
    def audit(self, audit):
            if audit:
                self._audit = audit
    @property
    def ticket(self):
        if self.api and self._ticket:
            return self.api.get_ticket(self._ticket)
    @ticket.setter
    def ticket(self, ticket):
            if ticket:
                self._ticket = ticket
    
    