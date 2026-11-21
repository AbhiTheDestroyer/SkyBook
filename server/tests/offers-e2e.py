#!/usr/bin/env python3
import json,urllib.request,urllib.error,concurrent.futures,time,pathlib
BASE='http://127.0.0.1:3001/api'
def call(path,method='GET',body=None,token=None):
 data=json.dumps(body).encode() if body is not None else None;h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 req=urllib.request.Request(BASE+path,data=data,method=method,headers=h)
 try:
  with urllib.request.urlopen(req,timeout=15)as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  try:d=json.load(e)
  except:d={'error':e.read().decode()}
  return e.code,d
def ok(name,cond,data=''):
 if not cond:raise AssertionError(f'{name}: {data}')
 print('PASS',name)
def login(role='PASSENGER',email=None):
 _,d=call('/auth/demo-session','POST',{'role':role,**({'email':email}if email else{})});return d['token']
P=login();R=login(email='rahul@demo.com');A=login('AIRLINE_ADMIN')
call('/demo/reset','POST',{'confirmed':True},A)
_,alloffers=call('/offers');by={x['promo_code']:x for x in alloffers}
ok('01 active offer',by['SAVE15']['status']=='ACTIVE')
ok('02 expired offer',by['MONSOON12']['status']=='EXPIRED')
ok('03 upcoming offer',by['SEPTEMBER600']['status']=='UPCOMING')
# A genuinely new account (no completed bookings) receives the welcome offer.
new_email=f"new{int(time.time()*1000)}@example.com"
st,new_user=call('/auth/register','POST',{'name':'New Offer User','email':new_email,'phone':'9000000000','password':'Welcome@123'});ok('new user registration',st==200,new_user)
st,new_login=call('/auth/login','POST',{'email':new_email,'password':'Welcome@123'});N=new_login['token'];ok('new user session',st==200 and bool(N))
_,welcome_flights=call('/flights?from=DEL&to=DXB&date=2026-08-25');welcome_flight=welcome_flights[0]
st,d=call('/offers/validate','POST',{'code':'SKYWELCOME500','flightId':welcome_flight['id'],'fareTier':'Saver'},N);ok('01 new user receives welcome offer',st==200 and d['discount']==500,d)
_,flights=call('/flights?from=DEL&to=BOM&date=2026-08-25');f=flights[0]
st,d=call('/offers/validate','POST',{'code':'NOTREAL','flightId':f['id'],'fareTier':'Saver'},P);ok('04 invalid promo',st==422 and 'not found' in d['reasons'][0].lower(),d)
st,badbook=call('/bookings','POST',{'flightId':f['id'],'name':'Passenger X','email':'passengerx@demo.com','seat':'14F','fareTier':'Standard','promoCode':'NOTREAL'},P);ok('12 booking revalidates promo server-side',st==409 and 'not found' in badbook['error'].lower(),badbook)
_,fd=call('/flights/'+str(f['id']));ok('invalid promo rolls back seat',next(x for x in fd['seats'] if x['label']=='14F')['status']=='AVAILABLE',fd)
st,d=call('/offers/apply','POST',{'confirmed':True,'code':'MONSOON12','flightId':f['id'],'fareTier':'Flex'},P);ok('04 expired offer rejected at apply',st==422 and any('expired' in x.lower() for x in d['reasons']),d)
st,d=call('/offers/validate','POST',{'code':'SAVE15','flightId':f['id'],'fareTier':'Saver'},P);ok('05 minimum fare',st==422 and any('Minimum fare' in x for x in d['reasons']),d)
_,intl=call('/flights?from=DEL&to=DXB&date=2026-08-25');fi=intl[0]
st,d=call('/offers/validate','POST',{'code':'INTERNATIONAL15','flightId':fi['id'],'fareTier':'Business','cabin':'BUSINESS'},P);ok('06 maximum discount',st==200 and d['discount']==3000,d)
st,d=call('/offers/validate','POST',{'code':'JAI-MUM','flightId':f['id'],'fareTier':'Flex'},P);ok('07 route restriction',st==422 and any('route' in x.lower() for x in d['reasons']),d)
code='AIR'+str(int(time.time()))[-6:]
payload={'title':'Airline restriction audit','description':'test','category':'DOMESTIC','promoCode':code,'discountType':'FIXED_AMOUNT','discountValue':300,'minimumFare':0,'startAt':'2026-08-01T00:00:00.000Z','expiresAt':'2026-12-31T23:59:59.000Z','status':'ACTIVE','usageLimit':20,'perUserLimit':2,'eligibility':'ALL','airlines':['Nonexistent Air'],'cabins':['ECONOMY']}
_,airOffer=call('/admin/offers','POST',payload,A)
st,d=call('/offers/validate','POST',{'code':code,'flightId':f['id'],'fareTier':'Saver'},P);ok('08 airline restriction',st==422 and any('airline' in x.lower() for x in d['reasons']),d)
st,d=call('/offers/validate','POST',{'code':'BUSINESS10','flightId':fi['id'],'fareTier':'Saver','cabin':'ECONOMY'},P);ok('09 cabin restriction',st==422 and any('cabin' in x.lower() for x in d['reasons']),d)
st,d=call('/offers/validate','POST',{'code':'STUDENT500','flightId':f['id'],'fareTier':'Flex'},P);ok('10 student ineligible',st==422 and any('student' in x.lower() for x in d['reasons']),d)
st,d=call('/offers/validate','POST',{'code':'STUDENT500','flightId':f['id'],'fareTier':'Flex'},R);ok('10b verified demo student',st==200,d)
st,d=call('/offers/validate','POST',{'code':'SKYWELCOME500','flightId':f['id'],'fareTier':'Flex'},P);ok('11 new-user history eligibility',st==422 and any('completed booking' in x for x in d['reasons']),d)
# Admin management lifecycle and immutable auditing.
st,draft=call('/admin/offers','POST',{**payload,'promoCode':'LIM'+str(int(time.time()))[-6:],'title':'One use race offer','airlines':[],'usageLimit':1,'perUserLimit':1},A);ok('22 admin create',st==200,draft)
st,edited=call('/admin/offers/'+str(draft['id']),'PUT',{'title':'One use race offer edited'},A);ok('22b admin edit',st==200 and 'edited' in edited['title'],edited)
st,_=call('/admin/offers/'+str(draft['id'])+'/deactivate','POST',{'confirmed':True},A);ok('22c admin deactivate',st==200)
st,_=call('/admin/offers/'+str(draft['id'])+'/activate','POST',{'confirmed':True},A);ok('22d admin activate',st==200)
# Offer apply/remove quote.
st,q=call('/offers/apply','POST',{'confirmed':True,'code':'INTERNATIONAL15','flightId':fi['id'],'fareTier':'Business','cabin':'BUSINESS','seatFee':500,'addOns':1200},P);ok('15 apply offer',st==200 and q['breakdown']['finalTotal']<q['breakdown']['baseFare']+2456,q)
st,rm=call('/offers/remove','POST',{'flightId':fi['id'],'fareTier':'Business','seatFee':500,'addOns':1200},P);ok('15 offer removal',st==200 and rm['breakdown']['discount']==0,rm)
# End-to-end route offer booking.
_,jf=call('/flights?from=JAI&to=BOM&date=2026-08-25');jf=jf[-1]
st,val=call('/offers/validate','POST',{'code':'JAI-MUM','flightId':jf['id'],'fareTier':'Flex'},P);ok('14 eligibility before booking',st==200 and val['discount']==700,val)
st,b=call('/bookings','POST',{'flightId':jf['id'],'name':'Passenger X','email':'passengerx@demo.com','seat':'14A','fareTier':'Flex','extraBaggage':False,'promoCode':'JAI-MUM','total':1},P);ok('16 offer + booking',st==200 and b['savings']==700,b)
ok('17 discounted payment amount',b['breakdown']['finalTotal']==b['total'] and b['breakdown']['discount']==700,b)
st,payment=call('/bookings/'+str(b['id'])+'/payment',token=P);ok('15 payment service received backend total',st==200 and payment['amount']==b['total'] and payment['status']=='SUCCESS',payment)
ok('13 frontend price manipulation ignored',b['total']>1,b)
_,an=call('/admin/offers/analytics',token=A);ok('usage tracking',an['totals']['redemptions']>=1,an)
st,cancel=call('/bookings/'+str(b['id'])+'/cancel','POST',{'confirmed':True},P);ok('18 offer + cancellation',st==200,cancel)
ok('19 discounted refund',cancel['refund']['amount']==b['total']-cancel['refund']['fee'],(b,cancel))
_,an2=call('/admin/offers/analytics',token=A);ok('redemption history retained after refund',an2['totals']['redemptions']>=1,an2)
# Per-user limit remains enforced on successful history.
_,jf2=call('/flights?from=JAI&to=BOM&date=2026-08-26');jf2=jf2[0]
st,d=call('/offers/validate','POST',{'code':'JAI-MUM','flightId':jf2['id'],'fareTier':'Flex'},P);ok('13 per-user limit',st==422 and any('already used' in x.lower() for x in d['reasons']),d)
# Global usage race: reset redemption state, create isolated one-use offer and two users book different seats.
call('/demo/reset','POST',{'confirmed':True},A)
_,racef=call('/flights?from=DEL&to=BOM&date=2026-08-27');racef=racef[0]
racecode='RACE'+str(int(time.time()))[-6:]
_,race=call('/admin/offers','POST',{**payload,'promoCode':racecode,'title':'Atomic final coupon','airlines':[],'usageLimit':1,'perUserLimit':1},A)
def book(args):
 token,email,seat=args;return call('/bookings','POST',{'flightId':racef['id'],'name':email.split('@')[0],'email':email,'seat':seat,'fareTier':'Standard','extraBaggage':False,'promoCode':racecode},token)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:res=list(ex.map(book,[(P,'passengerx@demo.com','14A'),(R,'rahul@demo.com','14B')]))
