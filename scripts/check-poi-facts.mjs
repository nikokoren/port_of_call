// Real archived AIS + reviewed static fact/POI reference scenarios.
// No vessel position, timestamp, camera, or production fact clock is changed.
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
import {geometry} from './visual-geometry.mjs';
import {previewPixels} from './preview-pixels.mjs';
const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const cases=[
 ['seattle-locks','seattle-candidates',5,'full','portrait','Ballard Locks'],
 ['seattle-terminal-blocked','seattle-candidates',7,'full','x',null],
 ['seattle-needle','seattle-candidates',6,'full','og','Space Needle'],
 ['seattle-dark','seattle-candidates',6,'full','og','Space Needle',true],
 ['seattle-spotlight','seattle-candidates-spotlight',6,'full','x','Space Needle'],
 ['hamburg-hall','hamburg-pois',2,'full','og','Elbphilharmonie'],
 ['helsinki-market-blocked','helsinki-pois',6,'full','portrait',null],
 ['helsinki-edge-clipped','helsinki-pois',6,'full','og',null],
 ['helsinki-fortress','helsinki-pois',1,'full','og',null],
 ['turku-museum','turku-pois',10,'full','og','Forum Marinum'],
 ['rauma-old-town','rauma-pois',0,'full','og',null],
 ['helsinki-half','helsinki-pois',6,'half_vertical','og',null],
 ['seattle-small','seattle-candidates',5,'quadrant','og',null],
 ['seattle-portrait-half','seattle-candidates',7,'half_vertical','portrait',null],
 ['seattle-facts-off','seattle-candidates',6,'full','og',null,false,false]
];
const results=[];
try{
 for(const [name,fixture,index,layout,device,expected,dark=false,facts=true] of cases.filter(c=>!process.env.CASE_PREFIX||c[0].startsWith(process.env.CASE_PREFIX))){
  const big=['x','portrait'].includes(device);
  const page=await browser.newPage({viewport:{width:device==='portrait'?780:big?1040:800,height:device==='portrait'?1040:big?780:480},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
   const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));
   await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
  });
  await page.goto(`http://127.0.0.1:8787/?fixture=${fixture}&layout=${layout}&device=${device}&labels=on&facts=${facts}&legend=true&poi-review=true&fact=${index}&dark=${dark}`);
  await page.waitForFunction(()=>document.querySelector('.poc')?.dataset.mapReady==='true'&&window.TRMNL_PLUGINS_READY===true,{timeout:40000});
  await page.evaluate(()=>document.fonts.ready);
  const g=await page.evaluate(geometry);
  const state=await page.evaluate(()=>({fact:document.querySelector('[data-poc-port-fact]')?.textContent,
   factVisible:!!document.querySelector('[data-poc-port-fact]')?.offsetHeight,
   labelOrder:[...document.querySelectorAll('.poc__landmark,.poc__label')].map(n=>({type:n.classList.contains('poc__landmark')?'poi':'ship',name:n.textContent})),
   related:[...document.querySelectorAll('.poc__landmark-data li[data-related="true"]')].map(n=>n.dataset.name),
   landmarks:[...document.querySelectorAll('.poc__landmark')].map(n=>n.textContent),
   candidates:[...document.querySelectorAll('.poc__landmark-data li')].map(n=>n.dataset.name),
   center:document.querySelector('.poc').__portOfCallMap.getCenter().toArray(),
   zoom:document.querySelector('.poc').__portOfCallMap.getZoom()}));
  state.relatedPins=await page.evaluate(()=>{
   const root=document.querySelector('.poc'),map=root.__portOfCallMap,r=root.getBoundingClientRect(),k=r.width/root.offsetWidth;
   const unit=Math.max(1,parseFloat(getComputedStyle(root.closest('.screen')).getPropertyValue('--ui-scale'))||1);
   const box=n=>{const b=n.getBoundingClientRect();return[(b.left-r.left)/k,(b.top-r.top)/k,(b.right-r.left)/k,(b.bottom-r.top)/k];};
   const hits=(a,b)=>a[0]<b[2]&&b[0]<a[2]&&a[1]<b[3]&&b[1]<a[3];
   return [...root.querySelectorAll('.poc__landmark-data li[data-related="true"]')].map(n=>{
    const p=map.project([+n.dataset.lon,+n.dataset.lat]),pin=[p.x-6*unit,p.y-16*unit,p.x+6*unit,p.y+unit];
    return{name:n.dataset.name,pinInside:pin[0]>=8&&pin[1]>=8&&pin[2]<=root.offsetWidth-8&&pin[3]<=root.offsetHeight-8,
     blockingHulls:[...root.querySelectorAll('.poc__ship')].filter(s=>hits(pin,box(s.querySelector('svg')))).map(s=>s.dataset.id)};
   });
  });
  console.log(name,JSON.stringify(state.landmarks),JSON.stringify(state.relatedPins));
  for(const [index,label] of state.labelOrder.entries()){
   if(label.type!=='poi')continue;
   const firstShip=state.labelOrder.findIndex(n=>n.type==='ship');
   if(firstShip<0)continue;
   if(state.factVisible&&state.related.includes(label.name))assert.ok(index<firstShip,name+': related POI reserves space first');
   else assert.ok(index>firstShip,name+': ordinary POI yields to ship names');
  }
  assert.deepEqual(errors,[]);
  if(expected)assert.ok(state.landmarks.includes(expected),name+': related POI missing; '+JSON.stringify(state));
  for(const key of ['landmarksClear','landmarkPinsExact','mapCountMatches','countSuffixTogether','countDividerSpaced',
   'cardAtCorner','cardInside','spotlightInside','spotlightClear','spotlightConnected','attributionClear','attributionInside','labelContentsValid'])
   assert.equal(g[key],true,name+' '+key);
  for(const key of ['labelCollisions','leaderCollisions','labelsOutside','hiddenShips','textOverflow'])assert.equal(g[key],0,name+' '+key);
  assert.ok(g.maxProjectionError<1);
  const pixels=previewPixels(await page.locator('.screen').screenshot({path:`docs/screenshots/poi-${name}.png`}));
  results.push({name,fixture,fact_index:index,layout,device,expected,dark,facts,...state,geometry:g,pixels,errors});await page.close();
 }
 await writeFile(process.env.CASE_PREFIX?'var/poi-subset.json':'docs/screenshots/results-poi-facts.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}
