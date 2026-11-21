#!/usr/bin/env python3
import json,urllib.request,urllib.error,concurrent.futures,time,pathlib
B='http://127.0.0.1:3001/api'
def call(path,method='GET',body=None,token=None):
 data=json.dumps(body).encode() if body is not None else None;h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 try:
  with urllib.request.urlopen(urllib.request.Request(B+path,data=data,method=method,headers=h),timeout=15) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  try:d=json.load(e)
  except:d={'error':e.read().decode()}
  return e.code,d
def ok(name,cond,data=''):
 if not cond:raise AssertionError(f'{name}: {data}')
 print('PASS',name)
def login(role='PASSENGER',email=None):return call('/auth/demo-session','POST',{'role':role,'email':email})[1]['token']
A=login('AIRLINE_ADMIN');X=login(email='passengerx@demo.com');F=login(email='passengerf@demo.com');G=login(email='passengerg@demo.com');H=login(email='passengerh@demo.com')
def setup():
 st,d=call('/demo/waitlist/reset','POST',{'confirmed':True},A);ok('demo reset',st==200,d);return d
# 1-6 join, eligibility, queue, fare authorization, leave/reorder
D=setup();fid=D['flightId']
st,d=call('/waitlist/join','POST',{'flightId':fid,'passengerCount':1,'cabin':'ECONOMY','maxFareAuthorized':6200,'seatPreference':'AISLE'},X);ok('join requires explicit confirmation',st==428,d)
st,j=call('/waitlist/join','POST',{'confirmed':True,'flightId':fid,'passengerCount':1,'cabin':'ECONOMY','maxFareAuthorized':6200,'seatPreference':'AISLE'},X);ok('01 join sold-out flight',st==201 and j['entry']['position']==4,j);xid=j['entry']['id']
st,dup=call('/waitlist/join','POST',{'confirmed':True,'flightId':fid,'passengerCount':1,'cabin':'ECONOMY','maxFareAuthorized':6200},X);ok('duplicate active waitlist rejected',st in [409,422],dup)
st,pos=call(f'/waitlist/{xid}/position',token=X);ok('03 real queue position',st==200 and pos['position']==4 and pos['queueSize']==4,pos)
st,prob=call(f'/waitlist/{xid}/probability',token=X);ok('19 explainable probability',st==200 and 5<=prob['probability']<=92 and prob['model']=='SKYBOOK_DEMO_V1' and prob['factors'],prob)
st,_=call(f'/waitlist/{xid}/update-fare','POST',{'maxFareAuthorized':6500},X);ok('fare update requires confirmation',st==428)
st,upd=call(f'/waitlist/{xid}/update-fare','POST',{'confirmed':True,'maxFareAuthorized':6500},X);ok('06 confirmed fare authorization update',st==200 and upd['max_fare_authorized']==6500,upd)
st,_=call('/waitlist/leave','POST',{'id':xid},X);ok('leave requires confirmation',st==428)
st,left=call('/waitlist/leave','POST',{'id':xid,'confirmed':True},X);ok('02 leave waitlist',st==200 and left['status']=='CANCELLED',left)
_,glist=call('/waitlist',token=G);ok('04 queue reorder after leave',glist[0]['position']==2,glist)
# 7-10 automatic release, FIFO promotion, payment success, booking/ticket
D=setup();fid=D['flightId']
st,cancel=call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A);promo=cancel['promotion']['promotion'];ok('07 cancellation releases seat and starts match',st==200 and cancel['seat']=='11A' and promo['status']=='PENDING',cancel)
_,fl=call('/flights/'+str(fid));ok('08 temporary atomic seat hold',next(s for s in fl['seats'] if s['label']=='11A')['status']=='HELD',fl)
_,fe=call('/waitlist',token=F);fentry=fe[0];ok('FIFO chooses Passenger F',fentry['status']=='PAYMENT_PENDING',fentry)
_,gp=call('/waitlist',token=G);ok('next queue passenger becomes #1',gp[0]['position']==1,gp)
_,p=call(f'/waitlist/{fentry["id"]}/promotion',token=F);ok('promotion window server controlled',p['promotion_expires_at'] and p['eligible_offer_code']=='SAVE15',p)
st,_=call(f'/waitlist/{fentry["id"]}/confirm-promotion','POST',{'promotionId':p['id']},F);ok('10 payment confirmation required',st==428)
st,confirmed=call(f'/waitlist/{fentry["id"]}/confirm-promotion','POST',{'promotionId':p['id'],'confirmed':True,'promoCode':'SAVE15'},F);ok('10 payment success and confirmation',st==200 and confirmed['status']=='CONFIRMED' and confirmed['seats']==['11A'] and confirmed['discount']>0,confirmed)
_,pay=call('/bookings/'+str(confirmed['bookingId'])+'/payment',token=F);ok('payment amount matches final total',pay['amount']==confirmed['total'] and pay['status']=='SUCCESS',pay)
_,fbook=call('/bookings',token=F);ok('booking and ticket generated',any(b['id']==confirmed['bookingId'] and b['ticket_no'] for b in fbook),fbook)
_,fl=call('/flights/'+str(fid));ok('seat permanently assigned',next(s for s in fl['seats'] if s['label']=='11A')['status']=='OCCUPIED')
# 12 idempotency: second confirmation cannot duplicate
st,again=call(f'/waitlist/{fentry["id"]}/confirm-promotion','POST',{'promotionId':p['id'],'confirmed':True},F);ok('12 duplicate confirmation rejected',st==409,again)
_,books=call('/admin/bookings',token=A);ok('no duplicate promoted booking',len([b for b in books if b['user_email']=='passengerf@demo.com' and b['flight_id']==fid and b['status']=='CONFIRMED'])==1)
_,inv=call('/admin/waitlist/invariants',token=A);ok('ONE SEAT → ONE ACTIVE BOOKING → ONE PASSENGER',inv['ok'],inv)
# Concurrent duplicate confirmation: one promotion can succeed at most once.
D2=setup();c2=call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A)[1];_,ef2=call('/waitlist',token=F);_,pp2=call(f'/waitlist/{ef2[0]["id"]}/promotion',token=F)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:confirm_race=list(ex.map(lambda _:call(f'/waitlist/{ef2[0]["id"]}/confirm-promotion','POST',{'promotionId':pp2['id'],'confirmed':True},F),range(2)))
ok('ONE PROMOTION → AT MOST ONE SUCCESSFUL CONFIRMATION',sorted(x[0] for x in confirm_race)==[200,409],confirm_race)
_,inv=call('/admin/waitlist/invariants',token=A);ok('invariants hold after confirmation race',inv['ok'],inv)
# Restore first confirmed scenario data is no longer required for event assertions; use race winner entry.
fentry=ef2[0];p=pp2
# audit/notifications/AI/offer/3D hooks
_,ev=call(f'/admin/waitlist/{fentry["id"]}/events',token=A);types=[e['event_type'] for e in ev];ok('audit events complete',all(x in types for x in ['PROMOTION_STARTED','PAYMENT_SUCCEEDED','CONFIRMED']),types)
_,notes=call('/notifications',token=F);ok('20 waitlist notifications',any('confirmed' in n['message'].lower() for n in notes),notes)
st,ai=call('/assistant','POST',{'message':'What is my waitlist position and chances?','conversationId':'WL-AI'},F);ok('21 SkyBuddy waitlist interaction',st==200 and ai['agent']=='WaitlistAgent' and ('confirmed' in ai['text'].lower() or 'not guaranteed' in ai['text'].lower()),ai)
ok('23 AI cannot allocate seats',all(x not in ai['tools'] for x in ['reserveSeat','makeBooking','cancelBooking']),ai['tools'])
src=pathlib.Path('src/main.tsx').read_text();ok('22 offer integration explicit', 'promotion.eligible_offer_code' in src and 'Revalidated at confirmation' in src)
ok('23 3D seat-map integration hook', 'seatLabels' in src and 'SEAT AVAILABLE' in src and 'SeatMap' in src)
# 9 promotion expiry moves to G
D=setup();fid=D['flightId'];cancel=call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A)[1];pid=cancel['promotion']['promotion']['id'];st,expired=call('/demo/waitlist/expire-promotion','POST',{'confirmed':True,'promotionId':pid},A);ok('09 promotion expiry',st==200 and expired['expired'] and expired['next']['matched'],expired)
_,fe=call('/waitlist',token=F);_,ge=call('/waitlist',token=G);ok('expired F and promoted G',fe[0]['status']=='EXPIRED' and ge[0]['status']=='PAYMENT_PENDING',(fe,ge))
# 11 payment failure releases and offers next
D=setup();cancel=call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A)[1];_,fe=call('/waitlist',token=F);_,p=call(f'/waitlist/{fe[0]["id"]}/promotion',token=F);st,failed=call(f'/waitlist/{fe[0]["id"]}/confirm-promotion','POST',{'confirmed':True,'promotionId':p['id'],'simulateFailure':True},F);ok('11 payment failure policy',st==200 and failed['status']=='PAYMENT_FAILED' and failed['next']['matched'],failed)
_,ge=call('/waitlist',token=G);ok('payment failure continues to next',ge[0]['status']=='PAYMENT_PENDING',ge)
# 13 race condition: same cancellation twice
D=setup()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:res=list(ex.map(lambda _:call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A),range(2)))
ok('13 cancellation race creates one promotion',sorted(x[0] for x in res)==[200,404],res)
_,adminq=call('/admin/waitlist',token=A);pending=[e for e in adminq if e['status']=='PAYMENT_PENDING'];ok('one held seat/one promotion',len(pending)==1,pending)
# Fare authorization skip: F 6000, G raised to 7000, fare6500
D=setup();_,fef=call('/waitlist',token=F);_,ge=call('/waitlist',token=G);call(f'/waitlist/{ge[0]["id"]}/update-fare','POST',{'confirmed':True,'maxFareAuthorized':7000},G);call('/demo/waitlist/set-fare','POST',{'confirmed':True,'fare':6500},A);result=call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A)[1];ok('fare authorization skips ineligible FIFO entry',result['promotion']['passenger']['name']=='Passenger G',result)
_,fev=call(f'/admin/waitlist/{fef[0]["id"]}/events',token=A);ok('fare skip is explainable',any(e['event_type']=='INELIGIBLE_SKIPPED' for e in fev),fev)
# 14 default group of 3 remains waiting when only 2 seats
D=setup();
for token in [F,G,H]:
 own=call('/waitlist',token=token)[1][0];call('/waitlist/leave','POST',{'id':own['id'],'confirmed':True},token)
