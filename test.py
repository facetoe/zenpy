import json
import sys
from datetime import datetime, timedelta
from zenpy import Zenpy
from zenpy.lib.api import Api

from zenpy.lib.objects.ticket import Ticket

# test_creds = json.load(open("/home/facetoe/zendeskapi_creds.json"))
test_creds = json.load(open('/home/facetoe/testapicreds.json'))
zenpy = Zenpy(test_creds['domain'], test_creds['email'], test_creds['token'])

# a = Zenpy('testing23', "facetoe@facetoe.com.au", 'IECmOGKwH462qc147hSHXSYVzkLzCZcHboJThIlD')


ticket = Ticket()
ticket.subject = "OMG I MADE A TICKET"
ticket.comment = "THIS IS MY FUNCY COMMENT"

tickets = zenpy.tickets()
zenpy.api.tickets.delete(tickets)

res = zenpy.api.tickets.create(ticket)


# print res.audit.author
# for event in res.audit.events:
# 	if event.type == 'Notification':
# 		print event.via.source._from
