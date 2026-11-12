// Synthetic DOM-only geometry test. Never save these invented fixes as a fixture,
// image, production observation or evidence of an actual maritime movement.
import {chromium} from 'playwright';
const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:800,height:480}});
 if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
  const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));
  await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
 });
 await page.goto('http://127.0.0.1:8787/?fixture=rauma-spotlight&labels=on');
 await page.waitForFunction(()=>document.querySelector('.poc')?.dataset.mapReady==='true'&&window.TRMNL_PLUGINS_READY===true);
 await page.evaluate(()=>{
  const root=document.querySelector('.poc'),map=root.__portOfCallMap;
  const ship=root.querySelector('.poc__data li[data-featured="true"]');
  const p=map.project([+ship.dataset.lon,+ship.dataset.lat]),ts=Number.isFinite(Number(ship.dataset.reported))?Number(ship.dataset.reported)*1000:Date.parse(ship.dataset.reported);
  const ol=root.querySelector('.poc__trail-data');ol.replaceChildren();
  [[40,20],[20,10],[0,0]].forEach(([dx,dy],i)=>{
   const point=map.unproject([p.x+dx,p.y+dy]),li=document.createElement('li');
   li.dataset.lon=point.lng;li.dataset.lat=point.lat;li.dataset.at=new Date(ts-(2-i)*120000).toISOString();ol.appendChild(li);
  });
  map.resize();
 });
 await page.waitForFunction(()=>document.querySelectorAll('.poc__trail-ink').length===2,{timeout:10000});
 const actual=await page.evaluate(()=>{
  const root=document.querySelector('.poc'),map=root.__portOfCallMap;
  const points=[...root.querySelectorAll('.poc__trail-data li')].map(n=>map.project([+n.dataset.lon,+n.dataset.lat]));
  return [...root.querySelectorAll('.poc__trail-ink')].every((line,i)=>Math.hypot(+line.getAttribute('x1')-points[i].x,+line.getAttribute('y1')-points[i].y)<.01&&Math.hypot(+line.getAttribute('x2')-points[i+1].x,+line.getAttribute('y2')-points[i+1].y)<.01);
 });
 if(!actual)throw new Error('Trail moved its input fixes');
 console.log('Synthetic DOM trail test passed: two exact projected segments; no image captured.');
}finally{await browser.close();}