_,jx=call('/waitlist/join','POST',{'confirmed':True,'flightId':D['flightId'],'passengerCount':3,'cabin':'ECONOMY','maxFareAuthorized':7000,'allowPartial':False},X);xid=jx['entry']['id'];release=call('/demo/waitlist/release-seats','POST',{'confirmed':True,'labels':['11A','11B'],'idempotencyKey':'group-default'},A)[1];ok('14 group not partially promoted by default',not release['results'],release)
_,xe=call('/waitlist',token=X);ok('group remains active',xe[0]['status']=='ACTIVE' and xe[0]['passenger_count']==3,xe)
# 15 partial enabled creates explicit 2-seat promotion and remainder after confirmation
call('/waitlist/leave','POST',{'id':xid,'confirmed':True},X);# reset seats occupied first
setup();
for token in [F,G,H]:
 own=call('/waitlist',token=token)[1][0];call('/waitlist/leave','POST',{'id':own['id'],'confirmed':True},token)
_,jx=call('/waitlist/join','POST',{'confirmed':True,'flightId':D['flightId'],'passengerCount':3,'cabin':'ECONOMY','maxFareAuthorized':7000,'allowPartial':True},X);xid=jx['entry']['id'];release=call('/demo/waitlist/release-seats','POST',{'confirmed':True,'labels':['11A','11B'],'idempotencyKey':'group-partial'},A)[1];_,xp=call(f'/waitlist/{xid}/promotion',token=X);ok('15 partial confirmation prompt',len(xp['seatLabels'])==2 and xp['remaining_passenger_count']==1,xp)
_,xc=call(f'/waitlist/{xid}/confirm-promotion','POST',{'confirmed':True,'promotionId':xp['id']},X);ok('partial confirmation retains remainder',xc['remainderEntryId'] is not None,xc)
# 16 flight cancellation, 17 schedule, 18 gate events
D=setup();st,_=call(f'/admin/waitlist/flight/{D["flightId"]}/schedule','POST',{'confirmed':True,'departure':'2026-08-21T11:00:00.000Z'},A);ok('17 schedule change handled',st==200)
_,fe=call('/waitlist',token=F);_,ev=call(f'/admin/waitlist/{fe[0]["id"]}/events',token=A);ok('schedule-change event',any(e['event_type']=='FLIGHT_SCHEDULE_CHANGED' for e in ev),ev)
st,_=call('/demo/flight-update','POST',{'confirmed':True,'type':'gate'},A);ok('18 gate change handled',st==200)
_,ev=call(f'/admin/waitlist/{fe[0]["id"]}/events',token=A);ok('gate-change event',any(e['event_type']=='GATE_CHANGED' for e in ev),ev)
call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A)
st,_=call(f'/admin/waitlist/flight/{D["flightId"]}/cancel','POST',{'confirmed':True},A);ok('16 flight cancellation closes queue',st==200)
_,fe=call('/waitlist',token=F);ok('cancelled flight entries expired',fe[0]['status']=='EXPIRED',fe)
_,seatstate=call('/flights/'+str(D['flightId']));ok('flight cancellation releases held seats',all(s['status']!='HELD' for s in seatstate['seats']),seatstate)
# 24 admin analytics / 25 security
_,stats=call('/admin/waitlist/analytics',token=A);ok('24 admin analytics',all(k in stats for k in ['promotionSuccessRate','paymentFailureRate','averageQueueLength','revenueRecovered']),stats)
st,_=call('/admin/waitlist',token=X);ok('25 passenger blocked from admin waitlist',st==403)
st,_=call('/waitlist',token=None);ok('private waitlist requires auth',st==401)
# Restore general SkyBook demo for regression suite.
call('/demo/reset','POST',{'confirmed':True},A)
print('ALL SMART WAITLIST E2E TESTS PASSED')
