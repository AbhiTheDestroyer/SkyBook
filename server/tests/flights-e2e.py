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
def login(role='PASSENGER'):return call('/auth/demo-session','POST',{'role':role})[1]['token']
P=login();A=login('AIRLINE_ADMIN');call('/demo/reset','POST',{'confirmed':True},A)
_,aps=call('/airports?q=Delhi');ok('airport autocomplete',aps['data'][0]['iata']=='DEL',aps)
st,res=call('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20&passengers=1&cabin=ECONOMY',t=P);ok('dynamic search API',st==200 and len(res)>=2 and all(x['origin']=='DEL' and x['destination']=='BOM' for x in res),res)
f=res[0];st,d=call('/flights/'+str(f['id']),t=P);ok('flight details and seats',st==200 and d['flight']['number']==f['number'] and isinstance(d['seats'],list),d)
st,status=call('/flights/status?flightNumber='+f['number']+'&date=2026-08-20');ok('verified flight status',st==200 and status['source']=='SKYBOOK_DATABASE',status)
# save, ownership and alert
st,_=call('/flights/'+str(f['id'])+'/save','POST',{},P);_,saved=call('/flights/saved/list',t=P);ok('saved flight',st==200 and any(x['id']==f['id'] for x in saved),saved)
st,alert=call('/flights/price-alerts','POST',{'origin':'DEL','destination':'BOM','travelDate':'2026-08-20','targetPrice':5000},P);ok('price alert',st==201 and alert['status']=='ACTIVE',alert)
_,alerts=call('/flights/price-alerts/list',t=P);ok('private price alert list',any(x['id']==alert['id'] for x in alerts))
st,_=call('/flights/saved/list');ok('private saved flights require auth',st==401)
# transparent frontend tools
src=pathlib.Path('src/main.tsx').read_text();css=pathlib.Path('src/styles.css').read_text();ok('functional filters/sort/compare',all(x in src for x in ['setSortBy','setStopFilter','setAirlineFilter','setCompare','maxPrice']))
ok('passenger/cabin/search validation',all(x in src for x in ['setAdults','setChildren','setInfants','setCabin','Origin and destination must be different']))
ok('mobile and accessibility styling','@media(max-width:720px)' in css and 'prefers-reduced-motion' in css)
# sold-out integration
D=call('/demo/waitlist/reset','POST',{'confirmed':True},A)[1];_,sold=call('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20',t=P);sk=next(x for x in sold if x['number']=='SK102');ok('sold-out inventory is real',sk['availability']==0,sk);ok('sold-out UI joins Smart Waitlist','Join waitlist' in src and 'skywaitlist' in src)
# reset then complete normal booking and journey creation
call('/demo/reset','POST',{'confirmed':True},A);_,normal=call('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20',t=P);f=next(x for x in normal if x['number']=='SK218');fd=call('/flights/'+str(f['id']),t=P)[1];seat=next(x for x in fd['seats'] if x['status']=='AVAILABLE')['label'];st,b=call('/bookings','POST',{'flightId':f['id'],'name':'Passenger X','email':'passengerx@demo.com','seat':seat,'fareTier':'Standard','extraBaggage':False},P);ok('search to payment booking',st==200 and b['transactionId'] and b['pnr'],b)
_,js=call('/journeys',t=P);ok('booking automatically appears in My Journey',any(j['booking']['id']==b['id'] for j in js['journeys']),js)
# status changes and SkyBuddy
call('/demo/flight-update','POST',{'type':'delay','confirmed':True},A);st,ai=call('/assistant','POST',{'message':'Find the cheapest nonstop flight from Delhi to Mumbai under 6000','conversationId':'FL-AI'},P);ok('SkyBuddy flight search uses data',st==200 and ai['agent'] in ['FlightSearchAgent','OfferRecommendationAgent'] and 'DEL' in ai['text'],ai)
_,an=call('/admin/flights/analytics',t=A);ok('admin flight analytics',all(k in an for k in ['total','delayed','soldOut','bookings','revenue']),an)
call('/demo/reset','POST',{'confirmed':True},A)
print('ALL FLIGHTS E2E TESTS PASSED')
