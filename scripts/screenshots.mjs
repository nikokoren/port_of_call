import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const cases=[
 ['og-helsinki','full','og','helsinki'],['og-turku','full','og','turku'],['og-rauma','full','og','rauma'],
 ['og-half-horizontal','half_horizontal','og','helsinki'],['og-half-vertical','half_vertical','og','helsinki'],
 ['og-quadrant','quadrant','og','helsinki'],['x-landscape','full','x','helsinki'],['x-portrait','full','portrait','turku'],
 ['x-half-horizontal','half_horizontal','x','helsinki'],['x-half-vertical','half_vertical','x','turku'],['x-quadrant','quadrant','x','rauma'],
 ['og-dark','full','og','helsinki',true],['og-one-bit','full','onebit','helsinki'],['og-empty','quadrant','og','empty'],
 ['og-stale','full','og','stale'],['og-unavailable','half_horizontal','og','unavailable'],['og-warming','quadrant','og','warming'],
 ['og-map-error','full','og','helsinki',false,true],
 ['og-demo-density','full','og','demo']
];
await mkdir('docs/screenshots',{recursive:true});
const results=[];
try {
 for(const [name,layout,device,fixture,dark=false,blockTiles=false] of cases.filter(c=>!process.env.CASE_PREFIX||c[0].startsWith(process.env.CASE_PREFIX))){
  const page=await browser.newPage({viewport:{width:device==='portrait'?1404:device==='x'?1872:800,height:device==='portrait'?1872:device==='x'?1404:480},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  if(blockTiles)await page.route(/^https:\/\/maps\.trmnl\.com\//,r=>r.abort());
  if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
   if(blockTiles&&route.request().url().startsWith('https://maps.trmnl.com/')){await route.abort();return;}
   try{const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));
    await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
   }catch{await route.abort();}
  });
  await page.goto(`http://127.0.0.1:8787/?layout=${layout}&device=${device}&fixture=${fixture}&labels=on&dark=${dark}`);
  await page.waitForFunction(()=>document.querySelector('.poc')?.dataset.mapReady,{timeout:35000});
  await page.evaluate(()=>document.fonts.ready);
  await page.waitForFunction(()=>window.TRMNL_PLUGINS_READY===true,{timeout:25000});
  const status=await page.evaluate(()=>({ready:document.querySelector('.poc').dataset.mapReady,
   markers:document.querySelectorAll('.poc__ship').length,attribution:document.body.innerText.includes('OpenStreetMap'),
   overflow:document.querySelector('.poc').scrollHeight>document.querySelector('.poc').clientHeight,
   text:document.querySelector('.poc__notice').innerText}));
  if(errors.length||status.ready!==(blockTiles?'error':'true')||!status.attribution||status.overflow)throw new Error(name+': '+JSON.stringify({status,errors}));
  if(!blockTiles && ['helsinki','turku','rauma','demo','stale'].includes(fixture)&&status.markers===0)throw new Error(name+': no markers');
  if(!blockTiles && status.markers) {
   const aboveDither=await page.evaluate(()=>[...document.querySelectorAll('.poc__ship')].every(m=>Number(getComputedStyle(m).zIndex)>0));
   if(!aboveDither)throw new Error(name+': glyphs may be covered by native dither canvas');
  }
  await page.locator('.screen').screenshot({path:`docs/screenshots/${name}.png`});
  results.push({name,...status,errors});console.log(name,status.markers,'markers');await page.close();
 }
 await writeFile(process.env.CASE_PREFIX?'docs/screenshots/results-additional.json':'docs/screenshots/results.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}
