import 'dotenv/config';
import Database from 'better-sqlite3';
import {randomBytes,scryptSync} from 'crypto';
import path from 'path';

if(process.env.NODE_ENV==='production'){
  throw new Error('Development account seeding is disabled in production.');
}
const db=new Database(path.join(process.cwd(),'data','skybook.db'));
db.pragma('foreign_keys = ON');
try{db.exec("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")}catch{}
const hash=(password:string)=>{const salt=randomBytes(16).toString('hex');return `${salt}:${scryptSync(password,salt,64).toString('hex')}`};
const accounts=[
 {name:'SkyBook Customer',email:'customer@skybook.com',phone:'9000000001',password:'SkyBook@123',role:'CUSTOMER'},
 {name:'SkyBook Administrator',email:'admin@skybook.com',phone:'9000000002',password:'SkyBook@Admin123',role:'ADMIN'},
 {name:'SkyBook Super Administrator',email:'superadmin@skybook.com',phone:'9000000003',password:'SkyBook@Super123',role:'SUPER_ADMIN'}
];
const upsert=db.prepare(`INSERT INTO users(name,email,phone,password_hash,role,account_status,must_change_password,created_at)
 VALUES(@name,@email,@phone,@passwordHash,@role,'ACTIVE',1,@createdAt)
 ON CONFLICT(email) DO UPDATE SET name=excluded.name,phone=excluded.phone,password_hash=excluded.password_hash,
 role=excluded.role,account_status='ACTIVE',must_change_password=1`);
const run=db.transaction(()=>{for(const a of accounts)upsert.run({...a,passwordHash:hash(a.password),createdAt:new Date().toISOString()})});
run();
console.log(`Seeded ${accounts.length} development accounts with scrypt password hashes and forced password change.`);
db.close();
