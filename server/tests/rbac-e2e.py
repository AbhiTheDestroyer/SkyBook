#!/usr/bin/env python3
import json,urllib.request,urllib.error,time
B='http://127.0.0.1:3001/api'
def call(path,method='GET',body=None,token=None):
 h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 try:
  with urllib.request.urlopen(urllib.request.Request(B+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers=h),timeout=10)as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  try:d=json.load(e)
  except:d={}
  return e.code,d
def ok(n,x,d=''):
 if not x:raise AssertionError(f'{n}: {d}')
 print('PASS',n)
def login(email,pw):return call('/auth/admin/login','POST',{'email':email,'password':pw})
ss,super=login('superadmin@skybook.com','SkyBook@Super123');ok('super login',ss==200,super);S=super['token']
_,me=call('/auth/me',token=S);ok('super effective all permissions','ROLES.CREATE' in me['permissions'] and 'ADMINS.CREATE' in me['permissions'],me)
code='FLIGHT_OPERATOR_QA';st,role=call('/admin/rbac/roles','POST',{'code':code,'name':'Flight Operator QA'},S)
if st==409:
 roles=call('/admin/rbac/roles',token=S)[1];role=next(x for x in roles if x['code']==code);st=200
ok('create persistent role',st in [200,201],role)
perms=['FLIGHTS.VIEW','FLIGHTS.CREATE','FLIGHTS.UPDATE'];ok('assign role permissions',call(f"/admin/rbac/roles/{role['id']}/permissions",'PUT',{'permissions':perms},S)[0]==200)
email=f"flightop{int(time.time())}@skybook.com";pw='Temporary@123';st,adm=call('/admin/rbac/admins','POST',{'name':'Flight Operator','email':email,'password':pw,'role':code},S);ok('create admin and assign role',st==201,adm)
st,new=login(email,pw);ok('new admin login',st==200,new);T=new['token']
_,auth=call('/auth/me',token=T);ok('effective permissions loaded',set(perms).issubset(auth['permissions']) and 'PAYMENTS.VIEW' not in auth['permissions'],auth)
ok('allowed flights view',call('/admin/flights',token=T)[0]==200)
flight={'number':f'QA{int(time.time())%100000}','airline':'SkyBook Air','origin':'DEL','destination':'BOM','departure':'2026-10-10T10:00','arrival':'2026-10-10T12:00','capacity':6,'fare':6000};st,created=call('/admin/flights','POST',flight,T);ok('allowed flight create',st==201,created)
ok('payments/bookings data denied',call('/admin/bookings',token=T)[0]==403)
ok('roles denied',call('/admin/rbac/roles',token=T)[0]==403)
# revoke create by replacing role permission set
ok('revoke create',call(f"/admin/rbac/roles/{role['id']}/permissions",'PUT',{'permissions':['FLIGHTS.VIEW','FLIGHTS.UPDATE']},S)[0]==200)
_,auth2=call('/auth/me',token=T);ok('permission version/effective state updated','FLIGHTS.CREATE' not in auth2['permissions'] and auth2['permissionVersion']>auth['permissionVersion'],auth2)
ok('direct create denied after revoke',call('/admin/flights','POST',{**flight,'number':flight['number']+'B'},T)[0]==403)
ok('grant create again',call(f"/admin/rbac/roles/{role['id']}/permissions",'PUT',{'permissions':perms},S)[0]==200)
ok('create works after grant',call('/admin/flights','POST',{**flight,'number':flight['number']+'C'},T)[0]==201)
logs=call('/admin/rbac/audit-logs?limit=100',token=S)[1];ok('audit contains grants and flight create',any(x['module']=='PERMISSIONS' for x in logs) and any(x['module']=='FLIGHTS' and x['action']=='CREATE' for x in logs),logs)
# direct deny overrides role
ok('direct deny',call(f"/admin/rbac/admins/{adm['id']}/permission",'PUT',{'permission':'FLIGHTS.CREATE','effect':'DENY'},S)[0]==200)
ok('deny overrides inherited',call('/admin/flights','POST',{**flight,'number':flight['number']+'D'},T)[0]==403)
# customer and unauthenticated boundaries
cust=call('/auth/customer/login','POST',{'email':'customer@skybook.com','password':'SkyBook@123'})[1]['token'];ok('customer admin API denied',call('/admin/flights',token=cust)[0]==403);ok('unauthenticated admin API denied',call('/admin/flights')[0]==401)
# self escalation denied
ok('admin self permission mutation denied',call(f"/admin/rbac/admins/{adm['id']}/permission",'PUT',{'permission':'ADMINS.CREATE','effect':'GRANT'},T)[0]==403)
# logout invalidates
ok('logout',call('/auth/logout','POST',{},T)[0]==200);ok('revoked session rejected',call('/admin/flights',token=T)[0]==401)
print('ALL RBAC E2E TESTS PASSED')