ok('12 usage-limit atomic race',sorted(x[0] for x in res)==[200,409],res)
ok('14 duplicate redemption prevented',len([x for x in res if x[0]==200])==1,res)
# AI offer recommendation comes from DB.
st,ai=call('/assistant','POST',{'message':'Find a flight from Jaipur to Mumbai and tell me the best offer','conversationId':'OFFER-AUDIT'},P);ok('20 AI recommendation',st==200 and ai['agent']=='OfferRecommendationAgent' and any(x['promo_code'] in ai['text'] for x in alloffers),ai)
# Save/share backing APIs.
st,sv=call('/offers/save','POST',{'offerId':by['SAVE15']['id']},P);_,saved=call('/offers/saved/list',token=P);ok('saved offers',st==200 and any(x['id']==by['SAVE15']['id'] for x in saved),saved)
_,notes=call('/notifications',token=P);ok('24 saved-offer notification',any('SAVE15' in x['message'] for x in notes),notes)
# Mobile CSS assertions (responsive bottom sheet, horizontal categories, sticky apply actions).
src=pathlib.Path('src/main.tsx').read_text();css=pathlib.Path('src/styles.css').read_text();ok('21 mobile UI rules', '@media(max-width:620px)' in css and '.offerCategories' in css and 'align-items:end' in css)
ok('22 expiry countdown uses actual timestamp', 'Date.parse(date)-Date.now()' in src and 'setInterval(tick,60000)' in src)
st,_=call('/admin/offers/analytics',token=P);ok('unauthorized admin access blocked',st==403)
# Archive is non-destructive.
st,_=call('/admin/offers/'+str(airOffer['id']),'DELETE',{'confirmed':True},A);ok('22e admin archive',st==200)
call('/demo/reset','POST',{'confirmed':True},A)
print('ALL OFFER E2E TESTS PASSED')
