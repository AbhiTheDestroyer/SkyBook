#!/usr/bin/env python3
"""Run against a live `npm run dev` server. Uses only standard library."""
import json, urllib.request, urllib.error, concurrent.futures
BASE='http://127.0.0.1:3001/api'
PASS_TOKEN=ADMIN_TOKEN=RAHUL_TOKEN=''
def call(path,method='GET',body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(BASE+path,data=data,method=method,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})})
    try:
        with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:
        try:d=json.load(e)
        except:d={'error':e.read().decode()}
        return e.code,d
def ask(message,conversation='AUDIT',email='passengerx@demo.com',scope='PASSENGER'):
    return call('/assistant','POST',{'message':message,'conversationId':conversation,'scope':scope},ADMIN_TOKEN if scope=='ADMIN' else RAHUL_TOKEN if email=='rahul@demo.com' else PASS_TOKEN)
def check(name,cond,detail=''):
    if not cond:raise AssertionError(f'{name}: {detail}')
    print('PASS',name)
_,pd=call('/auth/demo-session','POST',{'role':'PASSENGER'});PASS_TOKEN=pd['token']
_,rd=call('/auth/demo-session','POST',{'role':'PASSENGER','email':'rahul@demo.com'});RAHUL_TOKEN=rd['token']
_,ad=call('/auth/demo-session','POST',{'role':'AIRLINE_ADMIN'});ADMIN_TOKEN=ad['token']
call('/demo/reset','POST',{'confirmed':True},ADMIN_TOKEN)
scenarios=[
 ('01 cheap flight','Find a cheap flight from Delhi to Mumbai.','FLIGHT_SEARCH'),
 ('02 morning budget','Find a morning flight under ₹6000.','FLIGHT_SEARCH'),
 ('03 recommendation','Which one do you recommend?','RECOMMENDATION'),
 ('04 booking','Show my booking.','BOOKING'),
 ('05 seat','Find me a window seat.','SEAT'),
]
for name,msg,intent in scenarios:
 st,d=ask(msg,'AUDIT-FLOW');check(name,st==200 and d['intent']==intent,(st,d))
st,d=ask('What is my waitlist position?','AUDIT-WAIT','rahul@demo.com');check('06 waitlist position',st==200 and d['intent']=='WAITLIST' and '#1' in d['text'])
st,d=ask('What is my chance of confirmation?','AUDIT-WAIT','rahul@demo.com');check('07 waitlist probability',st==200 and 'estimate' in d['text'].lower())
st,d=ask('How much will I get if I cancel?');check('08 refund calculation',st==200 and '₹4,500' in d['text'])
st,d=ask('Where is Gate 24?');check('09 gate navigation',st==200 and d['intent']=='NAVIGATION' and d['actions'][0]['payload']['mode']=='3d')
st,d=ask('Can I take 25kg baggage?');check('10 baggage',st==200 and 'exceeds' in d['text'])
st,d=ask('Is my flight delayed?');check('11 flight monitoring',st==200 and d['intent']=='FLIGHT_STATUS' and 'ON TIME' in d['text'])
st,d=ask('Plan my 3-day Mumbai trip.');check('12 trip planning',st==200 and d['intent']=='TRIP_PLAN' and 'Day 3' in d['text'])
st,d=call('/agent/plan','POST',{'command':'Cancel my booking'});check('13 cancellation confirmation',st==200 and d['requiresConfirmation'] and d['steps'][0]['risk']=='MEDIUM')
st,d=ask('How many bookings were made today?','AUDIT-ADMIN','', 'ADMIN');check('14 admin bookings',st==200 and d['intent']=='ADMIN_ANALYTICS' and 'Bookings created today' in d['text'])
st,d=ask('Show flights with high occupancy.','AUDIT-ADMIN','', 'ADMIN');check('15 high occupancy',st==200 and d['intent']=='ADMIN_ANALYTICS' and 'occupancy' in d['text'].lower())
# Authorization and confirmation cannot be bypassed.
st,_=call('/admin/bookings',token=PASS_TOKEN);check('passenger cannot access admin bookings',st==403)
st,_=call('/assistant','POST',{'message':'show revenue','scope':'ADMIN'},PASS_TOKEN);check('passenger cannot invoke SkyAdmin',st==403)
st,_=call('/demo/cancel','POST',{},PASS_TOKEN);check('sensitive endpoint rejects missing confirmation',st==428)
st,_=call('/preferences','PUT',{'preferredSeat':'AISLE'},PASS_TOKEN);check('preference update requires confirmation',st==428)
st,_=call('/support-tickets','POST',{'subject':'Help','description':'Audit'},PASS_TOKEN);check('support ticket requires confirmation',st==428)
# Duplicate seat allocation under concurrent requests.
st,offers=call('/flights?from=JAI&to=DXB&date=2026-08-25');f=offers[0]
payload={'flightId':f['id'],'name':'Concurrency Test','email':'passengerx@demo.com','seat':'14A','fareTier':'Standard','extraBaggage':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex: results=list(ex.map(lambda _:call('/bookings','POST',payload,PASS_TOKEN),range(2)))
check('duplicate booking/seat race',sorted(x[0] for x in results)==[200,409],results)
# Cancellation/recovery race is atomic and idempotent.
call('/demo/reset','POST',{'confirmed':True},ADMIN_TOKEN)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex: results=list(ex.map(lambda _:call('/demo/cancel','POST',{'confirmed':True},PASS_TOKEN),range(2)))
check('waitlist recovery race',sorted(x[0] for x in results)==[200,400],results)
success=[x[1] for x in results if x[0]==200][0]
check('refund amount',success['refund']['amount']==4500 and success['refund']['fee']==500,success)
st,bookings=call('/admin/bookings',token=ADMIN_TOKEN);confirmed14a=[x for x in bookings if x['number']=='SK102' and x['seat']=='14A' and x['status']=='CONFIRMED']
check('single recovered seat owner',len(confirmed14a)==1 and confirmed14a[0]['user_name']=='Rahul',confirmed14a)
# Passenger APIs do not return another passenger records.
st,private=call('/bookings?email=unknown@example.com',token=PASS_TOKEN);check('user-data isolation',st==200 and all(x['user_email']=='passengerx@demo.com' for x in private),private)
call('/demo/reset','POST',{'confirmed':True},ADMIN_TOKEN)
print('ALL E2E AUDIT CHECKS PASSED')
