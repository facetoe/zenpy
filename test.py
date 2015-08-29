import json
import sys
from datetime import datetime, timedelta
from zenpy import Zenpy
from zenpy.lib.api import Api
from zenpy.lib.objects.comment import Comment

from zenpy.lib.objects.ticket import Ticket

# test_creds = json.load(open("/home/facetoe/zendeskapi_creds.json"))
from zenpy.lib.objects.user import User

test_creds = json.load(open('/home/facetoe/testapicreds.json'))
zenpy = Zenpy(test_creds['domain'], test_creds['email'], test_creds['token'])

ticket = Ticket()
ticket.subject = "OMG I MADE A TICKET"
ticket.comment = "THIS IS MY FUNCY COMMENT"

comment = Comment()
comment.public = False
comment.body = "PARTY LIKE A BEAST"

# zenpy.api.tickets.create(ticket)

# user = User()
# user.name = "Amazing Agent"
# user.email = 'this@super.agentman.com.au'
# # user.role = 'agent'
# id = zenpy.api.users.create(user).id

tickets = zenpy.tickets()

resp = zenpy.tickets.update(tickets)
id=  resp.id
status = zenpy.job_status(id=id)
print status.status
print status.message
for result in status.results:
	print result

sys.exit()
tickets = zenpy.tickets()
zenpy.api.tickets.delete(tickets)
zenpy.api.tickets.create(ticket)
for ticket in zenpy.api.tickets():
	ticket.comment = "SUCH ME THATR"

	ticket.status = 'open'
	result = zenpy.api.tickets.update(ticket)
	print result.audit.metadata.system.ip_address



# print res.audit.author
# for event in res.audit.events:
# 	if event.type == 'Notification':
# 		print event.via.source._from
