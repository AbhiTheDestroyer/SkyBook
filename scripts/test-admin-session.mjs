import{chromium}from'playwright';
for(const account of [{email:'admin@skybook.com',password:'SkyBook@Admin123',heading:'SkyBook Administrator'},{email:'superadmin@skybook.com',password:'SkyBook@Super123',heading:'SkyBook Super Administrator'}]){
 const browser=await chromium.launch({headless:true});const page=await browser.newPage();const errors=[];page.on('console',m=>m.type()==='error'&&errors.push(m.text()));
 await page.goto('http://127.0.0.1:5173/admin/login',{waitUntil:'networkidle'});await page.getByLabel('Email').fill(account.email);await page.getByLabel('Password').fill(account.password);await page.getByRole('button',{name:/Login as administrator/i}).click();await page.waitForURL('**/admin/dashboard');await page.waitForSelector('.adminmain h1');console.log('HEADING',await page.locator('.adminmain h1').first().textContent());
 await page.reload({waitUntil:'networkidle'});if(!page.url().endsWith('/admin/dashboard'))throw Error('refresh redirected');
 await page.getByRole('button',{name:'Logout admin'}).click();await page.waitForTimeout(300);if(!page.url().endsWith('/admin/login'))throw Error('logout route failed');
 await page.goto('http://127.0.0.1:5173/admin/dashboard',{waitUntil:'networkidle'});await page.waitForTimeout(300);if(!page.url().endsWith('/admin/login'))throw Error('protected route accessible after logout');
 console.log('PASS',account.email,'login dashboard refresh logout protected-route',errors.length?'console errors:'+errors.join('|'):'no console errors');await browser.close();
}
