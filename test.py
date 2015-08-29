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

user = User()
user.name = "SUPER MAN THING"
user.email = 'this@super.com.au'

for user in zenpy.users():
	if user.name.startswith('Face') or user.name.startswith('Sample'):
		continue
	user.name = "Jim Hendy"
	print user.name
	user.active = True
	print zenpy.api.users.update(user).name
	break

sys.exit()
tickets = zenpy.tickets()
zenpy.api.tickets.delete(tickets)
zenpy.api.tickets.create(ticket)
for ticket in zenpy.api.tickets():
	ticket.comment = comment

	ticket.status = 'open'
	result = zenpy.api.tickets.update(ticket)
	print result.audit.metadata.system.ip_address



# print res.audit.author
# for event in res.audit.events:
# 	if event.type == 'Notification':
# 		print event.via.source._from
