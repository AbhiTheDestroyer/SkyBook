#!/usr/bin/env python3
import json,urllib.request,urllib.error,pathlib,time
B='http://127.0.0.1:3001/api'
def call(p,m='GET',b=None,t=None):
 h={'Content-Type':'application/json'}
 if t:h['Authorization']='Bearer '+t
 try:
  with urllib.request.urlopen(urllib.request.Request(B+p,data=json.dumps(b).encode() if b is not None else None,method=m,headers=h),timeout=15)as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  try:d=json.load(e)
  except:d={'error':e.read().decode()}
  return e.code,d
def ok(n,c,d=''):
 if not c:raise AssertionError(f'{n}: {d}')
 print('PASS',n)
def login(role='PASSENGER',email=None):return call('/auth/demo-session','POST',{'role':role,'email':email})[1]['token']
A=login('AIRLINE_ADMIN');P=login();call('/demo/reset','POST',{'confirmed':True},A)
# 1/2 dashboard and details
st,d=call('/journeys',t=P);ok('01 upcoming journey displayed',st==200 and len(d['journeys'])==1 and d['journeys'][0]['status']=='UPCOMING',d);j=d['journeys'][0];jid=j['id'];fid=j['segments'][0]['flight_id']
st,detail=call('/journeys/'+str(jid),t=P);ok('02 complete journey details',st==200 and detail['booking']['pnr'] and detail['segments'] and detail['passengers'] and detail['baggage'] and detail['timeline'],detail)
ok('dynamic gate normalized',detail['segments'][0]['gate']=='B24',detail['segments'][0])
# ownership
other=login(email='rahul@demo.com');st,_=call('/journeys/'+str(jid),t=other);ok('journey ownership enforced',st==404)
# Payment pending/failure/success are journey states.
call('/admin/journeys/booking/'+str(detail['booking']['id'])+'/payment','POST',{'confirmed':True,'status':'PENDING'},A);jp=call('/journeys/'+str(jid),t=P)[1];ok('payment pending journey state',jp['status']=='PAYMENT_PENDING' and jp['nextAction']['type']=='PAYMENT',jp)
call('/admin/journeys/booking/'+str(detail['booking']['id'])+'/payment','POST',{'confirmed':True,'status':'FAILED'},A);jf=call('/journeys/'+str(jid),t=P)[1];ok('payment failure journey state',jf['status']=='PAYMENT_FAILED' and jf['nextAction']['type']=='PAYMENT_RETRY',jf)
call('/admin/journeys/booking/'+str(detail['booking']['id'])+'/payment','POST',{'confirmed':True,'status':'SUCCESS'},A);call('/journeys/'+str(jid),t=P)
# checkin unavailable then open
call('/admin/waitlist/flight/'+str(fid)+'/schedule','POST',{'confirmed':True,'departure':'2026-08-22T10:00:00.000Z'},A)
st,e=call('/journeys/'+str(jid)+'/checkin','POST',{'confirmed':True},P);ok('check-in eligibility reason',st==422 and '24 hours' in e['error'],e)
call('/admin/journeys/flight/'+str(fid)+'/checkin-open','POST',{'confirmed':True},A)
st,d=call('/journeys',t=P);j=d['journeys'][0];ok('03 check-in becomes available',j['status']=='CHECK_IN_OPEN' and j['nextAction']['type']=='CHECK_IN',j)
st,checked=call('/journeys/'+str(jid)+'/checkin','POST',{'confirmed':True},P);ok('04 check-in completes',st==200 and checked['status']=='CHECKED_IN' and checked['passengers'][0]['checkin_status']=='CHECKED_IN',checked)
ok('boarding pass next action',checked['nextAction']['type']=='BOARDING_PASS',checked['nextAction'])
# task, seat, baggage/payment
st,task=call('/journeys/'+str(jid)+'/tasks','POST',{'title':'Carry passport'},P);ok('personal task add',st==201 and not task['completed'],task)
st,task2=call(f'/journeys/{jid}/tasks/{task["id"]}','PATCH',{'completed':True},P);ok('personal task toggle',st==200 and task2['completed']==1,task2)
st,seat=call('/journeys/'+str(jid)+'/change-seat','POST',{'seat':'13B','confirmed':True},P);ok('3D seat service integration',st==200 and seat['booking']['seat']=='13B' and seat['passengers'][0]['seat']=='13B',seat)
old=seat['booking']['payment_amount'];st,bag=call('/journeys/'+str(jid)+'/baggage','POST',{'weightKg':10,'confirmed':True},P);updated=call('/journeys/'+str(jid),t=P)[1];ok('baggage and payment integration',st==200 and updated['booking']['payment_amount']==old+1200 and any(x['kind']=='EXTRA_CHECKED' for x in updated['baggage']),updated)
# gate/terminal change
call('/demo/flight-update','POST',{'type':'gate','confirmed':True},A);changed=call('/journeys/'+str(jid),t=P)[1];ok('05 gate and terminal change',changed['segments'][0]['gate']=='A12' and changed['segments'][0]['terminal']=='T1' and any(x['event_type']=='GATE_CHANGED' for x in changed['alerts']),changed)
nav=call('/navigation/bootstrap',t=P)[1];ok('06 navigation uses new A12 gate',nav['journey']['gateNumber']=='A12' and nav['journey']['gateNode']['node_key']=='gate_a12',nav['journey'])
# Critical consistency: A12 → B24 must propagate everywhere.
call('/admin/navigation/map-gate','POST',{'confirmed':True,'flightNumber':'SK102','gateNumber':'B24'},A);back=call('/journeys/'+str(jid),t=P)[1];ok('A12 to B24 journey details',back['segments'][0]['gate']=='B24' and back['segments'][0]['terminal']=='T2',back)
ok('A12 to B24 next action',back['nextAction'].get('gate')=='B24',back['nextAction'])
_,notes=call('/notifications',t=P);ok('A12 to B24 notification',any('B24' in n['message'] for n in notes),notes)
nav=call('/navigation/bootstrap',t=P)[1];ok('A12 to B24 navigator',nav['journey']['gateNumber']=='B24' and nav['journey']['gateNode']['node_key']=='gate_b24',nav['journey'])
_,ai_gate=call('/assistant','POST',{'message':'Where is my gate?','conversationId':'GATE-CONSISTENCY'},P);ok('A12 to B24 SkyBuddy', 'B24' in ai_gate['text'],ai_gate)
# delay/boarding/departed/landed/completed state machine
st,_=call('/admin/journeys/flight/'+str(fid)+'/state','POST',{'status':'DELAYED','confirmed':True},A);delay=call('/journeys/'+str(jid),t=P)[1];ok('07 delay alert',delay['status']=='DELAYED' and any(x['event_type']=='FLIGHT_DELAYED' for x in delay['alerts']),delay)
call('/admin/journeys/flight/'+str(fid)+'/state','POST',{'status':'BOARDING','confirmed':True},A);boarding=call('/journeys/'+str(jid),t=P)[1];ok('08 boarding next action',boarding['status']=='BOARDING' and boarding['nextAction']['type']=='BOARD_NOW',boarding)
call('/admin/journeys/flight/'+str(fid)+'/state','POST',{'status':'DEPARTED','confirmed':True},A);departed=call('/journeys/'+str(jid),t=P)[1];ok('09 departed becomes in flight',departed['status']=='IN_FLIGHT',departed)
call('/admin/journeys/flight/'+str(fid)+'/state','POST',{'status':'ARRIVED','confirmed':True},A);landed=call('/journeys/'+str(jid),t=P)[1];ok('10 landed state',landed['status']=='LANDED',landed)
call('/admin/journeys/'+str(jid)+'/complete','POST',{'confirmed':True},A);complete=call('/journeys/'+str(jid),t=P)[1];ok('11 completed journey',complete['status']=='COMPLETED' and complete['timeline'][-1]['state']=='COMPLETED',complete)
# share privacy
st,share=call('/journeys/'+str(jid)+'/share','POST',{'fields':['flight','route','departure','status','payment']},P);ok('privacy controlled share',st==200 and 'payment' not in share['fields'],share)
# SkyBuddy journey context
st,ai=call('/assistant','POST',{'message':'What should I do next? Show my journey and seat.','conversationId':'JRN-AI'},P);ok('SkyBuddy JourneyAgent',st==200 and ai['agent']=='JourneyAgent' and 'Seat' in ai['text'],ai)
# Multi-passenger journey preserves one seat per passenger.
st,mp=call('/demo/journeys/multi-passenger','POST',{'confirmed':True},A);ok('multi-passenger journey',st==200 and len(mp['passengers'])==2 and len({p['seat'] for p in mp['passengers']})==2,mp)
# Multi-segment and layover demo
st,multi=call('/demo/journeys/multi-segment','POST',{'confirmed':True},A);ok('multi-segment journey',st==200 and len(multi['segments'])==2 and multi['segments'][1]['origin']=='DXB' and multi['segments'][1]['destination']=='LHR',multi)
ok('layover event',any(e['event_type']=='LAYOVER_PLANNED' for e in multi['events']),multi['events'])
# Waitlist integration
call('/demo/waitlist/reset','POST',{'confirmed':True},A);F=login(email='passengerf@demo.com');fw=call('/journeys',t=F)[1];ok('waitlisted journey integration',len(fw['waitlisted'])==1 and fw['waitlisted'][0]['position']==1,fw)
call('/demo/waitlist/cancel-passenger-a','POST',{'confirmed':True},A);fw=call('/journeys',t=F)[1];ok('waitlist promotion in My Journey',fw['waitlisted'][0]['status']=='PAYMENT_PENDING',fw)
# cancellation/refund in normal journey after reset
call('/demo/reset','POST',{'confirmed':True},A);d=call('/journeys',t=P)[1];j=d['journeys'][0];st,cancel=call('/bookings/'+str(j['booking']['id'])+'/cancel','POST',{'confirmed':True},P);cancelled=call('/journeys/'+str(j['id']),t=P)[1];ok('cancelled journey and refund',st==200 and cancelled['status']=='CANCELLED' and cancelled['booking']['refund_status']=='INITIATED',cancelled)
# admin metrics + frontend responsive/offline/action hooks
_,metrics=call('/admin/journeys/analytics',t=A);ok('admin journey analytics',all(k in metrics for k in ['active','cancelled','checkinRate','navigationLaunches','waitlistConversions']),metrics)
src=pathlib.Path('src/main.tsx').read_text();css=pathlib.Path('src/styles.css').read_text();ok('controlled polling and offline cache','skybook_journeys_cache' in src and '15000' in src);ok('mobile/desktop/accessibility UI','@media(max-width:620px)' in css and '.journeyDetailGrid' in css and 'prefers-reduced-motion' in css);ok('functional journey actions',all(x in src for x in ["'/checkin'","'/change-seat'","'/baggage'",'skynavigate3d']))
call('/demo/reset','POST',{'confirmed':True},A)
print('ALL MY JOURNEY E2E TESTS PASSED')
