// Approved camera/reference-only previews: no simulated vessel observations.
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
const approved=JSON.parse(await readFile('docs/approved-framing.json','utf8')).harbors;
const cases=Object.keys(approved).flatMap(port=>[['full','og'],['full','x']].map(([layout,device])=>({port,layout,device})));
for(const device of ['og','x'])for(const layout of ['half_horizontal','half_vertical','quadrant'])cases.push({port:'seattle',layout,device});
for(const port of ['seattle','helsinki','rotterdam'])cases.push({port,layout:'full',device:'portrait'});
cases.push({port:'seattle',layout:'full',device:'og-portrait'});
const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const results=[];
try{
 for(const c of cases){
  const x=['x','portrait'].includes(c.device),profile=x?'x':'og',camera=approved[c.port][profile];
  const page=await browser.newPage({viewport:{width:c.device==='portrait'?780:c.device==='og-portrait'?480:x?1040:800,height:c.device==='portrait'?1040:c.device==='og-portrait'?800:x?780:480},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
   const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
  });
  await page.goto(`http://127.0.0.1:8787/?framing=approved&port=${c.port}&layout=${c.layout}&device=${c.device}&facts=true`);
  await page.waitForFunction(()=>document.querySelector('.poc')?.dataset.mapReady==='true'&&window.TRMNL_PLUGINS_READY===true,{timeout:40000});
  const measured=await page.evaluate(focus=>{
   const root=document.querySelector('.poc'),map=root.__portOfCallMap,r=root.getBoundingClientRect(),k=r.width/root.offsetWidth;
   const b=root.querySelector('[data-poc-box]').getBoundingClientRect(),card={right:(b.right-r.left)/k,top:(b.top-r.top)/k},W=root.clientWidth,H=root.clientHeight;
   const scale=Math.max(1,parseFloat(getComputedStyle(root.closest('.screen')).getPropertyValue('--ui-scale'))||1),g=12*scale;
   let open=(W-card.right)*H>=W*card.top?[card.right+g,g,W-g,H-g]:[g,g,W-g,card.top-g];
   if(open[2]-open[0]<40||open[3]-open[1]<40)open=[g,g,W-g,H-g];
   const p=map.project(focus),expected=[(open[0]+open[2])/2,(open[1]+open[3])/2];
   return{device:root.dataset.cameraDevice,zoom:map.getZoom()-Math.log2(scale),center:map.getCenter().toArray(),anchor:[p.x,p.y],expectedAnchor:expected,
    anchorError:Math.hypot(p.x-expected[0],p.y-expected[1]),ships:root.querySelectorAll('.poc__ship').length,landmarks:root.querySelectorAll('.poc__landmark').length,
    viewportInside:root.scrollHeight<=root.clientHeight+1,notice:root.querySelector('[data-editor-count]').textContent};
  },camera.focus);
  assert.deepEqual(errors,[]);assert.equal(measured.device,profile);assert.equal(measured.zoom,camera.zoom);assert.ok(measured.anchorError<1,c.port+' / '+c.device+': exported harbor focus drifted '+JSON.stringify(measured));
  assert.equal(measured.ships,0);assert.equal(measured.viewportInside,true);assert.match(measured.notice,/Map framing preview/);
  const name=`approved-${c.port}-${c.device}`;
  if(c.layout==='full'&&['og','x'].includes(c.device)&&['seattle','helsinki','singapore','rotterdam'].includes(c.port))await page.locator('.screen').screenshot({path:'docs/screenshots/'+name+'.png'});
  results.push({...c,expected:camera,mapOnly:true,...measured,errors});console.log(c.port,c.layout,c.device,'zoom',measured.zoom,'anchor error',measured.anchorError.toFixed(3));await page.close();
 }
 await writeFile('docs/screenshots/results-approved-framing.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}
