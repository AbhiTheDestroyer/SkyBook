#!/usr/bin/env python3
import json,urllib.request,urllib.error,time
B='http://127.0.0.1:3001/api'
def c(p,m='GET',b=None,t=None):
 h={'Content-Type':'application/json'}
 if t:h['Authorization']='Bearer '+t
 try:
  with urllib.request.urlopen(urllib.request.Request(B+p,data=json.dumps(b).encode() if b is not None else None,method=m,headers=h),timeout=15)as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  try:d=json.load(e)
  except:d={'error':e.read().decode()}
  return e.code,d
def ok(n,x,d=''):
 if not x:raise AssertionError(f'{n}: {d}')
 print('PASS',n)
def login(role='PASSENGER',email=None):return c('/auth/demo-session','POST',{'role':role,'email':email})[1]['token']
A=login('AIRLINE_ADMIN');P=login();R=login(email='rahul@demo.com');c('/demo/reset','POST',{'confirmed':True},A);P=login();R=login(email='rahul@demo.com')
# profile persistence
st,p=c('/profile',t=P);ok('login/profile',st==200 and p['user']['email']=='passengerx@demo.com',p)
st,_=c('/profile','PATCH',{'name':'Passenger X Updated','phone':'+91 9876543210','emergencyContact':'Emergency +91 9000000000','preferredMeal':'VEGETARIAN','accessibilityPreferences':['NO_STAIRS']},P);p=c('/profile',t=P)[1];ok('personal info persists',st==200 and p['user']['name']=='Passenger X Updated' and p['settings']['preferred_meal']=='VEGETARIAN',p)
st,sp=c('/profile/passengers','POST',{'name':'Family Traveller','relationship':'FAMILY','nationality':'Indian','documentType':'PASSPORT','documentLast4':'1234'},P);ok('saved passenger persists',st==201 and sp['document_last4']=='1234',sp)
st,_=c('/profile/passengers/'+str(sp['id']),'PATCH',{'name':'Hacker'},R);ok('cross-user passenger edit denied',st==404)
# flight save/alert/book
_,fl=c('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20',t=P);f=next(x for x in fl if x['availability']>0);c('/flights/'+str(f['id'])+'/save','POST',{},P);_,sv=c('/flights/saved/list',t=P);ok('saved flight profile',any(x['id']==f['id'] for x in sv),sv)
_,alert=c('/flights/price-alerts','POST',{'origin':'DEL','destination':'BOM','travelDate':'2026-08-20','targetPrice':6000},P);ok('price alert profile',alert['user_id']==p['user']['id'],alert)
fd=c('/flights/'+str(f['id']),t=P)[1];seat=next(s for s in fd['seats'] if s['status']=='AVAILABLE')['label'];st,b=c('/bookings','POST',{'flightId':f['id'],'name':'Passenger X Updated','email':'passengerx@demo.com','seat':seat,'fareTier':'Standard','expectedFare':f['fare']},P);ok('booking/payment/ticket',st==200 and b['transactionId'] and b['ticketNo'],b)
_,payments=c('/profile/payments',t=P);_,tickets=c('/profile/tickets',t=P);ok('profile payment history',any(x['booking_id']==b['id'] for x in payments));ok('profile ticket history',any(x['ticket_no']==b['ticketNo'] for x in tickets))
_,jd=c('/journeys',t=P);j=next(x for x in jd['journeys'] if x['booking']['id']==b['id']);ok('My Journey profile',j['booking']['pnr']==b['pnr'],j)
# seat and notification
newseat=next(s for s in fd['seats'] if s['status']=='AVAILABLE' and s['label']!=seat)['label'];st,j2=c('/journeys/'+str(j['id'])+'/change-seat','POST',{'confirmed':True,'seat':newseat},P);ok('seat change persists',st==200 and j2['passengers'][0]['seat']==newseat,j2)
_,notes=c('/notifications',t=P);ok('notifications owner scoped',all('recipient' not in x for x in notes),notes)
# navigation/status/AI
_,nav=c('/navigation/bootstrap',t=P);ok('airport navigation profile',nav['journey'] is not None,nav)
_,status=c('/flights/status?flightNumber='+f['number']+'&date=2026-08-20');ok('flight status profile',status['source']=='SKYBOOK_DATABASE',status)
_,ai=c('/assistant','POST',{'message':'Show my journey, seat and gate','conversationId':'PROFILE-QA'},P);ok('SkyBuddy authorized profile context',ai['agent']=='JourneyAgent' and newseat in ai['text'],ai)
# admin gate/delay/cancel synchronization
c('/admin/navigation/map-gate','POST',{'confirmed':True,'flightNumber':f['number'],'gateNumber':'A12'},A);c('/admin/navigation/map-gate','POST',{'confirmed':True,'flightNumber':f['number'],'gateNumber':'B24'},A);jj=c('/journeys/'+str(j['id']),t=P)[1];ok('admin gate sync',jj['segments'][0]['gate']=='B24',jj)
c('/admin/journeys/flight/'+str(f['id'])+'/state','POST',{'confirmed':True,'status':'DELAYED'},A);jj=c('/journeys/'+str(j['id']),t=P)[1];ok('admin delay sync',jj['status']=='DELAYED',jj)
c('/admin/journeys/flight/'+str(f['id'])+'/state','POST',{'confirmed':True,'status':'CANCELLED'},A);jj=c('/journeys/'+str(j['id']),t=P)[1];ok('admin cancellation/refund sync',jj['status']=='CANCELLED' and jj['booking']['refund_status']=='INITIATED',jj)
_,refunds=c('/profile/refunds',t=P);ok('refund profile',any(x['booking_id']==b['id'] for x in refunds),refunds)
# support
st,sup=c('/support-tickets','POST',{'confirmed':True,'subject':'Booking help','description':'Need assistance','category':'BOOKING'},P);_,support=c('/profile/support',t=P);ok('support persists',st==200 and any(x['ticket_ref']==sup['ticketRef'] for x in support),support)
# IDOR checks
st,rb=c('/bookings?email=passengerx@demo.com',t=R);ok('User B cannot read User A bookings',st==200 and all(x['user_email']=='rahul@demo.com' for x in rb),rb)
st,_=c('/journeys/'+str(j['id']),t=R);ok('User B cannot read journey',st==404)
st,_=c('/bookings/'+str(b['id'])+'/payment',t=R);ok('User B cannot read payment',st==403)
st,_=c('/profile/passengers/'+str(sp['id']),'DELETE',t=R);ok('User B cannot delete passenger',st==404)
st,_=c('/flights/saved/list');ok('saved flights require auth',st==401)
st,_=c('/flights/price-alerts/list');ok('alerts require auth',st==401)
st,_=c('/profile');ok('profile requires auth',st==401)
# logout invalidates token
st,_=c('/auth/logout','POST',{},P);st2,_=c('/profile',t=P);ok('logout invalidates session',st==200 and st2==401)
c('/demo/reset','POST',{'confirmed':True},A)
print('ALL PROFILE SECURITY E2E TESTS PASSED')
