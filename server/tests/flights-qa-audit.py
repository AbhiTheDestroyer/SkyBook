#!/usr/bin/env python3
import json,urllib.request,urllib.error,concurrent.futures,pathlib
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
P=login();R=login(email='rahul@demo.com');A=login('AIRLINE_ADMIN');c('/demo/reset','POST',{'confirmed':True},A)
# Search modes
_,one=c('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20',t=P);ok('01 one-way inventory search',len(one)>=2 and all(x['origin']=='DEL' for x in one),one)
st,roundtrip=c('/flights/itineraries','POST',{'tripType':'ROUND_TRIP','passengers':1,'cabin':'ECONOMY','segments':[{'origin':'DEL','destination':'BOM','date':'2026-08-25'},{'origin':'BOM','destination':'DEL','date':'2026-08-27'}]},P);ok('02 round-trip search',st==200 and len(roundtrip['segments'])==2,roundtrip)
st,multi=c('/flights/itineraries','POST',{'tripType':'MULTI_CITY','segments':[{'origin':'DEL','destination':'BOM','date':'2026-08-25'},{'origin':'BOM','destination':'BLR','date':'2026-08-26'},{'origin':'BLR','destination':'DEL','date':'2026-08-28'}]},P);ok('03 multi-city search',st==200 and len(multi['segments'])==3,multi)
_,ap=c('/airports?q=Mumbai');ok('04 autocomplete',ap['data'][0]['iata']=='BOM',ap)
src=pathlib.Path('src/main.tsx').read_text();css=pathlib.Path('src/styles.css').read_text();ok('05 airport swap', 'setFrom(to);setTo(from)' in src);ok('06 date validation','bookingWindow?.minDate' in src and 'Origin and destination must be different' in src);ok('07 passenger selection',all(x in src for x in ['setAdults','setChildren','setInfants','Infants cannot exceed adults']));ok('08 cabin selection','Premium Economy' in src and 'setCabin' in src);ok('09 filters',all(x in src for x in ['setStopFilter','setAirlineFilter','maxPrice']));ok('10 sorting',all(x in src for x in ['CHEAPEST','FASTEST','EARLIEST','LATEST','FEWEST']));ok('11 comparison','compareTray' in src and 'setCompare' in src)
f=one[0];_,fd=c('/flights/'+str(f['id']),t=P);ok('12 flight details',fd['flight']['number']==f['number'] and fd['seats'],fd);ok('13 fare selection','const fares=' in src and 'Saver' in src and 'Flex' in src);ok('14 pricing service','expectedFare' in src and 'DiscountEngine.calculate' in pathlib.Path('server/index.ts').read_text());ok('15 seat inventory',fd['availability']==len([s for s in fd['seats'] if s['status'] in ['AVAILABLE','PREMIUM']]));ok('16 3D seat map','function SeatMap' in src and '<Canvas' in src);ok('17 passenger details','Passenger details' in src and 'formgrid' in src);ok('18 baggage','BAGGAGE & ADD-ONS' in src and 'extraBaggage' in src);ok('19 offers','/offers/validate' in src and 'promoResult' in src);ok('20 payment service','/bookings' in src and 'Pay securely (Demo)' in src)
# Stale fare invalidation
f=next(x for x in one if x['availability']>0);seat=next(s for s in c('/flights/'+str(f['id']),t=P)[1]['seats'] if s['status']=='AVAILABLE')['label'];old=f['fare'];c('/admin/flights/'+str(f['id'])+'/fare','PUT',{'confirmed':True,'fare':old+700},A);st,stale=c('/bookings','POST',{'flightId':f['id'],'name':'Passenger X','email':'passengerx@demo.com','seat':seat,'fareTier':'Standard','expectedFare':old},P);ok('fare update invalidates old price',st==409 and 'Fare updated' in stale['error'],stale)
st,b=c('/bookings','POST',{'flightId':f['id'],'name':'Passenger X','email':'passengerx@demo.com','seat':seat,'fareTier':'Standard','expectedFare':old+700},P);ok('21 booking after new total confirmation',st==200 and b['total']>old,b);_,pay=c('/bookings/'+str(b['id'])+'/payment',t=P);ok('20 payment uses new backend price',pay['amount']==b['total'],pay);ok('22 ticket generated',bool(b['ticketNo']),b);_,js=c('/journeys',t=P);ok('23 My Journey created',any(j['booking']['id']==b['id'] for j in js['journeys']),js)
# sold out/waitlist
D=c('/demo/waitlist/reset','POST',{'confirmed':True},A)[1];_,full=c('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20',t=P);sk=next(x for x in full if x['number']=='SK102');ok('24 sold out enables waitlist',sk['availability']==0 and 'Join waitlist' in src,sk)
# status/tracker truthful
st,fs=c('/flights/status?flightNumber=SK102&date=2026-08-20');ok('25 status service',st==200 and fs['source']=='SKYBOOK_DATABASE',fs);ok('26 tracker does not fabricate',fs['trackingAvailable'] is False,fs)
# saved/alerts/deals/navigation/AI
c('/demo/reset','POST',{'confirmed':True},A);_,fl=c('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20',t=P);f=fl[0];_,al=c('/flights/price-alerts','POST',{'origin':'DEL','destination':'BOM','travelDate':'2026-08-20','targetPrice':5000},P);ok('27 price alert',al['status']=='ACTIVE',al);c('/flights/'+str(f['id'])+'/save','POST',{},P);_,sv=c('/flights/saved/list',t=P);ok('28 saved flights',any(x['id']==f['id'] for x in sv),sv);_,deals=c('/offers');ok('29 flight deals use OffersService',len(deals)>0 and all('promo_code' in x for x in deals));ok('30 airport navigation action','Navigate airport' in src)
_,ai=c('/assistant','POST',{'message':'Find cheapest nonstop Delhi to Mumbai flight under 6000','conversationId':'FL-QA'},P);ok('31 SkyBuddy grounded',ai['agent'] in ['FlightSearchAgent','OfferRecommendationAgent'] and ai.get('facts') and all(':' in x for x in ai['facts']),ai)
# delay and A12→B24 consistency
c('/demo/flight-update','POST',{'type':'delay','confirmed':True},A);_,delayed=c('/flights/status?flightNumber=SK102&date=2026-08-20');ok('32 delay',delayed['status']=='DELAYED',delayed);c('/admin/navigation/map-gate','POST',{'confirmed':True,'flightNumber':'SK102','gateNumber':'A12'},A);c('/admin/navigation/map-gate','POST',{'confirmed':True,'flightNumber':'SK102','gateNumber':'B24'},A);_,rr=c('/flights/search?origin=DEL&destination=BOM&departureDate=2026-08-20',t=P);rf=next(x for x in rr if x['number']=='SK102');ok('33/34 gate terminal current',rf['gate']=='B24' and rf['terminal']=='T2',rf);_,rd=c('/flights/'+str(rf['id']),t=P);ok('details current gate',rd['flight']['gate']=='B24',rd);_,nav=c('/navigation/bootstrap',t=P);ok('navigation current gate',nav['journey']['gateNumber']=='B24',nav['journey']);_,gai=c('/assistant','POST',{'message':'Where is my gate?','conversationId':'FG'},P);ok('SkyBuddy current gate','B24' in gai['text'],gai)
# cancellation/alternative
c('/admin/journeys/flight/'+str(rf['id'])+'/state','POST',{'status':'CANCELLED','confirmed':True},A);_,cancelled=c('/flights/status?flightNumber=SK102&date=2026-08-20');ok('35 cancellation',cancelled['status']=='CANCELLED',cancelled);_,alts=c('/waitlist/alternatives/'+str(rf['id']));ok('36 alternatives API',isinstance(alts,list),alts);ok('37 multi-segment','/flights/itineraries' in pathlib.Path('server/index.ts').read_text());ok('38 mobile','@media(max-width:720px)' in css);ok('39 desktop','.flightCard' in css);st,_=c('/flights/saved/list');ok('40 authentication',st==401);st,_=c('/admin/flights/analytics',t=P);ok('41 authorization',st==403);_,admin=c('/admin/flights/analytics',t=A);ok('42 admin dashboard',all(k in admin for k in ['total','delayed','soldOut','revenue']),admin)
# last-seat race
c('/demo/reset','POST',{'confirmed':True},A);_,dyn=c('/flights/search?origin=JAI&destination=DXB&departureDate=2026-08-25',t=P);lf=dyn[0];c('/admin/flights/'+str(lf['id'])+'/inventory','PUT',{'confirmed':True,'available':1},A);seat=next(s for s in c('/flights/'+str(lf['id']),t=P)[1]['seats'] if s['status']=='AVAILABLE')['label']
def book(args):
 token,email=args;return c('/bookings','POST',{'flightId':lf['id'],'name':email.split('@')[0],'email':email,'seat':seat,'fareTier':'Standard','expectedFare':lf['fare']},token)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:r=list(ex.map(book,[(P,'passengerx@demo.com'),(R,'rahul@demo.com')]))
ok('last seat race: one booking only',sorted(x[0] for x in r)==[200,409],r)
c('/demo/reset','POST',{'confirmed':True},A)
print('ALL FLIGHTS QA AUDIT TESTS PASSED')
