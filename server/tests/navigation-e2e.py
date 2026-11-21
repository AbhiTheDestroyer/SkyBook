#!/usr/bin/env python3
import json,urllib.request,urllib.error,pathlib,time
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
def login(role):return call('/auth/demo-session','POST',{'role':role})[1]['token']
P=login('PASSENGER');A=login('AIRLINE_ADMIN');call('/demo/reset','POST',{'confirmed':True},A)
_,boot=call('/navigation/bootstrap',token=P);nodes={n['node_key']:n for n in boot['nodes']}
ok('structured demo graph',boot['airport']['demo'] and len(boot['nodes'])>=35 and len(boot['edges'])>=35)
# Graph integrity: every active node belongs to one connected component and edge metrics are valid.
adj={n['id']:set() for n in boot['nodes']}
for e in boot['edges']:
 if e['from_node'] in adj and e['to_node'] in adj:
  adj[e['from_node']].add(e['to_node'])
  if e['bidirectional']:adj[e['to_node']].add(e['from_node'])
seen={next(iter(adj))};stack=list(seen)
while stack:
 x=stack.pop()
 for y in adj[x]-seen:seen.add(y);stack.append(y)
ok('no disconnected active navigation nodes',len(seen)==len(adj),set(adj)-seen)
ok('all edge distances/times are positive',all(e['distance']>0 and e['walking_time']>0 for e in boot['edges']))
# 1 entrance to B24
st,r=call('/navigation/route','POST',{'start':'t2_entrance_a','destination':'gate_b24','mode':'FASTEST'});fast=r['selected'];ok('01 entrance to Gate B24 route',st==200 and fast['nodes'][0]['node_key']=='t2_entrance_a' and fast['nodes'][-1]['node_key']=='gate_b24',fast)
ok('distance/time/floor generated',fast['distance']>0 and fast['walkingTime']>0 and fast['floorChanges']==1)
ok('reported distance equals traversed edges',fast['distance']==round(sum(e['distance'] for e in fast['edges'])),fast)
ok('reported time equals traversed edge time',fast['walkingTime']==max(1,__import__('math').ceil(sum(e['walking_time'] for e in fast['edges'])/60)),fast)
ok('turn-by-turn generated from graph',len(fast['directions'])==len(fast['nodes']) and all(x['instruction'] for x in fast['directions']))
_,cached=call('/navigation/route','POST',{'start':'t2_entrance_a','destination':'gate_b24','mode':'FASTEST'});ok('common route cache',cached['selected'].get('cacheHit') is True,cached['selected'])
# 2 security to B24
_,security_route=call('/navigation/route','POST',{'start':'t2_security_entry','destination':'gate_b24','mode':'FASTEST'});ok('02 Security to Gate B24',security_route['selected']['nodes'][0]['node_key']=='t2_security_entry' and security_route['selected']['nodes'][-1]['node_key']=='gate_b24')
# 3-5 routes from gate to facilities
_,to_restroom=call('/navigation/route','POST',{'start':'gate_b24','destination':'t2_restroom_f2','mode':'SHORTEST'});ok('03 Gate B24 to Restroom',to_restroom['selected']['nodes'][-1]['type']=='RESTROOM')
_,to_lounge=call('/navigation/route','POST',{'start':'gate_b24','destination':'t2_lounge','mode':'FASTEST'});ok('04 Gate B24 to Lounge',to_lounge['selected']['nodes'][-1]['type']=='LOUNGE')
_,to_restaurant=call('/navigation/route','POST',{'start':'gate_b24','destination':'t2_restaurant','mode':'FASTEST'});ok('05 Gate B24 to Restaurant',to_restaurant['selected']['nodes'][-1]['type']=='RESTAURANT')
# 6 explicit floor transition
_,floor_route=call('/navigation/route','POST',{'start':'t2_elevator_f1','destination':'t2_elevator_f2','mode':'ACCESSIBLE'});ok('06 Floor 1 to Floor 2',floor_route['selected']['floorChanges']==1 and floor_route['selected']['nodes'][0]['floor_number']==1 and floor_route['selected']['nodes'][-1]['floor_number']==2)
# 7 reverse terminal transfer
_,t1t2=call('/navigation/route','POST',{'start':'t1_entrance','destination':'t2_entrance_a','mode':'ACCESSIBLE'});ok('07 Terminal 1 to Terminal 2',t1t2['selected']['terminalTransfers']==1 and any(e.get('transport_type')=='SHUTTLE' for e in t1t2['selected']['edges']))
# route alternatives
opts={x['mode']:x for x in r['options']};ok('route alternatives',all(x in opts for x in ['FASTEST','SHORTEST','ACCESSIBLE','LOW_WALKING','FAMILY']))
ok('09 shortest route minimizes distance',opts['SHORTEST']['distance']<=opts['FASTEST']['distance'],opts)
ok('10 fastest route minimizes time',opts['FASTEST']['walkingTime']<=opts['SHORTEST']['walkingTime'],opts)
ok('fastest/shortest use different weighted paths', [n['node_key'] for n in opts['FASTEST']['nodes']]!=[n['node_key'] for n in opts['SHORTEST']['nodes']],opts)
ok('04 accessible avoids stairs',opts['ACCESSIBLE']['accessible'] and all(n['type']!='STAIRS' for n in opts['ACCESSIBLE']['nodes']),opts['ACCESSIBLE'])
ok('low-walking avoids stairs',all(n['type']!='STAIRS' for n in opts['LOW_WALKING']['nodes']),opts['LOW_WALKING'])
# 2 SkyBuddy uses verified route
st,ai=call('/assistant','POST',{'message':'How do I get to Gate B24?','conversationId':'NAV-AUDIT'},P);ok('02 SkyBuddy gate route',st==200 and ai['agent']=='AirportNavigationAgent' and str(fast['distance']) in ai['text'] and 'SEEDED' not in ai.get('facts',[]),ai)
# 3 nearby POI from B24
st,near=call('/navigation/nearby?nodeId='+str(nodes['gate_b24']['id'])+'&categories=RESTROOM');ok('03 restroom near B24',st==200 and near and near[0]['category']=='RESTROOM' and near[0]['distance']>0,near)
st,ai2=call('/assistant','POST',{'message':'Find a restroom near Gate B24.','conversationId':'NAV-POI'},P);ok('SkyBuddy nearby POI',st==200 and ai2['intent']=='FACILITY' and near[0]['name'] in ai2['text'],ai2)
# search/autocomplete
_,search=call('/navigation/search?q=gat');ok('gate autocomplete',len(search)>=6 and any(x['gate_number']=='B24' for x in search),search)
_,rest=call('/navigation/search?q=rest');ok('POI autocomplete',any('Restroom' in x['name'] for x in rest),rest)
# 5 flight aware
ok('05 flight-aware gate mapping',boot['journey']['number']=='SK102' and boot['journey']['gateNumber']=='B24' and boot['journey']['gateNode']['node_key']=='gate_b24',boot['journey'])
_,public_boot=call('/navigation/bootstrap');ok('personalized journey requires authentication',public_boot['journey'] is None,public_boot)
# session and arrival
st,sess=call('/navigation/sessions','POST',{'start':nodes['t2_entrance_a']['id'],'destination':nodes['gate_b24']['id'],'mode':'ACCESSIBLE'},P);ok('navigation session starts',st==200 and sess['status']=='NAVIGATING',sess)
st,arr=call('/navigation/sessions/'+str(sess['sessionId']),'PUT',{'progress':100},P);ok('10 arrival detection',st==200 and arr['status']=='ARRIVED' and arr['progress']==100,arr)
# 9 changed destination recalculates
_,changed=call('/navigation/route','POST',{'start':'t2_security_exit','destination':'t2_lounge','mode':'FASTEST'});ok('09 destination change recalculates',changed['selected']['nodes'][-1]['node_key']=='t2_lounge' and changed['selected']['distance']!=fast['distance'])
# security completed route doesn't go back to entrance/security entry
_,postsec=call('/navigation/route','POST',{'start':'t2_security_exit','destination':'gate_b24','mode':'FASTEST'});ok('security-aware start',all(n['node_key'] not in ['t2_entrance_a','t2_security_entry'] for n in postsec['selected']['nodes']))
# terminal transfer
_,transfer=call('/navigation/route','POST',{'start':'t2_entrance_a','destination':'gate_a12','mode':'ACCESSIBLE'});ok('terminal transfer',transfer['selected']['terminalTransfers']>=1 and any(e.get('transport_type')=='SHUTTLE' for e in transfer['selected']['edges']),transfer['selected'])
# 6 operational gate change updates journey and route
st,_=call('/demo/flight-update','POST',{'type':'gate','confirmed':True},A);ok('admin gate change accepted',st==200)
_,changedBoot=call('/navigation/bootstrap',token=P);ok('06 gate change destination updated',changedBoot['journey']['gateNumber']=='A12' and changedBoot['journey']['gateNode']['node_key']=='gate_a12',changedBoot['journey'])
# Notification includes navigation-aware gate change
_,notes=call('/notifications',token=P);ok('gate-change navigation notification',any('A12' in n['message'] and 'route' in n['message'].lower() for n in notes),notes)
# 7/8 fallbacks: core route is independent from WebGL and AI
src=pathlib.Path('src/main.tsx').read_text();css=pathlib.Path('src/styles.css').read_text()
ok('15 functional 2D navigation', 'AirportMap2DGraph' in src and 'routeLine2d' in src and 'onPointerMove' in src)
ok('16 structured 3D visualization', 'AirportGraph3D' in src and 'routePoints' in src and '<Line points={routePoints}' in src)
ok('2D/3D share navigation state', 'nodes={boot.nodes} route={route} currentId={current} destinationId={destination}' in src)
ok('17 3D fallback to 2D',"3D unavailable. Functional 2D navigation is active." in src and "if(!available)setMode('2d')" in src)
ok('18 manual navigation independent of AI',fast['source']=='SEEDED_DEMO_GRAPH')
ok('19 wrong-direction/manual recalculation', 'Location changed. Recalculating from the selected landmark' in src and "setStatus('ROUTE_READY')" in src)
ok('21 mobile navigation layout', '@media(max-width:620px)' in css and '.turnPanel' in css and '.nearbyDrawer' in css)
ok('22 keyboard and accessibility controls', 'aria-label="Zoom in"' in src and 'Use arrow keys to pan' in src and 'prefers-reduced-motion' in css)
st,err=call('/navigation/route','POST',{'start':'missing','destination':'gate_b24','mode':'FASTEST'});ok('invalid node API error',st==422 and 'not found' in err['error'].lower(),err)
st,err=call('/navigation/route','POST',{'start':'t2_entrance_a','destination':'gate_b24','mode':'FLYING'});ok('invalid route-mode API error',st==400,err)
# Admin authorization and editor mutation
st,_=call('/admin/navigation',token=P);ok('passenger blocked from map admin',st==403)
_,admin=call('/admin/navigation',token=A);floor=admin['nodes'][0]['floor_id'];key='audit_node_'+str(int(time.time()))
st,new=call('/admin/navigation/nodes','POST',{'nodeKey':key,'floorId':floor,'name':'Audit Information Point','type':'INFORMATION','x':2,'y':0,'z':8,'accessible':True},A);ok('admin adds graph node',st==200 and new['node_key']==key,new)
st,moved=call('/admin/navigation/nodes/'+str(new['id']),'PUT',{'x':3,'z':9},A);ok('admin moves node',st==200 and moved['x']==3,moved)
st,_=call('/admin/navigation/nodes/'+str(new['id']),'DELETE',{'confirmed':True},A);ok('admin deactivates node',st==200)
# reset gate for core regression
call('/demo/reset','POST',{'confirmed':True},A)
print('ALL NAVIGATION E2E TESTS PASSED')
